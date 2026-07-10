"""Main entry point for the Business Visibility Optimization System."""

from typing import Any
from core.orchestrator import VisibilityOrchestrator
from core.business_profile import DEFAULT_PROFILE
from agents.agent1_analysis import Agent1Analysis
from agents.agent2_action_planning import Agent2ActionPlanning
from agents.agent3_execution import Agent3Execution
import json


def print_section(title: str, content: Any):
    """Pretty print a section of results."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(content)
    print()


def main():
    """Main function to run the visibility optimization system."""
    
    print("""
╔════════════════════════════════════════════════════════════╗
║   Business Visibility Optimization System                 ║
║   Three-Agent Architecture for Business Discoverability   ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Initialize system
    orchestrator = VisibilityOrchestrator(business_profile=DEFAULT_PROFILE)

    # Initialize agents
    agent1 = Agent1Analysis()
    agent2 = Agent2ActionPlanning()
    agent3 = Agent3Execution()

    # Example queries
    primary_keyword = DEFAULT_PROFILE.target_keywords[0] if DEFAULT_PROFILE.target_keywords else "business near me"
    secondary_keyword = DEFAULT_PROFILE.target_keywords[-1] if DEFAULT_PROFILE.target_keywords else "best local business"
    example_queries = [
        f"Why don't I show up when people search for '{primary_keyword}'?",
        "What can I do to rank higher in local search results?",
        f"How do I improve my visibility for '{secondary_keyword}'?"
    ]
    
    print("Example queries you can ask:")
    for i, q in enumerate(example_queries, 1):
        print(f"  {i}. {q}")
    
    print("\n" + "="*60)
    print("Starting with example query...")
    print("="*60)
    
    # Run example query
    query = example_queries[0]
    results = orchestrator.process_query(query, agent1, agent2, agent3)
    
    # Display results
    print_section(
        "📊 Agent 1: Analysis Results",
        json.dumps(results["agent1_analysis"], indent=2)
    )
    
    print_section(
        "📋 Agent 2: Action Plan",
        json.dumps(results["agent2_action_plan"], indent=2)
    )
    
    print_section(
        "⚙️  Agent 3: Execution Results",
        json.dumps(results["agent3_execution"], indent=2)
    )
    
    # Show generated materials
    execution = results["agent3_execution"]
    if execution.get("generated_materials"):
        print_section(
            "📄 Generated Materials",
            f"{len(execution['generated_materials'])} materials generated"
        )
        for action_id, material in execution["generated_materials"].items():
            print(f"\n--- Material for Action: {action_id} ---")
            print(f"Type: {material.get('type')}")
            if material.get('content'):
                print(f"Content:\n{material['content'][:500]}..." if len(str(material['content'])) > 500 else f"Content:\n{material['content']}")
    
    print("\n" + "="*60)
    print("✅ System demonstration complete!")
    print("="*60)
    print("\nTo use interactively, modify main() to accept user input.")


if __name__ == "__main__":
    main()
