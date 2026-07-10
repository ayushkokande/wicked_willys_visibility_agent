"""Business profile data model."""

import os
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
                "name": "Example Bar & Grill",
                "address": "123 Main Street, Springfield, ST 00000",
                "phone": "+1-555-XXX-XXXX",
                "website": "https://example.com",
                "primary_category": "Bar",
                "secondary_categories": ["Restaurant", "Nightlife"],
                "target_keywords": ["bar near Main Street", "downtown Springfield bar"]
            }
        }


def _split_env_list(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


# Default profile, configurable via environment variables:
# BUSINESS_NAME, BUSINESS_ADDRESS, BUSINESS_CATEGORY,
# BUSINESS_SECONDARY_CATEGORIES (comma-separated),
# BUSINESS_TARGET_KEYWORDS (comma-separated),
# BUSINESS_WEBSITE, BUSINESS_PHONE
DEFAULT_PROFILE = BusinessProfile(
    name=os.getenv("BUSINESS_NAME", "Example Bar & Grill"),
    address=os.getenv("BUSINESS_ADDRESS", "123 Main Street, Springfield, ST 00000"),
    phone=os.getenv("BUSINESS_PHONE"),
    website=os.getenv("BUSINESS_WEBSITE"),
    primary_category=os.getenv("BUSINESS_CATEGORY", "Bar"),
    secondary_categories=_split_env_list(
        os.getenv("BUSINESS_SECONDARY_CATEGORIES", "Restaurant,Nightlife")
    ),
    target_keywords=_split_env_list(
        os.getenv(
            "BUSINESS_TARGET_KEYWORDS",
            "bar near Main Street,downtown Springfield bar,best bar in Springfield",
        )
    ),
)
