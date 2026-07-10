"""Main orchestrator that coordinates the three-agent system."""

from typing import Optional, Dict, Any
from datetime import datetime
from core.business_profile import BusinessProfile, DEFAULT_PROFILE
from core.allowed_actions import ActionPlan
import uuid


class VisibilityOrchestrator:
    """
    Orchestrates the flow between the three agents:
    Agent 1: Analysis
    Agent 2: Action Planning
    Agent 3: Execution
    """
    
    def __init__(self, business_profile: BusinessProfile = DEFAULT_PROFILE):
        """
        Initialize the orchestrator with a business profile.
        
        Args:
            business_profile: The business to optimize visibility for
        """
        self.business_profile = business_profile
        self.query_history: list = []
        self.analysis_history: list = []
        self.action_plan_history: list = []
        
    def process_query(self, query: str, agent1, agent2, agent3) -> Dict[str, Any]:
        """
        Process a business query through all three agents.
        
        Args:
            query: Business query string
            agent1: Agent 1 instance (Analysis Agent)
            agent2: Agent 2 instance (Action Planning Agent)
            agent3: Agent 3 instance (Execution Agent)
            
        Returns:
            Complete results from all agents
        """
        query_id = str(uuid.uuid4())
        
        # Store query
        self.query_history.append({
            "query_id": query_id,
            "query": query,
            "timestamp": datetime.now(),
            "business": self.business_profile.name
        })
        
        print(f"\n{'='*60}")
        print(f"Processing Query: {query}")
        print(f"Query ID: {query_id}")
        print(f"{'='*60}\n")
        
        # Agent 1: Analysis
        print("🔍 Agent 1: Running Analysis...")
        analysis_result = agent1.analyze(query, self.business_profile)
        self.analysis_history.append({
            "query_id": query_id,
            "analysis": analysis_result
        })
        
        # Agent 2: Action Planning
        print("\n📋 Agent 2: Planning Actions...")
        action_plan = agent2.plan_actions(analysis_result, self.business_profile)
        action_plan.analysis_id = analysis_result.get("analysis_id")
        self.action_plan_history.append({
            "query_id": query_id,
            "action_plan": action_plan
        })
        
        # Agent 3: Execution
        print("\n⚙️  Agent 3: Executing Actions...")
        # execution_result = agent3.execute_actions(action_plan, self.business_profile)
        execution_result = agent3.generate_action_plan(action_plan, self.business_profile)
        
        # Compile results
        results = {
            "query_id": query_id,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "business": self.business_profile.name,
            "agent1_analysis": analysis_result,
            "agent2_action_plan": action_plan.dict(),
            "agent3_execution": execution_result
        }
        
        print(f"\n{'='*60}")
        print("✅ Query Processing Complete")
        print(f"{'='*60}\n")
        
        return results
    
    def get_history(self) -> Dict[str, Any]:
        """Get complete query history."""
        return {
            "queries": self.query_history,
            "analyses": self.analysis_history,
            "action_plans": self.action_plan_history
        }
    
    def update_business_profile(self, updates: Dict[str, Any]):
        """Update business profile with new information."""
        for key, value in updates.items():
            if hasattr(self.business_profile, key):
                setattr(self.business_profile, key, value)
        self.business_profile.last_updated = datetime.now()
