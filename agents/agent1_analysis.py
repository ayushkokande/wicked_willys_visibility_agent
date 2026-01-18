"""Agent 1: Discovery & Analysis Agent - Analyzes competitors and identifies SEO issues."""

from typing import Dict, Any, List
from datetime import datetime
from core.business_profile import BusinessProfile
import uuid


class Agent1AnalysisLLM:
    """
    Agent 1: Discovery & Analysis Agent
    
    Responsibilities:
    - Find businesses matching query requirements
    - Analyze ranking factors
    - Diagnose why target business isn't ranking well
    - Provide detailed analysis with rankings and explanations
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize Agent 1.
        
        Args:
            llm_client: LLM client for analysis (optional, can use mock for now)
        """
        self.llm_client = llm_client
        
    def analyze(self, query: str, business_profile: BusinessProfile) -> Dict[str, Any]:
        """
        Perform comprehensive analysis based on business query.
        
        Args:
            query: Business query (e.g., "bar near Bleecker Street")
            business_profile: The business being optimized
            
        Returns:
            Detailed analysis dictionary
        """
        analysis_id = str(uuid.uuid4())
        
        print(f"  Analyzing query: '{query}'")
        print(f"  Target business: {business_profile.name}")
        
        # Step 1: Discover competing businesses
        print("  → Discovering competing businesses...")
        competitors = self._discover_competitors(query, business_profile)
        
        # Step 2: Analyze rankings
        print("  → Analyzing rankings...")
        ranking_analysis = self._analyze_rankings(competitors, business_profile)
        
        # Step 3: Diagnose issues
        print("  → Diagnosing visibility issues...")
        issues = self._diagnose_issues(business_profile, competitors, query)
        
        # Step 4: SEO analysis
        print("  → Performing SEO gap analysis...")
        seo_analysis = self._analyze_seo_gaps(business_profile, competitors)
        
        # Step 5: Missing opportunities
        print("  → Identifying missed opportunities...")
        opportunities = self._identify_opportunities(business_profile, competitors)
        
        analysis_result = {
            "analysis_id": analysis_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "target_business": business_profile.name,
            
            # Competitor Analysis
            "competitors_found": len(competitors),
            "competitors": competitors,
            
            # Rankings
            "ranking_analysis": ranking_analysis,
            "target_business_estimated_rank": self._estimate_rank(business_profile, competitors),
            
            # Issues Identified
            "issues": issues,
            "critical_issues": [i for i in issues if i.get("severity") == "critical"],
            "high_priority_issues": [i for i in issues if i.get("severity") == "high"],
            
            # SEO Analysis
            "seo_analysis": seo_analysis,
            
            # Opportunities
            "opportunities": opportunities,
            
            # Summary
            "summary": self._generate_summary(query, business_profile, issues, opportunities)
        }
        
        return analysis_result
    
    def _discover_competitors(self, query: str, business_profile: BusinessProfile) -> List[Dict[str, Any]]:
        """Discover businesses that match the query."""
        # Mock competitor data - In production, this would use Google Places API, Yelp API, etc.
        competitors = [
            {
                "name": "The Corner Bar",
                "address": "145 Bleecker Street, New York, NY",
                "distance": "0.1 miles",
                "rating": 4.5,
                "review_count": 342,
                "categories": ["Bar", "American", "Nightlife"],
                "has_gmb": True,
                "has_website": True,
                "google_reviews": 340,
                "yelp_reviews": 28
            },
            {
                "name": "Bleecker Street Pub",
                "address": "160 Bleecker Street, New York, NY",
                "distance": "0.2 miles",
                "rating": 4.3,
                "review_count": 289,
                "categories": ["Bar", "Pub", "American"],
                "has_gmb": True,
                "has_website": True,
                "google_reviews": 285,
                "yelp_reviews": 42
            },
            {
                "name": "Greenwich Village Tavern",
                "address": "139 Bleecker Street, New York, NY",
                "distance": "0.1 miles",
                "rating": 4.7,
                "review_count": 456,
                "categories": ["Bar", "Restaurant", "Nightlife"],
                "has_gmb": True,
                "has_website": True,
                "google_reviews": 450,
                "yelp_reviews": 56
            }
        ]
        return competitors
    
    def _analyze_rankings(self, competitors: List[Dict], business_profile: BusinessProfile) -> Dict[str, Any]:
        """Analyze why competitors rank where they do."""
        ranking_factors = []
        
        for competitor in competitors:
            factors = {
                "business": competitor["name"],
                "ranking_factors": {
                    "review_count": {
                        "value": competitor["review_count"],
                        "impact": "high" if competitor["review_count"] > 300 else "medium"
                    },
                    "rating": {
                        "value": competitor["rating"],
                        "impact": "high" if competitor["rating"] > 4.4 else "medium"
                    },
                    "google_presence": {
                        "value": competitor.get("google_reviews", 0),
                        "impact": "high" if competitor.get("has_gmb") else "low"
                    },
                    "website_optimization": {
                        "value": competitor.get("has_website", False),
                        "impact": "medium" if competitor.get("has_website") else "low"
                    }
                }
            }
            ranking_factors.append(factors)
        
        return {
            "top_ranked": competitors[0] if competitors else None,
            "ranking_factors": ranking_factors,
            "key_ranking_signals": [
                "Review count and quality",
                "Google My Business optimization",
                "Proximity to search location",
                "Category relevance",
                "Website presence and SEO"
            ]
        }
    
    def _diagnose_issues(self, business_profile: BusinessProfile, 
                        competitors: List[Dict], query: str) -> List[Dict[str, Any]]:
        """Diagnose why the target business isn't ranking well."""
        issues = []
        
        # Compare with top competitors
        if competitors:
            top_competitor = competitors[0]
            
            # Review count issue
            if business_profile.review_count < top_competitor.get("review_count", 0) * 0.5:
                issues.append({
                    "issue_id": "low_review_count",
                    "title": "Low Review Count",
                    "description": f"Only {business_profile.review_count} reviews vs {top_competitor.get('review_count')} for top competitor",
                    "severity": "high",
                    "impact": "Significantly reduces local search visibility",
                    "evidence": f"Top competitor has {top_competitor.get('review_count')} reviews"
                })
            
            # Google My Business issue
            if not business_profile.google_my_business_id:
                issues.append({
                    "issue_id": "missing_gmb",
                    "title": "Missing or Incomplete Google My Business Profile",
                    "description": "No Google My Business ID found",
                    "severity": "critical",
                    "impact": "Cannot appear in local pack results without GMB",
                    "evidence": "All top competitors have optimized GMB profiles"
                })
            
            # Keyword optimization
            issues.append({
                "issue_id": "keyword_optimization",
                "title": "Suboptimal Keyword Usage",
                "description": "Target keywords not effectively used in business listings",
                "severity": "medium",
                "impact": "Reduces relevance for search queries like 'bar near Bleecker Street'",
                "evidence": f"Query keywords not prominent in current profile"
            })
            
            # Citation consistency
            if business_profile.citation_count is None or business_profile.citation_count < 10:
                issues.append({
                    "issue_id": "low_citations",
                    "title": "Low Local Citation Count",
                    "description": "Insufficient presence across local directories",
                    "severity": "medium",
                    "impact": "Reduces local SEO authority",
                    "evidence": f"Estimated citations: {business_profile.citation_count or 'unknown'}"
                })
        
        return issues
    
    def _analyze_seo_gaps(self, business_profile: BusinessProfile, 
                         competitors: List[Dict]) -> Dict[str, Any]:
        """Analyze SEO gaps compared to competitors."""
        gaps = {
            "on_page_seo": {
                "missing_elements": [],
                "optimization_opportunities": []
            },
            "local_seo": {
                "gmb_status": "missing" if not business_profile.google_my_business_id else "incomplete",
                "citation_count": business_profile.citation_count or 0,
                "competitor_avg_citations": 25  # Mock value
            },
            "content_seo": {
                "blog_content": "none_detected",
                "social_signals": "weak" if not business_profile.facebook_url else "moderate"
            },
            "technical_seo": {
                "schema_markup": "not_detected",
                "mobile_friendly": "unknown"
            }
        }
        
        # Add specific gaps
        if not business_profile.google_my_business_id:
            gaps["local_seo"]["gmb_status"] = "missing"
            gaps["on_page_seo"]["missing_elements"].append("Google My Business profile")
        
        if business_profile.citation_count is None or business_profile.citation_count < 10:
            gaps["on_page_seo"]["optimization_opportunities"].append(
                "Build citations on local directories (target: 20+ citations)"
            )
        
        return gaps
    
    def _identify_opportunities(self, business_profile: BusinessProfile, 
                               competitors: List[Dict]) -> List[Dict[str, Any]]:
        """Identify opportunities for improvement."""
        opportunities = []
        
        # Review generation opportunity
        opportunities.append({
            "opportunity_id": "review_generation",
            "title": "Review Generation Campaign",
            "description": "Actively solicit reviews from satisfied customers",
            "potential_impact": "high",
            "effort": "medium",
            "reason": "Reviews are a primary ranking factor for local search"
        })
        
        # Content marketing
        opportunities.append({
            "opportunity_id": "content_marketing",
            "title": "Local Content Marketing",
            "description": "Create blog content about 'best bars on Bleecker Street' and local area",
            "potential_impact": "medium",
            "effort": "medium",
            "reason": "Content helps with keyword targeting and link building"
        })
        
        # Citation building
        opportunities.append({
            "opportunity_id": "citation_building",
            "title": "Local Citation Building",
            "description": "Get listed on local directories and citation sites",
            "potential_impact": "high",
            "effort": "medium",
            "reason": "Citations improve local SEO authority"
        })
        
        return opportunities
    
    def _estimate_rank(self, business_profile: BusinessProfile, 
                      competitors: List[Dict]) -> Dict[str, Any]:
        """Estimate current ranking position."""
        # Simple heuristic based on profile data
        score = 0
        
        if business_profile.google_my_business_id:
            score += 30
        if business_profile.review_count > 100:
            score += 20
        elif business_profile.review_count > 50:
            score += 10
        if business_profile.website:
            score += 15
        if business_profile.citation_count and business_profile.citation_count > 15:
            score += 20
        
        # Estimate rank (lower is better, 1-10 range)
        estimated_position = max(1, 11 - (score // 10))
        
        return {
            "estimated_position": estimated_position,
            "ranking_score": score,
            "max_score": 100,
            "visibility_status": "high" if estimated_position <= 3 else "medium" if estimated_position <= 7 else "low"
        }
    
    def _generate_summary(self, query: str, business_profile: BusinessProfile, 
                         issues: List[Dict], opportunities: List[Dict]) -> str:
        """Generate human-readable summary."""
        critical_count = len([i for i in issues if i.get("severity") == "critical"])
        high_count = len([i for i in issues if i.get("severity") == "high"])
        
        summary = f"""
Analysis Summary for {business_profile.name}:
- Query: "{query}"
- Competitors analyzed: Multiple businesses in the area
- Critical issues found: {critical_count}
- High-priority issues: {high_count}
- Opportunities identified: {len(opportunities)}

Key Findings:
{issues[0]['title'] if issues else 'No critical issues found'} - {issues[0]['description'] if issues else ''}

Recommended focus areas:
1. {opportunities[0]['title'] if opportunities else 'General optimization'}
2. {opportunities[1]['title'] if len(opportunities) > 1 else 'Review management'}
        """
        return summary.strip()
