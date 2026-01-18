"""Agent 1 with real LLM integration for analysis."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from core.business_profile import BusinessProfile
from utils.llm_client import LLMClient
import uuid
import json


ANALYSIS_SYSTEM_PROMPT = """You are an . Your role is to:

1. Analyze why a business might not be appearing in local search results
2. Identify competitor advantages
3. Diagnose SEO and visibility issues
4. Provide actionable insights

When analyzing, consider:
- Google My Business optimization
- Review count and quality
- Local citations and directory listings
- On-page SEO factors
- Content quality and relevance
- Social signals
- Technical SEO factors

Always provide specific, actionable insights based on the business profile and query."""


class Agent1AnalysisLLM:
    """
    Agent 1: Discovery & Analysis Agent with LLM integration
    
    Uses LLM to provide intelligent analysis of visibility issues.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize Agent 1 with LLM.
        
        Args:
            llm_client: LLM client for analysis
        """
        self.llm_client = llm_client
        
    def analyze(self, query: str, business_profile: BusinessProfile) -> Dict[str, Any]:
        """
        Perform comprehensive analysis using LLM.
        
        Args:
            query: Business query
            business_profile: The business being optimized
            
        Returns:
            Detailed analysis dictionary
        """
        analysis_id = str(uuid.uuid4())
        
        print(f"  🤖 Analyzing with LLM: '{query}'")
        print(f"  Target business: {business_profile.name}")
        
        # Build context for LLM
        business_context = f"""
Business Profile:
- Name: {business_profile.name}
- Address: {business_profile.address}
- Primary Category: {business_profile.primary_category}
- Secondary Categories: {', '.join(business_profile.secondary_categories)}
- Target Keywords: {', '.join(business_profile.target_keywords)}
- Current Review Count: {business_profile.review_count}
- Average Rating: {business_profile.average_rating}
- Website: {business_profile.website or 'Not provided'}
- Google My Business: {'Set up' if business_profile.google_my_business_id else 'Not set up'}
- Citation Count: {business_profile.citation_count or 'Unknown'}
"""
        
        # Competitor discovery prompt
        competitor_prompt = f"""
{business_context}

User Query: "{query}"

Based on this query and business profile, analyze the competitive landscape.

Provide a JSON response with:
1. "estimated_competitors": List of 3-5 likely competitor types in the area with estimated metrics
2. "why_competitors_rank": Key reasons competitors might rank higher
3. "target_business_gaps": Specific gaps for {business_profile.name}

Format as valid JSON only, no markdown."""

        # Issue diagnosis prompt
        issues_prompt = f"""
{business_context}

User Query: "{query}"

Diagnose specific visibility issues for {business_profile.name}.

Provide a JSON response with an "issues" array, each issue having:
- "issue_id": unique identifier
- "title": brief title
- "description": detailed description
- "severity": "critical", "high", or "medium"
- "impact": business impact description
- "evidence": supporting evidence

Focus on actionable issues. Format as valid JSON only."""

        # Opportunities prompt
        opportunities_prompt = f"""
{business_context}

User Query: "{query}"

Identify opportunities for {business_profile.name} to improve visibility.

Provide a JSON response with an "opportunities" array, each opportunity having:
- "opportunity_id": unique identifier
- "title": brief title
- "description": detailed description
- "potential_impact": "high", "medium", or "low"
- "effort": "easy", "medium", or "hard"
- "reason": why this would help

Format as valid JSON only."""

        # Make LLM calls
        try:
            print("  → Analyzing competitive landscape...")
            competitor_response = self.llm_client.generate(
                competitor_prompt, 
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
                temperature=0.3
            )
            competitor_data = self._parse_json_response(competitor_response)
            
            print("  → Diagnosing visibility issues...")
            issues_response = self.llm_client.generate(
                issues_prompt,
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
                temperature=0.3
            )
            issues_data = self._parse_json_response(issues_response)
            
            print("  → Identifying opportunities...")
            opportunities_response = self.llm_client.generate(
                opportunities_prompt,
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
                temperature=0.3
            )
            opportunities_data = self._parse_json_response(opportunities_response)
            
        except Exception as e:
            print(f"  ⚠️  LLM error: {e}")
            # Fallback to basic analysis
            competitor_data = {"estimated_competitors": [], "why_competitors_rank": [], "target_business_gaps": []}
            issues_data = {"issues": []}
            opportunities_data = {"opportunities": []}
        
        # Compile results
        issues = issues_data.get("issues", [])
        opportunities = opportunities_data.get("opportunities", [])
        
        analysis_result = {
            "analysis_id": analysis_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "target_business": business_profile.name,
            "llm_powered": True,
            
            # Competitor Analysis
            "competitors": competitor_data.get("estimated_competitors", []),
            "ranking_factors": competitor_data.get("why_competitors_rank", []),
            "gaps": competitor_data.get("target_business_gaps", []),
            
            # Issues
            "issues": issues,
            "critical_issues": [i for i in issues if i.get("severity") == "critical"],
            "high_priority_issues": [i for i in issues if i.get("severity") == "high"],
            
            # Opportunities
            "opportunities": opportunities,
            
            # Summary
            "summary": self._generate_summary(query, business_profile, issues, opportunities)
        }
        
        return analysis_result
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Remove markdown code blocks if present
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (```json and ```)
            lines = [l for l in lines if not l.startswith("```")]
            text = "\n".join(lines)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except:
                    pass
            return {}
    
    def _generate_summary(self, query: str, business_profile: BusinessProfile,
                         issues: List[Dict], opportunities: List[Dict]) -> str:
        """Generate analysis summary."""
        critical_count = len([i for i in issues if i.get("severity") == "critical"])
        high_count = len([i for i in issues if i.get("severity") == "high"])
        
        summary = f"""
LLM-Powered Analysis for {business_profile.name}:
- Query: "{query}"
- Critical issues found: {critical_count}
- High-priority issues: {high_count}
- Opportunities identified: {len(opportunities)}
"""
        if issues:
            summary += f"\nTop Issue: {issues[0].get('title', 'N/A')}"
        if opportunities:
            summary += f"\nTop Opportunity: {opportunities[0].get('title', 'N/A')}"
            
        return summary.strip()
