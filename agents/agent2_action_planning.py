"""Agent 2: Action Planning Agent - Determines allowed actions based on analysis."""

from typing import Dict, Any, List
from datetime import datetime
from core.business_profile import BusinessProfile
from core.allowed_actions import (
    ActionPlan, AllowedAction, ActionType, ActionPriority, 
    AutomationLevel, ACTION_REGISTRY
)
import uuid


class Agent2ActionPlanning:
    """
    Agent 2: Action Planning Agent
    
    Responsibilities:
    - Review Agent 1's analysis
    - Identify actionable items
    - Determine allowed actions
    - Prioritize and categorize actions
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize Agent 2.
        
        Args:
            llm_client: LLM client for action planning (optional)
        """
        self.llm_client = llm_client
        
    def plan_actions(self, analysis_result: Dict[str, Any], 
                    business_profile: BusinessProfile) -> ActionPlan:
        """
        Create an action plan based on Agent 1's analysis.
        
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
        
        # Generate allowed actions
        actions = []
        
        # Map issues to actions
        for issue in issues:
            issue_actions = self._map_issue_to_actions(issue, seo_analysis, business_profile)
            actions.extend(issue_actions)
        
        # Map opportunities to actions
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
    
    def _map_issue_to_actions(self, issue: Dict[str, Any], 
                             seo_analysis: Dict[str, Any],
                             business_profile: BusinessProfile) -> List[AllowedAction]:
        """Map a specific issue to actionable items."""
        actions = []
        issue_id = issue.get("issue_id")
        severity = issue.get("severity", "medium")
        
        # Determine priority based on severity
        if severity == "critical":
            priority = ActionPriority.HIGH
        elif severity == "high":
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
            
            # Also generate content for GMB
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
                prerequisites=[actions[-1].action_id if actions else None]  # Depends on citation list
            ))
        
        return actions
    
    def _map_opportunity_to_actions(self, opportunity: Dict[str, Any],
                                   business_profile: BusinessProfile) -> List[AllowedAction]:
        """Map opportunities to actionable items."""
        actions = []
        opp_id = opportunity.get("opportunity_id")
        
        if opp_id == "content_marketing":
            actions.append(AllowedAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.CREATE_BLOG_POST,
                title="Create Local Content Blog Post",
                description=f"Generate blog post about '{business_profile.target_keywords[0] if business_profile.target_keywords else 'local area'}' to improve SEO",
                priority=ActionPriority.MEDIUM,
                automation_level=AutomationLevel.FULLY_AUTOMATED,
                estimated_impact="Medium - Helps with keyword targeting",
                difficulty="easy",
                time_required="15 minutes",
                reason=opportunity.get("description"),
                related_issue=opp_id
            ))
    
        elif opp_id == "citation_building":
            # Already handled by low_citations issue mapping
            pass
        
        return actions
    
    def _deduplicate_actions(self, actions: List[AllowedAction]) -> List[AllowedAction]:
        """Remove duplicate actions based on action_type."""
        seen_types = set()
        unique_actions = []
        
        for action in actions:
            if action.action_type not in seen_types:
                seen_types.add(action.action_type)
                unique_actions.append(action)
            else:
                # Keep the one with higher priority
                existing = next(a for a in unique_actions if a.action_type == action.action_type)
                if action.priority == ActionPriority.HIGH and existing.priority != ActionPriority.HIGH:
                    unique_actions.remove(existing)
                    unique_actions.append(action)
        
        return unique_actions
    
    def _prioritize_actions(self, actions: List[AllowedAction], 
                           issues: List[Dict[str, Any]]) -> List[AllowedAction]:
        """Prioritize actions based on impact and urgency."""
        # Sort by priority (HIGH, MEDIUM, LOW), then by impact description
        priority_order = {ActionPriority.HIGH: 0, ActionPriority.MEDIUM: 1, ActionPriority.LOW: 2}
        
        actions.sort(key=lambda a: (
            priority_order.get(a.priority, 99),
            a.estimated_impact.lower().startswith("high") if a.estimated_impact else False,
            a.action_id
        ))
        
        return actions
