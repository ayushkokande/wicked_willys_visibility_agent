"""Defines allowed actions that can be taken by the visibility optimization system."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ActionType(str, Enum):
    """Types of actions that can be taken."""
    # Automated Actions
    GENERATE_CONTENT = "generate_content"
    CREATE_SCHEMA_MARKUP = "create_schema_markup"
    GENERATE_META_TAGS = "generate_meta_tags"
    CREATE_CITATION_LIST = "create_citation_list"
    GENERATE_SITEMAP = "generate_sitemap"
    CREATE_BLOG_POST = "create_blog_post"
    GENERATE_SOCIAL_CONTENT = "generate_social_content"
    CREATE_REPORT = "create_report"
    
    # Manual Actions (guided)
    UPDATE_GMB_PROFILE = "update_gmb_profile"
    SUBMIT_TO_DIRECTORIES = "submit_to_directories"
    OPTIMIZE_WEBSITE_CONTENT = "optimize_website_content"
    BUILD_BACKLINKS = "build_backlinks"
    CLAIM_LISTINGS = "claim_listings"
    MANAGE_REVIEWS = "manage_reviews"


class ActionPriority(str, Enum):
    """Priority levels for actions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AutomationLevel(str, Enum):
    """Level of automation for actions."""
    FULLY_AUTOMATED = "fully_automated"  # Agent 3 can execute directly
    PARTIALLY_AUTOMATED = "partially_automated"  # Agent 3 generates materials
    MANUAL = "manual"  # Requires human action


class AllowedAction(BaseModel):
    """Represents an allowed action that can be taken."""
    
    action_id: str = Field(..., description="Unique identifier for the action")
    action_type: ActionType = Field(..., description="Type of action")
    title: str = Field(..., description="Human-readable action title")
    description: str = Field(..., description="Detailed description of the action")
    priority: ActionPriority = Field(..., description="Action priority")
    automation_level: AutomationLevel = Field(..., description="Automation capability")
    
    # Impact estimation
    estimated_impact: str = Field(..., description="Expected impact description")
    difficulty: str = Field(..., description="Difficulty level (easy/medium/hard)")
    time_required: Optional[str] = Field(None, description="Estimated time to complete")
    
    # Requirements
    required_resources: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list, description="Action IDs that must complete first")
    
    # Context
    reason: str = Field(..., description="Why this action is recommended")
    related_issue: Optional[str] = Field(None, description="Issue from Agent 1 this addresses")
    
    # Status
    status: str = Field(default="pending", description="pending/in_progress/completed/failed")
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Execution data (for automated actions)
    execution_data: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "action_id": "action_001",
                "action_type": "generate_content",
                "title": "Generate Optimized Google My Business Description",
                "description": "Create an SEO-optimized description for GMB profile with target keywords",
                "priority": "high",
                "automation_level": "fully_automated",
                "estimated_impact": "High - Improves local search visibility",
                "difficulty": "easy",
                "time_required": "5 minutes",
                "reason": "Current GMB description lacks target keywords and compelling copy",
                "related_issue": "Missing keyword optimization in GMB profile"
            }
        }


class ActionPlan(BaseModel):
    """Collection of allowed actions with metadata."""
    
    plan_id: str = Field(..., description="Unique plan identifier")
    query: str = Field(..., description="Original business query")
    actions: List[AllowedAction] = Field(..., description="List of allowed actions")
    total_actions: int = Field(..., description="Total number of actions")
    automated_count: int = Field(..., description="Count of fully automated actions")
    manual_count: int = Field(..., description="Count of manual actions")
    
    created_at: datetime = Field(default_factory=datetime.now)
    analysis_id: Optional[str] = Field(None, description="Reference to Agent 1 analysis")
    
    def get_actions_by_priority(self, priority: ActionPriority) -> List[AllowedAction]:
        """Get actions filtered by priority."""
        return [a for a in self.actions if a.priority == priority]
    
    def get_automated_actions(self) -> List[AllowedAction]:
        """Get actions that can be fully automated."""
        return [a for a in self.actions if a.automation_level == AutomationLevel.FULLY_AUTOMATED]
    
    def get_manual_actions(self) -> List[AllowedAction]:
        """Get actions that require manual intervention."""
        return [a for a in self.actions if a.automation_level == AutomationLevel.MANUAL]


# Action Registry - Defines what actions are available
ACTION_REGISTRY = {
    ActionType.GENERATE_CONTENT: {
        "automation_level": AutomationLevel.FULLY_AUTOMATED,
        "default_priority": ActionPriority.HIGH,
        "category": "Content"
    },
    ActionType.CREATE_SCHEMA_MARKUP: {
        "automation_level": AutomationLevel.FULLY_AUTOMATED,
        "default_priority": ActionPriority.HIGH,
        "category": "Technical SEO"
    },
    ActionType.GENERATE_META_TAGS: {
        "automation_level": AutomationLevel.FULLY_AUTOMATED,
        "default_priority": ActionPriority.HIGH,
        "category": "Technical SEO"
    },
    ActionType.CREATE_CITATION_LIST: {
        "automation_level": AutomationLevel.FULLY_AUTOMATED,
        "default_priority": ActionPriority.MEDIUM,
        "category": "Local SEO"
    },
    ActionType.CREATE_BLOG_POST: {
        "automation_level": AutomationLevel.FULLY_AUTOMATED,
        "default_priority": ActionPriority.MEDIUM,
        "category": "Content"
    },
    ActionType.UPDATE_GMB_PROFILE: {
        "automation_level": AutomationLevel.MANUAL,
        "default_priority": ActionPriority.HIGH,
        "category": "Local SEO"
    },
    ActionType.SUBMIT_TO_DIRECTORIES: {
        "automation_level": AutomationLevel.MANUAL,
        "default_priority": ActionPriority.MEDIUM,
        "category": "Local SEO"
    }
}
