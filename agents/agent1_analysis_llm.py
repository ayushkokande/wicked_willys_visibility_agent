"""Agent 1 with real LLM integration for ranking-only output.

Drop-in replacement for your existing `agent_analysis_llm.py` while preserving the
overall framework and public interface your code depends on:

- Same class name: Agent1AnalysisLLM
- Same constructor signature
- Same `analyze(query, business_profile) -> Dict[str, Any]`
- Same `_parse_json_response` helper (kept, slightly hardened)
- Same `_generate_summary` method (kept signature)

Behavior:
- Agent 1 now ONLY produces a ranked list of likely local search results.
- Legacy keys (competitors/issues/opportunities/etc.) are preserved but empty
  so downstream code does not break.

Fix included:
- If no candidates are provided (your current flow), the LLM MUST STILL generate
  a ranked list (it will not refuse).
- Adds a single retry if the model returns an empty ranked_results list.

Output:
- Primary: `ranked_results`
- Also mirrored into `results` for compatibility with generic pipelines
- Includes `inferred_location` (coarse; not a street address unless provided)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from core.business_profile import BusinessProfile
from utils.llm_client import LLMClient
import uuid
import json


RANKING_SYSTEM_PROMPT = """You are Agent 1: Local Search Results Ranker (SERP Generator).

Task:
Given a user query (e.g., “good coffee shops near the university”), return a ranked list of the TOP local search results a user would expect.

Critical rules:
- You MUST return 5–10 ranked results unless the query is impossible or location is undefined.
- Do NOT anchor on the target business. The target business is context only and must NOT be forced into rank #1.
- If you include the target business, include it only if it genuinely fits the query and location. Rank it wherever it naturally belongs.
- Output MUST be valid JSON only (no markdown, no prose).
- Do NOT include numeric claims (ratings, review counts, “#1 in NYC”, etc.).
- inferred_location must be coarse (e.g., a neighborhood, landmark, or city district) unless the user explicitly gave an address.

"""


class Agent1AnalysisLLM:
    """
    Agent 1: Discovery & Analysis Agent (refactored to Ranking-Only) with LLM integration.

    Uses LLM to return a ranked list of likely search results for a local query.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize Agent 1 with LLM.

        Args:
            llm_client: LLM client for ranking output
        """
        self.llm_client = llm_client

    def analyze(self, query: str, business_profile: BusinessProfile) -> Dict[str, Any]:
        """
        Produce a ranked list using LLM (ranking-only).

        Args:
            query: User search query
            business_profile: The business being optimized (kept for context + downstream compatibility)

        Returns:
            Analysis dictionary (framework-compatible) containing ranked results.
        """
        analysis_id = str(uuid.uuid4())
        clean_query = (query or "").strip()

        print(f"  🤖 Ranking with LLM: '{clean_query}'")
        print(f"  Target business: {business_profile.name}")

        # Business context retained for compatibility, but explicitly "context only".
        business_context = f"""
Business Profile (context only; do not fabricate claims):
- Target Name: {business_profile.name}
- Address: {business_profile.address}
- Primary Category: {business_profile.primary_category}
- Secondary Categories: {', '.join(business_profile.secondary_categories)}
- Target Keywords: {', '.join(business_profile.target_keywords)}
- Current Review Count: {business_profile.review_count}
- Average Rating: {business_profile.average_rating}
- Website: {business_profile.website or 'Not provided'}
- Google My Business: {'Set up' if business_profile.google_my_business_id else 'Not set up'}
- Citation Count: {business_profile.citation_count or 'Unknown'}
""".strip()

        # Ranking-only prompt (single call; generate if no candidates are provided).
        ranking_prompt = f""""
{business_context}

User Query: "{clean_query}"

You MUST return a ranked list of businesses for this query.
- If candidate businesses are provided: rank ONLY those candidates.
- If no candidates are provided: generate up to 10 plausible real businesses that fit the query and implied location.

Return valid JSON only in this exact schema:
{{
  "query": "{clean_query}",
  "inferred_location": string,
  "ranked_results": [
    {{
      "rank": integer,
      "name": string,
      "address": string|null,
      "website": string|null,
      "reason_tokens": [string]
    }}
  ],
  "notes": string
}}

Constraints:
- Up to 10 results max.
- rank must start at 1 and be consecutive.
- reason_tokens must be <= 3 short phrases derived from the query text only (e.g., ["near downtown", "bar"]).
- Do NOT include ratings/review counts or other numeric claims.
- inferred_location must be coarse (e.g., a neighborhood, landmark, or city district), not a street address unless the user provided one.
""".strip()

        # Default / fallback outputs
        ranking_data: Dict[str, Any] = {
            "query": clean_query,
            "inferred_location": "",
            "ranked_results": [],
            "notes": "llm_not_called",
        }

        try:
            if not self.llm_client:
                raise RuntimeError("LLM client not provided")

            print("  → Producing ranked results...")
            ranking_response = self.llm_client.generate(
                ranking_prompt,
                system_prompt=RANKING_SYSTEM_PROMPT,
                temperature=0.2,
            )
            parsed = self._parse_json_response(ranking_response)

            ranked_results = parsed.get("ranked_results", [])
            if not isinstance(ranked_results, list):
                ranked_results = []

            # Retry once if empty (common model failure mode)
            if len(ranked_results) == 0:
                retry_prompt = (
                    ranking_prompt
                    + "\n\nIMPORTANT: Do not refuse due to missing candidates. "
                      "Produce 5-10 business names localized to the implied area. "
                      "Return JSON only."
                )
                ranking_response_retry = self.llm_client.generate(
                    retry_prompt,
                    system_prompt=RANKING_SYSTEM_PROMPT,
                    temperature=0.3,
                )
                parsed_retry = self._parse_json_response(ranking_response_retry)

                rr_retry = parsed_retry.get("ranked_results", [])
                if isinstance(rr_retry, list) and len(rr_retry) > 0:
                    parsed = parsed_retry
                    ranked_results = rr_retry

            # Normalize results: enforce 1..N ranks, max 10, safe types
            normalized_results: List[Dict[str, Any]] = []
            for idx, item in enumerate(ranked_results[:10], start=1):
                if not isinstance(item, dict):
                    continue

                name = item.get("name", "")
                address = item.get("address", None)
                website = item.get("website", None)
                reason_tokens = item.get("reason_tokens", [])

                if not isinstance(name, str):
                    name = ""
                if address is not None and not isinstance(address, str):
                    address = None
                if website is not None and not isinstance(website, str):
                    website = None
                if not isinstance(reason_tokens, list):
                    reason_tokens = []

                # Trim reason_tokens to <= 3, stringify elements
                rt_clean: List[str] = []
                for t in reason_tokens:
                    if isinstance(t, str) and t.strip():
                        rt_clean.append(t.strip())
                    if len(rt_clean) >= 3:
                        break

                normalized_results.append(
                    {
                        "rank": idx,
                        "name": name.strip(),
                        "address": address.strip() if isinstance(address, str) else None,
                        "website": website.strip() if isinstance(website, str) else None,
                        "reason_tokens": rt_clean,
                    }
                )

            inferred_location = parsed.get("inferred_location", "")
            if not isinstance(inferred_location, str):
                inferred_location = ""

            notes = parsed.get("notes", "")
            if not isinstance(notes, str):
                notes = ""

            ranking_data = {
                "query": parsed.get("query", clean_query) if isinstance(parsed.get("query", clean_query), str) else clean_query,
                "inferred_location": inferred_location.strip(),
                "ranked_results": normalized_results,
                "notes": notes.strip(),
            }

            # If still empty after retry, give a stronger note for debugging
            if len(ranking_data["ranked_results"]) == 0 and not ranking_data["notes"]:
                ranking_data["notes"] = "empty_ranked_results_after_retry"

        except Exception as e:
            print(f"  ⚠️  LLM error: {e}")
            ranking_data = {
                "query": clean_query,
                "inferred_location": "",
                "ranked_results": [],
                "notes": f"llm_error: {str(e)}",
            }

        ranked_results_out = ranking_data.get("ranked_results", [])

        # Framework-compatible result object:
        # Preserve legacy keys your other code may expect (empty by design here).
        analysis_result: Dict[str, Any] = {
            "analysis_id": analysis_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,  # preserve original query string (including newline if upstream passed it)
            "target_business": business_profile.name,
            "llm_powered": True,

            # Primary output for Agent 1 (ranking-only)
            "inferred_location": ranking_data.get("inferred_location", ""),
            "ranked_results": ranked_results_out,

            # Optional mirror for compatibility if some code expects generic "results"
            "results": ranked_results_out,

            # Legacy keys preserved (empty by design for Agent 1 after refactor)
            "competitors": [],
            "ranking_factors": [],
            "gaps": [],
            "issues": [],
            "critical_issues": [],
            "high_priority_issues": [],
            "opportunities": [],

            # Summary (kept for compatibility)
            "summary": self._generate_summary(query, business_profile, issues=[], opportunities=[]),

            # Notes for debugging/traceability
            "notes": ranking_data.get("notes", ""),
        }

        return analysis_result

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks and stray text."""
        if not isinstance(response, str):
            return {}

        text = response.strip()

        # Remove markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        # Attempt direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Attempt to extract first JSON object from mixed text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            candidate = text[start:end].strip()
            try:
                return json.loads(candidate)
            except Exception:
                return {}

        return {}

    def _generate_summary(
        self,
        query: str,
        business_profile: BusinessProfile,
        issues: List[Dict],
        opportunities: List[Dict],
    ) -> str:
        """Generate a short summary (kept for framework compatibility)."""
        clean_query = (query or "").strip()
        summary = f"""
LLM Ranking Output for {business_profile.name}:
- Query: "{clean_query}"
- Mode: ranked_results_only
- Issues analyzed: 0 (handled by Agent 2/3)
- Opportunities analyzed: 0 (handled by Agent 2/3)
""".strip()
        return summary
