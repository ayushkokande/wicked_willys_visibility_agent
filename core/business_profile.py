"""Business profile data model for Wicked Willy's and other businesses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BusinessProfile(BaseModel):
    """Represents a business profile with all relevant visibility data."""
    
    name: str = Field(..., description="Business name")
    address: str = Field(..., description="Full business address")
    phone: Optional[str] = Field(None, description="Business phone number")
    website: Optional[str] = Field(None, description="Business website URL")
    
    # Local SEO Data
    google_my_business_id: Optional[str] = None
    yelp_id: Optional[str] = None
    review_count: int = 0
    average_rating: float = 0.0
    
    # SEO Metrics
    domain_authority: Optional[int] = None
    backlink_count: Optional[int] = None
    citation_count: Optional[int] = None
    
    # Social Presence
    facebook_url: Optional[str] = None
    instagram_handle: Optional[str] = None
    twitter_handle: Optional[str] = None
    
    # Keywords & Categories
    primary_category: Optional[str] = None
    secondary_categories: List[str] = Field(default_factory=list)
    target_keywords: List[str] = Field(default_factory=list)
    
    # Timestamps
    last_analyzed: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Wicked Willy's",
                "address": "149 Bleecker Street, New York, NY 10012",
                "phone": "+1-212-XXX-XXXX",
                "website": "https://wickedwillys.com",
                "primary_category": "Bar",
                "secondary_categories": ["Restaurant", "Nightlife"],
                "target_keywords": ["bar near Bleecker Street", "Greenwich Village bar"]
            }
        }


# Default profile for Wicked Willy's
WICKED_WILLYS_PROFILE = BusinessProfile(
    name="Wicked Willy's",
    address="149 Bleecker Street, New York, NY 10012",
    primary_category="Bar",
    secondary_categories=["Restaurant", "Nightlife", "American Cuisine"],
    target_keywords=[
        "bar near Bleecker Street",
        "Greenwich Village bar",
        "restaurant near Bleecker Street",
        "best bar in Greenwich Village"
    ]
)
