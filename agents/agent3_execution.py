"""Agent 3: Execution Agent - Executes allowed actions on behalf of the business."""

from typing import Dict, Any, List
from datetime import datetime
from core.business_profile import BusinessProfile
from core.allowed_actions import ActionPlan, AllowedAction, ActionType, AutomationLevel


class Agent3Execution:
    """
    Agent 3: Execution Agent
    
    Responsibilities:
    - Execute automated actions from Agent 2's plan
    - Generate materials for manual actions
    - Track execution status
    - Report results
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize Agent 3.
        
        Args:
            llm_client: LLM client for content generation (optional)
        """
        self.llm_client = llm_client
        
    def execute_actions(self, action_plan: ActionPlan, 
                       business_profile: BusinessProfile) -> Dict[str, Any]:
        """
        Execute actions from the action plan.
        
        Args:
            action_plan: Action plan from Agent 2
            business_profile: Business being optimized
            
        Returns:
            Execution results with completed actions and materials
        """
        print(f"  Executing {action_plan.total_actions} actions...")
        
        completed_actions = []
        failed_actions = []
        generated_materials = {}
        manual_instructions = []
        
        # Process each action
        for action in action_plan.actions:
            try:
                result = self._execute_action(action, business_profile)
                
                if result["status"] == "completed":
                    completed_actions.append(action.action_id)
                    action.status = "completed"
                    action.completed_at = datetime.now()
                    
                    if result.get("material"):
                        generated_materials[action.action_id] = result["material"]
                    
                    if result.get("manual_instructions"):
                        manual_instructions.extend(result["manual_instructions"])
                else:
                    failed_actions.append(action.action_id)
                    action.status = "failed"
                    
            except Exception as e:
                print(f"    ⚠️  Error executing {action.action_id}: {str(e)}")
                failed_actions.append(action.action_id)
                action.status = "failed"
        
        execution_result = {
            "execution_id": action_plan.plan_id,
            "timestamp": datetime.now().isoformat(),
            "total_actions": action_plan.total_actions,
            "completed_count": len(completed_actions),
            "failed_count": len(failed_actions),
            "completed_actions": completed_actions,
            "failed_actions": failed_actions,
            "generated_materials": generated_materials,
            "manual_instructions": manual_instructions,
            "summary": self._generate_execution_summary(action_plan, completed_actions, failed_actions)
        }
        
        print(f"  → Completed: {len(completed_actions)}, Failed: {len(failed_actions)}")
        
        return execution_result
    
    def _execute_action(self, action: AllowedAction, 
                       business_profile: BusinessProfile) -> Dict[str, Any]:
        """Execute a single action."""
        print(f"    Executing: {action.title}...")
        
        if action.automation_level == AutomationLevel.FULLY_AUTOMATED:
            return self._execute_automated_action(action, business_profile)
        elif action.automation_level == AutomationLevel.PARTIALLY_AUTOMATED:
            return self._execute_partial_action(action, business_profile)
        else:
            return self._generate_manual_instructions(action, business_profile)
    
    def _execute_automated_action(self, action: AllowedAction,
                                 business_profile: BusinessProfile) -> Dict[str, Any]:
        """Execute a fully automated action."""
        
        if action.action_type == ActionType.GENERATE_CONTENT:
            material = self._generate_gmb_description(business_profile)
            return {
                "status": "completed",
                "material": {
                    "type": "gmb_description",
                    "content": material,
                    "usage": "Copy this description into your Google My Business profile"
                }
            }
        
        elif action.action_type == ActionType.CREATE_SCHEMA_MARKUP:
            material = self._generate_schema_markup(business_profile)
            return {
                "status": "completed",
                "material": {
                    "type": "schema_markup",
                    "content": material,
                    "usage": "Add this JSON-LD script to the <head> section of your website"
                }
            }
        
        elif action.action_type == ActionType.GENERATE_META_TAGS:
            material = self._generate_meta_tags(business_profile)
            return {
                "status": "completed",
                "material": {
                    "type": "meta_tags",
                    "content": material,
                    "usage": "Add these meta tags to your website's <head> section"
                }
            }
        
        elif action.action_type == ActionType.CREATE_CITATION_LIST:
            material = self._generate_citation_list(business_profile)
            return {
                "status": "completed",
                "material": {
                    "type": "citation_list",
                    "content": material,
                    "usage": "Submit your business to these directories"
                }
            }
        
        elif action.action_type == ActionType.CREATE_BLOG_POST:
            material = self._generate_blog_post(business_profile)
            return {
                "status": "completed",
                "material": {
                    "type": "blog_post",
                    "content": material,
                    "usage": "Publish this blog post on your website"
                }
            }
        
        else:
            return {"status": "not_implemented", "message": f"Action type {action.action_type} not yet implemented"}
    
    def _execute_partial_action(self, action: AllowedAction,
                               business_profile: BusinessProfile) -> Dict[str, Any]:
        """Execute a partially automated action (generates materials)."""
        if action.action_type == ActionType.MANAGE_REVIEWS:
            material = self._generate_review_templates(business_profile)
            return {
                "status": "completed",
                "material": {
                    "type": "review_templates",
                    "content": material
                },
                "manual_instructions": [
                    "Use these templates to request reviews from customers",
                    "Set up automated review request emails"
                ]
            }
        return {"status": "not_implemented"}
    
    def _generate_manual_instructions(self, action: AllowedAction,
                                     business_profile: BusinessProfile) -> Dict[str, Any]:
        """Generate instructions for manual actions."""
        instructions = [
            f"Action: {action.title}",
            f"Description: {action.description}",
            f"Reason: {action.reason}",
            f"Steps:",
            f"1. [Action-specific steps would be generated here]",
            f"2. Verify completion",
            f"3. Check results"
        ]
        
        return {
            "status": "pending_manual",
            "manual_instructions": instructions
        }
    
    # Content generation methods
    
    def _generate_gmb_description(self, business_profile: BusinessProfile) -> str:
        """Generate optimized GMB description."""
        keywords = ", ".join(business_profile.target_keywords[:3])
        
        description = f"""
Welcome to {business_profile.name}, located in the heart of Greenwich Village at {business_profile.address}.

{business_profile.name} is your premier destination for {keywords}. We offer a unique blend of [bar/restaurant experience] with [key features].

Whether you're looking for [specific offerings], {business_profile.name} provides an unforgettable experience. Our location on Bleecker Street puts us in the center of Greenwich Village's vibrant nightlife scene.

Visit us for [hours/events/specialties]. We're easily accessible by [transportation] and are a favorite among locals and visitors alike.

Keywords: {", ".join(business_profile.target_keywords[:5])}
        """
        return description.strip()
    
    def _generate_schema_markup(self, business_profile: BusinessProfile) -> str:
        """Generate JSON-LD schema markup."""
        schema = {
            "@context": "https://schema.org",
            "@type": "BarOrPub",
            "name": business_profile.name,
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "149 Bleecker Street",
                "addressLocality": "New York",
                "addressRegion": "NY",
                "postalCode": "10012",
                "addressCountry": "US"
            },
            "telephone": business_profile.phone or "[Phone Number]",
            "url": business_profile.website,
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": str(business_profile.average_rating) if business_profile.average_rating else "4.0",
                "reviewCount": str(business_profile.review_count)
            }
        }
        
        import json
        return f"<script type=\"application/ld+json\">\n{json.dumps(schema, indent=2)}\n</script>"
    
    def _generate_meta_tags(self, business_profile: BusinessProfile) -> str:
        """Generate meta tags."""
        keywords = ", ".join(business_profile.target_keywords)
        description = f"{business_profile.name} - {', '.join(business_profile.target_keywords[:3])} in Greenwich Village"
        
        tags = f"""
<meta name="description" content="{description}">
<meta name="keywords" content="{keywords}">
<meta property="og:title" content="{business_profile.name}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="business.business">
<meta property="og:address:street_address" content="149 Bleecker Street">
<meta property="og:address:locality" content="New York">
<meta property="og:address:region" content="NY">
        """
        return tags.strip()
    
    def _generate_citation_list(self, business_profile: BusinessProfile) -> List[Dict[str, str]]:
        """Generate list of citation sites."""
        citations = [
            {"name": "Google My Business", "url": "https://business.google.com", "priority": "critical"},
            {"name": "Yelp", "url": "https://www.yelp.com", "priority": "high"},
            {"name": "TripAdvisor", "url": "https://www.tripadvisor.com", "priority": "high"},
            {"name": "Foursquare", "url": "https://foursquare.com", "priority": "medium"},
            {"name": "YellowPages", "url": "https://www.yellowpages.com", "priority": "medium"},
            {"name": "Better Business Bureau", "url": "https://www.bbb.org", "priority": "medium"},
            {"name": "Local.com", "url": "https://www.local.com", "priority": "medium"},
            {"name": "Manta", "url": "https://www.manta.com", "priority": "low"},
            {"name": "CitySearch", "url": "https://www.citysearch.com", "priority": "low"},
            {"name": "Zomato", "url": "https://www.zomato.com", "priority": "medium"},
        ]
        return citations
    
    def _generate_blog_post(self, business_profile: BusinessProfile) -> str:
        """Generate a blog post for content marketing."""
        post = f"""
# The Ultimate Guide to the Best Bars on Bleecker Street

If you're searching for the perfect bar experience in Greenwich Village, look no further than Bleecker Street. This iconic street is home to some of New York City's most beloved drinking establishments, including {business_profile.name} at 149 Bleecker Street.

## Why Bleecker Street is a Bar Lover's Paradise

Bleecker Street has a rich history as one of Greenwich Village's premier nightlife destinations. With its central location and vibrant atmosphere, it's the perfect spot for both locals and visitors to experience authentic New York City bar culture.

## What Makes {business_profile.name} Special

Located at the heart of Bleecker Street, {business_profile.name} offers an unforgettable experience that combines [unique features]. Whether you're looking for [specific offerings], we've got you covered.

## The Best Time to Visit

[Content about timing, events, specials, etc.]

## How to Get There

{business_profile.name} is easily accessible by [transportation options] and is just a short walk from [landmarks].

Keywords: {", ".join(business_profile.target_keywords)}
        """
        return post.strip()
    
    def _generate_review_templates(self, business_profile: BusinessProfile) -> Dict[str, str]:
        """Generate review request templates."""
        templates = {
            "email_subject": f"Enjoyed your visit to {business_profile.name}? We'd love your feedback!",
            "email_body": f"""
Hi [Customer Name],

Thank you for visiting {business_profile.name} at {business_profile.address}! We hope you had a great experience.

If you enjoyed your visit, we'd be incredibly grateful if you could share your thoughts on Google: [Review Link]

Your feedback helps other guests discover us and means the world to our team.

Thank you!
{business_profile.name}
            """,
            "in_person_ask": "We'd love it if you could leave us a review on Google - it really helps us out!"
        }
        return templates
    
    def _generate_execution_summary(self, action_plan: ActionPlan,
                                   completed: List[str], failed: List[str]) -> str:
        """Generate execution summary."""
        return f"""
Execution Summary:
- Total actions: {action_plan.total_actions}
- Successfully completed: {len(completed)}
- Failed: {len(failed)}
- Automation rate: {(len(completed) / action_plan.total_actions * 100) if action_plan.total_actions > 0 else 0:.1f}%

Next steps: Review generated materials and follow manual instructions for remaining actions.
        """.strip()
