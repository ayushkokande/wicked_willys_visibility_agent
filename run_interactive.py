#!/usr/bin/env python3
"""Interactive runner for the Visibility Optimization System."""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from core.orchestrator import VisibilityOrchestrator
from core.business_profile import WICKED_WILLYS_PROFILE, BusinessProfile
from agents.agent1_analysis import Agent1Analysis
from agents.agent2_action_planning import Agent2ActionPlanning
from agents.agent3_execution import Agent3Execution


def print_banner():
    """Print welcome banner."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║   🍺 Wicked Willy's Visibility Optimization System 🍺            ║
║   Three-Agent Architecture for Business Discoverability          ║
╚══════════════════════════════════════════════════════════════════╝
    """)


def print_help():
    """Print help information."""
    print("""
Commands:
  help     - Show this help message
  query    - Enter a visibility query
  status   - Show current business profile
  history  - Show query history
  exit     - Exit the program

Example Queries:
  • "Why don't I show up for 'bar near Bleecker Street'?"
  • "How can I improve my local search ranking?"
  • "What are my competitors doing better?"
  • "How do I get more reviews?"
    """)


def run_mock_mode():
    """Run in mock mode (no LLM required)."""
    print("\n🔧 Running in MOCK MODE (no API keys required)")
    print("   Using simulated data for demonstration\n")
    
    orchestrator = VisibilityOrchestrator(business_profile=WICKED_WILLYS_PROFILE)
    agent1 = Agent1Analysis()
    agent2 = Agent2ActionPlanning()
    agent3 = Agent3Execution()
    
    return orchestrator, agent1, agent2, agent3


def run_llm_mode(provider: str = "openai"):
    """Run with real LLM integration."""
    from utils.llm_client import LLMClient
    from agents.agent1_analysis_llm import Agent1AnalysisLLM
    
    print(f"\n🤖 Running in LLM MODE with {provider.upper()}")
    print("   Using real AI for intelligent analysis\n")
    
    llm_client = LLMClient(provider=provider)
    
    orchestrator = VisibilityOrchestrator(business_profile=WICKED_WILLYS_PROFILE)
    agent1 = Agent1AnalysisLLM(llm_client=llm_client)
    agent2 = Agent2ActionPlanning()  # Planning logic is rule-based
    agent3 = Agent3Execution()  # Execution is rule-based
    
    return orchestrator, agent1, agent2, agent3


def display_results(results: dict):
    """Display results in a readable format."""
    print("\n" + "="*60)
    print("📊 ANALYSIS RESULTS")
    print("="*60)
    
    analysis = results.get("agent1_analysis", {})
    
    # Show issues
    issues = analysis.get("issues", [])
    if issues:
        print("\n🔴 Issues Found:")
        for i, issue in enumerate(issues[:5], 1):
            severity = issue.get("severity", "unknown")
            emoji = "🔴" if severity == "critical" else "🟠" if severity == "high" else "🟡"
            print(f"  {emoji} {i}. {issue.get('title', 'Unknown')}")
            print(f"     {issue.get('description', '')[:100]}...")
    
    # Show opportunities
    opportunities = analysis.get("opportunities", [])
    if opportunities:
        print("\n🟢 Opportunities:")
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"  {i}. {opp.get('title', 'Unknown')}")
            print(f"     Impact: {opp.get('potential_impact', 'unknown')}")
    
    print("\n" + "="*60)
    print("📋 ACTION PLAN")
    print("="*60)
    
    action_plan = results.get("agent2_action_plan", {})
    actions = action_plan.get("actions", [])
    
    automated = [a for a in actions if a.get("automation_level") == "fully_automated"]
    manual = [a for a in actions if a.get("automation_level") == "manual"]
    
    if automated:
        print("\n⚡ Automated Actions (will execute):")
        for i, action in enumerate(automated, 1):
            print(f"  {i}. {action.get('title', 'Unknown')}")
    
    if manual:
        print("\n📝 Manual Actions (guidance provided):")
        for i, action in enumerate(manual, 1):
            print(f"  {i}. {action.get('title', 'Unknown')}")
    
    print("\n" + "="*60)
    print("⚙️  EXECUTION RESULTS")
    print("="*60)
    
    execution = results.get("agent3_execution", {})
    print(f"\n✅ Completed: {execution.get('completed_count', 0)}")
    print(f"❌ Failed: {execution.get('failed_count', 0)}")
    
    materials = execution.get("generated_materials", {})
    if materials:
        print(f"\n📄 Materials Generated: {len(materials)}")
        for action_id, material in materials.items():
            print(f"  • {material.get('type', 'Unknown')}: {material.get('usage', '')[:50]}...")


def main():
    """Main interactive loop."""
    print_banner()
    
    # Check for API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Select mode
    if openai_key or anthropic_key:
        print("API key detected. Choose mode:")
        print("  1. Mock mode (simulated data)")
        print("  2. OpenAI mode (GPT-4)")
        print("  3. Anthropic mode (Claude)")
        
        choice = input("\nSelect mode (1/2/3) [1]: ").strip() or "1"
        
        if choice == "2" and openai_key:
            orchestrator, agent1, agent2, agent3 = run_llm_mode("openai")
        elif choice == "3" and anthropic_key:
            orchestrator, agent1, agent2, agent3 = run_llm_mode("anthropic")
        else:
            orchestrator, agent1, agent2, agent3 = run_mock_mode()
    else:
        print("No API keys found. Running in mock mode.")
        print("To use LLM mode, set OPENAI_API_KEY or ANTHROPIC_API_KEY in environment.\n")
        orchestrator, agent1, agent2, agent3 = run_mock_mode()
    
    print_help()
    
    # Interactive loop
    while True:
        try:
            user_input = input("\n🍺 Wicked Willy's > ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("\nGoodbye! 🍺")
                break
            
            if user_input.lower() == "help":
                print_help()
                continue
            
            if user_input.lower() == "status":
                profile = orchestrator.business_profile
                print(f"\n📍 Business: {profile.name}")
                print(f"   Address: {profile.address}")
                print(f"   Category: {profile.primary_category}")
                print(f"   Reviews: {profile.review_count}")
                print(f"   Keywords: {', '.join(profile.target_keywords[:3])}")
                continue
            
            if user_input.lower() == "history":
                history = orchestrator.get_history()
                queries = history.get("queries", [])
                if queries:
                    print("\n📜 Query History:")
                    for i, q in enumerate(queries, 1):
                        print(f"  {i}. {q.get('query', 'Unknown')[:50]}...")
                else:
                    print("\nNo queries yet.")
                continue
            
            # Treat as query
            print(f"\n🔍 Processing query: {user_input}\n")
            results = orchestrator.process_query(user_input, agent1, agent2, agent3)
            display_results(results)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 🍺")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue


if __name__ == "__main__":
    main()
