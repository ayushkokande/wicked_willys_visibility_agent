"""
Agent 2: Action Planning Agent - Determines allowed actions based on analysis.

Enhancement:
- Accepts Agent 1 ranked list (analysis_result["ranked"] / ["ranking"])
- Uses LLM (if available) to explain WHY results are ranked the way they are
- Produces an "agent2_report" (evidence plan + factor deltas) and optionally
  converts those deltas into issues so your existing action mapping can fire.

Design goals:
- Brand-aware context (Brand/Social/Earned buckets)
- No-synthetic-data behavior: if evidence is missing, request evidence via queries
- Structured JSON output for deterministic downstream usage
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from core.business_profile import BusinessProfile
from core.allowed_actions import (
    ActionPlan, AllowedAction, ActionType, ActionPriority,
    AutomationLevel, ACTION_REGISTRY
)
import uuid
import json
import re


# ----------------------------
# LLM prompts (Agent 2 context)
# ----------------------------

AGENT2_RANKING_AUDIT_SYSTEM_PROMPT = """
You are Agent 2: Business Visibility Explainer & Evidence Planner.

Mission:
- Explain why the target business (see brand_context) is ranked low or missing for a local discovery query.
- Validate the ranked list using ONLY verifiable evidence.
- Produce an evidence-backed diagnosis and a plan to collect missing evidence.

Evidence buckets (must be used explicitly):
1) Brand: the target business's official site and owned properties.
2) Social: social/UGC platforms (e.g., Instagram, Reddit, YouTube).
3) Earned: independent media/review/comparison/editorial sources.

Hard rules:
- NO synthetic facts. If you do not have evidence, do NOT invent.
- Every claim should be paired with "evidence_needed": bucket + queries + what_to_extract.
- Output MUST be strict JSON matching the provided schema. No markdown, no extra keys.
- Use ranking factors relevant to local discovery:
  Relevance, Proximity, Prominence, Trust, Freshness.

What you will receive:
- query
- ranked results from Agent 1 (names + optional metadata)
- brand context for the target business

What you must output:
- ranking_explanation (global + pairwise for top results)
- deltas_vs_top (target business vs top competitor) with evidence needs
- evidence_plan (queries grouped by bucket)
- action_hypotheses (what likely helps the target business improve)
- confidence (1-5)
""".strip()


# A deliberately small schema so you can implement quickly without extra files.
# (If you prefer, move this schema to core/types.py and validate with Pydantic.)
AGENT2_RANKING_AUDIT_SCHEMA = {
    "type": "object",
    "required": ["query", "business_present", "business_rank", "ranking_explanation",
                 "deltas_vs_top", "evidence_plan", "action_hypotheses", "confidence"],
    "properties": {
        "query": {"type": "string"},
        "business_present": {"type": "boolean"},
        "business_rank": {"type": ["integer", "null"]},
        "ranking_explanation": {
            "type": "object",
            "required": ["global_reasons", "pairwise"],
            "properties": {
                "global_reasons": {"type": "array", "items": {"type": "string"}},
                "pairwise": {"type": "array", "items": {"type": "object"}},
            }
        },
        "deltas_vs_top": {"type": "array", "items": {"type": "object"}},
        "evidence_plan": {"type": "array", "items": {"type": "object"}},
        "action_hypotheses": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "integer", "minimum": 1, "maximum": 5},
    }
}


class Agent2ActionPlanning:
    """
    Agent 2: Action Planning Agent

    Responsibilities:
    - Review Agent 1's analysis
    - Explain ranked list (why ordered that way) using LLM (optional)
    - Identify actionable items
    - Determine allowed actions
    - Prioritize and categorize actions
    """

    def __init__(self, llm_client=None):
        """
        Initialize Agent 2.

        Args:
            llm_client: LLM client for action planning and ranking explanation (optional)

        Expected llm_client interface:
            llm_client.complete(system: str, user: str, temperature: float=0.2) -> str

        If your client differs (e.g., call(messages=[...]) or chat.completions),
        adapt _call_llm().
        """
        self.llm_client = llm_client

    # ----------------------------
    # Public API
    # ----------------------------

    def plan_actions(self, analysis_result: Dict[str, Any],
                     business_profile: BusinessProfile) -> ActionPlan:
        """
        Create an action plan based on Agent 1's analysis (+ optional ranking explanation).

        Args:
            analysis_result: Results from Agent 1
            business_profile: Business being optimized

        Returns:
            ActionPlan with prioritized allowed actions
        """
        plan_id = str(uuid.uuid4())
        query = analysis_result.get("query", "Unknown query")

        print(f"  Creating action plan for query: '{query}'")
        print(f"  Analyzing {len(analysis_result.get('issues', []))} issues...")

        # Extract issues and opportunities
        issues = analysis_result.get("issues", [])
        opportunities = analysis_result.get("opportunities", [])
        seo_analysis = analysis_result.get("seo_analysis", {})

        # Get ranked results from Agent 1
        ranked_results = analysis_result.get("ranked_results", [])
        
        # 1) Try LLM-based ranking explanation if we have an LLM client
        agent2_report = None
        if self.llm_client and ranked_results:
            print("  → Analyzing ranking with LLM...")
            agent2_report = self.explain_ranked_list(analysis_result, business_profile)
            if agent2_report:
                analysis_result["agent2_report"] = agent2_report
                issues_from_ranking = self._ranking_report_to_issues(agent2_report, business_profile)
                if issues_from_ranking:
                    issues.extend(issues_from_ranking)
                    print(f"  → LLM analysis created {len(issues_from_ranking)} issues")
        
        # 2) FALLBACK: If no issues from LLM, create issues directly from ranking
        if not issues and ranked_results:
            print("  → Creating issues from ranking (fallback mode)...")
            issues = self._create_issues_from_ranking(ranked_results, business_profile)
            print(f"  → Fallback created {len(issues)} issues")

        # 3) Generate allowed actions from issues/opportunities
        actions: List[AllowedAction] = []

        for issue in issues:
            issue_actions = self._map_issue_to_actions(issue, seo_analysis, business_profile)
            actions.extend(issue_actions)

        for opportunity in opportunities:
            opp_actions = self._map_opportunity_to_actions(opportunity, business_profile)
            actions.extend(opp_actions)

        # Remove duplicates and prioritize
        actions = self._deduplicate_actions(actions)
        actions = self._prioritize_actions(actions, issues)

        # Count action types
        automated_count = len([a for a in actions if a.automation_level == AutomationLevel.FULLY_AUTOMATED])
        manual_count = len([a for a in actions if a.automation_level == AutomationLevel.MANUAL])

        action_plan = ActionPlan(
            plan_id=plan_id,
            query=query,
            actions=actions,
            total_actions=len(actions),
            automated_count=automated_count,
            manual_count=manual_count
        )

        print(f"  → Generated {len(actions)} actions ({automated_count} automated, {manual_count} manual)")
        return action_plan

    # ----------------------------
    # NEW: Ranking explanation
    # ----------------------------

    def explain_ranked_list(self, analysis_result: Dict[str, Any],
                            business_profile: BusinessProfile) -> Optional[Dict[str, Any]]:
        """
        Use LLM to explain WHY the ranked list is ordered and what evidence is missing.

        Returns:
            agent2_report dict matching AGENT2_RANKING_AUDIT_SCHEMA, or None.
        """
        if not self.llm_client:
            return None

        query = analysis_result.get("query", "Unknown query")
        ranked = (
            analysis_result.get("ranked")
            or analysis_result.get("ranking")
            or analysis_result.get("ranked_results")
            or []
        )
        if not ranked:
            return None

        # Build brand context pack (brand-first)
        brand_name = getattr(business_profile, "name", "the business")
        brand_site = getattr(business_profile, "website", None) or getattr(business_profile, "site", None)
        social_profiles = getattr(business_profile, "social_profiles", {}) or {}
        target_keywords = getattr(business_profile, "target_keywords", []) or []
        landmarks = getattr(business_profile, "landmarks", []) or []

        # Normalize ranked list so the LLM has consistent fields
        ranked_compact = self._normalize_ranked_list(ranked)

        # Identify target business presence quickly (name match heuristic)
        business_present, business_rank = self._find_business_in_ranked(ranked_compact, brand_name)

        payload = {
            "query": query,
            "ranked_results": ranked_compact,
            "brand_context": {
                "brand_name": brand_name,
                "brand_site": brand_site,
                "social_profiles": social_profiles,
                "target_keywords": target_keywords[:10],
                "landmarks": landmarks[:10],
                # This forces the bucket framing you described:
                "evidence_buckets": {
                    "brand": "official brand/owned properties",
                    "social": "UGC/community/social platforms",
                    "earned": "independent media/review/comparison sites"
                },
                "constraints": {
                    "no_synthetic_data": True,
                    "must_propose_queries_for_missing_evidence": True
                }
            },
            "known": {
                "business_present": business_present,
                "business_rank": business_rank
            },
            "schema": AGENT2_RANKING_AUDIT_SCHEMA
        }

        raw = self._call_llm(
            system=AGENT2_RANKING_AUDIT_SYSTEM_PROMPT,
            user=json.dumps(payload, ensure_ascii=True),
            temperature=0.2
        )

        report = self._safe_json_parse(raw)
        if not report:
            return None

        # Ensure the minimal keys exist; fill a couple of safe defaults if needed
        report.setdefault("query", query)
        report.setdefault("business_present", business_present)
        report.setdefault("business_rank", business_rank)
        report.setdefault("confidence", 3)
        return report

    # ----------------------------
    # Existing mapping: issues -> actions
    # ----------------------------

    def _classify_issue_by_keywords(self, issue: Dict[str, Any]) -> str:
        """Classify an issue based on keywords in title/description."""
        issue_id = str(issue.get("issue_id", "")).lower()
        title = str(issue.get("title", "")).lower()
        description = str(issue.get("description", "")).lower()
        text = f"{issue_id} {title} {description}"
        
        # GMB related
        if any(kw in text for kw in ["google my business", "gmb", "google business", "google profile", "business profile"]):
            return "missing_gmb"
        # Review related
        if any(kw in text for kw in ["review", "rating", "star", "feedback", "testimonial"]):
            return "low_review_count"
        # Citation related
        if any(kw in text for kw in ["citation", "directory", "listing", "nap", "yelp", "tripadvisor"]):
            return "low_citations"
        # Keyword/SEO related
        if any(kw in text for kw in ["keyword", "seo", "content", "optimization", "meta", "search term"]):
            return "keyword_optimization"
        # Website related
        if any(kw in text for kw in ["website", "site", "page", "technical", "schema"]):
            return "website"
        # Missing from ranking
        if any(kw in text for kw in ["missing", "not appearing", "not showing", "invisible", "not found"]):
            return "missing_from_ranked"
        return "general"

    def _map_issue_to_actions(self, issue: Dict[str, Any],
                             seo_analysis: Dict[str, Any],
                             business_profile: BusinessProfile) -> List[AllowedAction]:
        """Map a specific issue to actionable items."""
        actions: List[AllowedAction] = []
        issue_id = issue.get("issue_id")
        severity = issue.get("severity", "medium")
        
        # If issue_id doesn't match known values, classify by keywords
        classified_id = self._classify_issue_by_keywords(issue)
        if issue_id not in ["missing_gmb", "low_review_count", "keyword_optimization", "low_citations", "missing_from_ranked"]:
            issue_id = classified_id
            print(f"    Classified issue '{issue.get('title', 'unknown')[:30]}' as: {issue_id}")

        # Determine priority based on severity
        if severity in ("critical", "high"):
            priority = ActionPriority.HIGH
        else:
            priority = ActionPriority.MEDIUM

        # Missing GMB profile
        if issue_id == "missing_gmb":
            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.UPDATE_GMB_PROFILE,
                title="Set Up Google My Business Profile",
                description="Create and optimize a Google My Business profile with complete business information, categories, and photos",
                priority=priority,
                automation_level=AutomationLevel.MANUAL,
                estimated_impact="Critical - Required for local pack visibility",
                difficulty="medium",
                time_required="1-2 hours",
                reason=issue.get("description"),
                related_issue=issue.get("issue_id"),
                required_resources=["GMB account access", "Business verification documents"]
            ))

            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.GENERATE_CONTENT,
                title="Generate Optimized GMB Description",
                description="Create SEO-optimized business description with target keywords for GMB profile",
                priority=priority,
                automation_level=AutomationLevel.FULLY_AUTOMATED,
                estimated_impact="High - Improves keyword relevance in local search",
                difficulty="easy",
                time_required="5 minutes",
                reason="GMB description needs keyword optimization",
                related_issue=issue.get("issue_id")
            ))

        # Low review count
        elif issue_id == "low_review_count":
            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.MANAGE_REVIEWS,
                title="Review Generation Strategy",
                description="Create templates and process for generating customer reviews",
                priority=ActionPriority.HIGH,
                automation_level=AutomationLevel.PARTIALLY_AUTOMATED,
                estimated_impact="High - Reviews significantly impact local rankings",
                difficulty="medium",
                time_required="Ongoing",
                reason=issue.get("description"),
                related_issue=issue.get("issue_id"),
                required_resources=["Review request templates", "Customer communication plan"]
            ))

        # Keyword optimization
        elif issue_id == "keyword_optimization":
            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.GENERATE_CONTENT,
                title="Keyword-Optimized Business Descriptions",
                description="Generate multiple versions of business descriptions optimized for target keywords",
                priority=priority,
                automation_level=AutomationLevel.FULLY_AUTOMATED,
                estimated_impact="Medium-High - Improves search relevance",
                difficulty="easy",
                time_required="10 minutes",
                reason=issue.get("description"),
                related_issue=issue.get("issue_id")
            ))

        # Low citations
        elif issue_id == "low_citations":
            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.CREATE_CITATION_LIST,
                title="Generate Local Citation List",
                description="Create comprehensive list of local directories and citation sites for business submission",
                priority=priority,
                automation_level=AutomationLevel.FULLY_AUTOMATED,
                estimated_impact="High - Citations boost local SEO authority",
                difficulty="easy",
                time_required="5 minutes",
                reason=issue.get("description"),
                related_issue=issue.get("issue_id")
            ))

            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.SUBMIT_TO_DIRECTORIES,
                title="Submit to Local Directories",
                description="Submit business information to local citation directories",
                priority=priority,
                automation_level=AutomationLevel.MANUAL,
                estimated_impact="High - Builds local SEO foundation",
                difficulty="medium",
                time_required="2-4 hours",
                reason="Need to create accounts and submit to citation sites",
                related_issue=issue.get("issue_id"),
                prerequisites=[actions[-1].action_id if actions else None]
            ))

        # NEW: If the business is missing from the ranked list, force foundational visibility work
        elif issue_id == "missing_from_ranked":
            # This issue is produced by _ranking_report_to_issues().
            # We map it to a mix of trust/prominence/relevance actions.
            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.GENERATE_CONTENT,
                title="Generate Query-Aligned Brand Copy",
                description=f"Generate website/GMB copy that explicitly aligns {business_profile.name} with the query intent (e.g., matching target keywords like nearby landmarks or neighborhoods)",
                priority=ActionPriority.HIGH,
                automation_level=AutomationLevel.FULLY_AUTOMATED,
                estimated_impact="High - Improves relevance signals for LLM + local search",
                difficulty="easy",
                time_required="10 minutes",
                reason=issue.get("description"),
                related_issue=issue.get("issue_id"),
            ))

            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.CREATE_CITATION_LIST,
                title="Build Earned/Directory Presence Plan",
                description="Generate a prioritized citation + earned media outreach target list to improve prominence/trust signals",
                priority=ActionPriority.HIGH,
                automation_level=AutomationLevel.FULLY_AUTOMATED,
                estimated_impact="High - Increases discoverability across Earned sources",
                difficulty="easy",
                time_required="10 minutes",
                reason="Missing from ranking often indicates weak prominence/trust signals across Earned sources.",
                related_issue=issue.get("issue_id"),
            ))

        # Website/Technical SEO issues
        elif issue_id == "website":
            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.CREATE_SCHEMA_MARKUP,
                title="Generate Schema Markup",
                description="Create LocalBusiness JSON-LD schema markup for better search visibility",
                priority=priority,
                automation_level=AutomationLevel.FULLY_AUTOMATED,
                estimated_impact="Medium-High - Enables rich snippets in search results",
                difficulty="easy",
                time_required="10 minutes",
                reason=issue.get("description"),
                related_issue=issue.get("issue_id")
            ))

        # Low ranking (not in top 3)
        elif issue_id == "low_ranking":
            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.GENERATE_CONTENT,
                title="Optimize Content for Query Relevance",
                description="Generate keyword-optimized content to improve ranking position",
                priority=ActionPriority.HIGH,
                automation_level=AutomationLevel.FULLY_AUTOMATED,
                estimated_impact="High - Improves relevance signals",
                difficulty="easy",
                time_required="15 minutes",
                reason=issue.get("description"),
                related_issue=issue.get("issue_id")
            ))
            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.GENERATE_REVIEW_RESPONSE,
                title="Create Review Response Templates",
                description="Generate professional review response templates to improve engagement",
                priority=ActionPriority.MEDIUM,
                automation_level=AutomationLevel.FULLY_AUTOMATED,
                estimated_impact="Medium - Improves customer engagement signals",
                difficulty="easy",
                time_required="10 minutes",
                reason="Responding to reviews improves ranking signals",
                related_issue=issue.get("issue_id")
            ))

        # Maintain ranking (already in top 3)
        elif issue_id == "maintain_ranking":
            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.CREATE_BLOG_POST,
                title="Create Fresh Content",
                description="Generate fresh blog/social content to maintain ranking momentum",
                priority=ActionPriority.LOW,
                automation_level=AutomationLevel.FULLY_AUTOMATED,
                estimated_impact="Medium - Keeps content fresh",
                difficulty="easy",
                time_required="20 minutes",
                reason=issue.get("description"),
                related_issue=issue.get("issue_id")
            ))

        # General/fallback - create at least one action
        elif issue_id == "general" or not actions:
            issue_title = issue.get("title", "Visibility Issue")
            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.GENERATE_CONTENT,
                title=f"Address: {issue_title[:40]}",
                description=f"Generate optimized content to address this issue: {issue.get('description', 'visibility improvement needed')[:100]}",
                priority=priority,
                automation_level=AutomationLevel.FULLY_AUTOMATED,
                estimated_impact="Medium - Addresses identified visibility issue",
                difficulty="easy",
                time_required="15 minutes",
                reason=issue.get("description"),
                related_issue=issue.get("issue_id")
            ))

        return actions

    def _map_opportunity_to_actions(self, opportunity: Dict[str, Any],
                                   business_profile: BusinessProfile) -> List[AllowedAction]:
        """Map opportunities to actionable items."""
        actions: List[AllowedAction] = []
        opp_id = opportunity.get("opportunity_id")

        if opp_id == "content_marketing":
            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.CREATE_BLOG_POST,
                title="Create Local Content Blog Post",
                description=f"Generate blog post about '{business_profile.target_keywords[0] if getattr(business_profile, 'target_keywords', []) else 'local area'}' to improve SEO",
                priority=ActionPriority.MEDIUM,
                automation_level=AutomationLevel.FULLY_AUTOMATED,
                estimated_impact="Medium - Helps with keyword targeting",
                difficulty="easy",
                time_required="15 minutes",
                reason=opportunity.get("description"),
                related_issue=opp_id
            ))

        elif opp_id == "citation_building":
            pass

        return actions

    def _deduplicate_actions(self, actions: List[AllowedAction]) -> List[AllowedAction]:
        """Remove duplicate actions based on action_type."""
        seen_types = set()
        unique_actions: List[AllowedAction] = []

        for action in actions:
            if action.action_type not in seen_types:
                seen_types.add(action.action_type)
                unique_actions.append(action)
            else:
                existing = next(a for a in unique_actions if a.action_type == action.action_type)
                if action.priority == ActionPriority.HIGH and existing.priority != ActionPriority.HIGH:
                    unique_actions.remove(existing)
                    unique_actions.append(action)

        return unique_actions

    def _prioritize_actions(self, actions: List[AllowedAction],
                            issues: List[Dict[str, Any]]) -> List[AllowedAction]:
        """Prioritize actions based on impact and urgency."""
        priority_order = {ActionPriority.HIGH: 0, ActionPriority.MEDIUM: 1, ActionPriority.LOW: 2}

        actions.sort(key=lambda a: (
            priority_order.get(a.priority, 99),
            a.estimated_impact.lower().startswith("high") if a.estimated_impact else False,
            a.action_id
        ))
        return actions

    # ----------------------------
    # Helpers: convert ranking report -> issues
    # ----------------------------

    def _ranking_report_to_issues(self, report: Dict[str, Any],
                                 business_profile: BusinessProfile) -> List[Dict[str, Any]]:
        """
        Translate Agent 2 ranking report into issue objects that your existing
        _map_issue_to_actions can consume.
        """
        issues: List[Dict[str, Any]] = []
        business_present = bool(report.get("business_present", False))

        if not business_present:
            business_name = getattr(business_profile, 'name', "The business")
            issues.append({
                "issue_id": "missing_from_ranked",
                "severity": "high",
                "description": (
                    f"{business_name} is missing from the ranked results. "
                    f"Likely gaps in relevance/prominence/trust vs competitors. "
                    f"See agent2_report.evidence_plan for validation queries."
                )
            })

        # If deltas suggest low prominence/trust, map to existing ids when possible
        for delta in report.get("deltas_vs_top", []) or []:
            factor = (delta.get("factor") or "").lower()
            why = delta.get("why_delta") or "Gap detected vs top competitor."
            business_score = delta.get("business_score_estimate")
            top_score = delta.get("top_competitor_score_estimate")

            # Only create issues when the gap is material
            if isinstance(business_score, int) and isinstance(top_score, int) and (top_score - business_score) >= 2:
                if factor in ("trust", "prominence"):
                    issues.append({"issue_id": "low_citations", "severity": "high", "description": why})
                elif factor == "relevance":
                    issues.append({"issue_id": "keyword_optimization", "severity": "high", "description": why})

        return self._dedupe_issue_dicts(issues)

    def _dedupe_issue_dicts(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        out = []
        for i in issues:
            key = (i.get("issue_id"), i.get("description"))
            if key not in seen:
                seen.add(key)
                out.append(i)
        return out

    def _create_issues_from_ranking(self, ranked_results: List[Dict[str, Any]], 
                                     business_profile: BusinessProfile) -> List[Dict[str, Any]]:
        """
        Create issues directly from ranking results (fallback when LLM analysis fails).
        
        Analyzes whether the target business appears in the ranking and creates
        appropriate issues based on its position or absence.
        """
        issues: List[Dict[str, Any]] = []
        business_name = getattr(business_profile, 'name', "The business")
        business_name_lower = business_name.lower()

        # Check if business is in ranked results
        business_rank = None
        for result in ranked_results:
            name = result.get("name", "").lower()
            if business_name_lower in name:
                business_rank = result.get("rank")
                break

        if business_rank is None:
            # Business is NOT in the ranked results - this is a critical issue
            issues.append({
                "issue_id": "missing_from_ranked",
                "title": f"{business_name} Missing from Search Results",
                "severity": "critical",
                "description": (
                    f"{business_name} does not appear in the top search results for this query. "
                    f"This indicates significant gaps in visibility, relevance, or prominence. "
                    f"Actions needed: optimize GMB, build citations, improve keyword targeting."
                )
            })
            
            # Add specific issues for common visibility problems
            issues.append({
                "issue_id": "low_citations",
                "title": "Insufficient Local Citations",
                "severity": "high",
                "description": (
                    "Business may be missing from key local directories and citation sources. "
                    "Need to build presence on Yelp, TripAdvisor, Foursquare, and local directories."
                )
            })
            
            issues.append({
                "issue_id": "keyword_optimization",
                "title": "Keyword Relevance Gap",
                "severity": "high",
                "description": (
                    "Website and GMB profile may not be optimized for the searched keywords. "
                    "Need to align content with user search intent and local queries."
                )
            })
            
        elif business_rank > 3:
            # Business is ranked but not in top 3
            issues.append({
                "issue_id": "low_ranking",
                "title": f"{business_name} Ranked #{business_rank} - Room for Improvement",
                "severity": "high",
                "description": (
                    f"{business_name} appears at position #{business_rank}. "
                    f"To move into top 3, need to improve reviews, citations, and content relevance."
                )
            })
            
            issues.append({
                "issue_id": "low_review_count",
                "title": "Review Strategy Needed",
                "severity": "medium",
                "description": (
                    "Higher-ranked competitors likely have more or better reviews. "
                    "Implement a review generation strategy to improve ranking."
                )
            })
            
        else:
            # Business is in top 3 - maintenance mode
            issues.append({
                "issue_id": "maintain_ranking",
                "title": f"Maintain #{business_rank} Position",
                "severity": "low",
                "description": (
                    f"{business_name} is ranked #{business_rank}. "
                    f"Focus on maintaining and defending this position through consistent optimization."
                )
            })
        
        return issues

    # ----------------------------
    # Helpers: ranked list normalization + parsing
    # ----------------------------

    def _normalize_ranked_list(self, ranked: Any) -> List[Dict[str, Any]]:
        """
        Ensure ranked list is a list of dicts with at least: rank, name, and optional metadata.
        Accepts:
          - list[str]
          - list[dict]
          - dict with 'results' or similar
        """
        # If Agent 1 returns an object, try extracting
        if isinstance(ranked, dict):
            ranked = ranked.get("results") or ranked.get("items") or ranked.get("ranked") or []

        results: List[Dict[str, Any]] = []
        if not isinstance(ranked, list):
            return results

        for idx, item in enumerate(ranked, start=1):
            if isinstance(item, dict):
                results.append({
                    "rank": item.get("rank", idx),
                    "name": item.get("name") or item.get("title") or f"result_{idx}",
                    "source": item.get("source"),
                    "address": item.get("address"),
                    "rating": item.get("rating"),
                    "reviews": item.get("user_ratings_total") or item.get("review_count"),
                    "distance_to_landmark_m": item.get("distance_to_landmark_m"),
                    "snippets": item.get("snippets") or item.get("evidence_snippets"),
                    "evidence_urls": item.get("evidence_urls") or item.get("urls"),
                })
            else:
                results.append({"rank": idx, "name": str(item)})

        return results

    def _find_business_in_ranked(self, ranked_compact: List[Dict[str, Any]], brand_name: str) -> (bool, Optional[int]):
        brand_name_l = (brand_name or "").strip().lower()
        for r in ranked_compact:
            nm = (r.get("name") or "").strip().lower()
            if brand_name_l and brand_name_l in nm:
                return True, r.get("rank")
        return False, None

    def _call_llm(self, system: str, user: str, temperature: float = 0.2) -> str:
        """
        Invoke the LLM client using the generate method.
        
        Args:
            system: System prompt
            user: User prompt/content
            temperature: Sampling temperature
            
        Returns:
            LLM response text
        """
        # Use the generate method which takes (prompt, system_prompt=...)
        return self.llm_client.generate(
            prompt=user,
            system_prompt=system,
            temperature=temperature
        )

    def _safe_json_parse(self, raw: str) -> Optional[Dict[str, Any]]:
        """
        Robustly parse JSON from an LLM response. If the model emits extra text,
        attempt to extract the first top-level JSON object.
        """
        if not raw:
            return None
        raw = raw.strip()

        # Direct parse
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            pass

        # Extract JSON object substring (best-effort)
        obj = self._extract_first_json_object(raw)
        if not obj:
            return None

        try:
            parsed = json.loads(obj)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    def _extract_first_json_object(self, text: str) -> Optional[str]:
        """
        Extract first balanced {...} JSON object from text.
        """
        start = text.find("{")
        if start == -1:
            return None

        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
        return None
