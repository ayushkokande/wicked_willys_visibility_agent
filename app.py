"""Streamlit UI for the Business Visibility Agent - Step-by-Step Flow."""

import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="Business Visibility Agent",
    page_icon="📍",
    layout="wide"
)

# Now import the rest after page config
from core.business_profile import DEFAULT_PROFILE
from agents.agent1_analysis_llm import Agent1AnalysisLLM
from agents.agent2_action_planning import Agent2ActionPlanning
from agents.agent3_execution import Agent3Execution
from core.allowed_actions import ActionPlan


def init_session():
    """Initialize session state."""
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    if 'query' not in st.session_state:
        st.session_state.query = ""
    if 'agent1_output' not in st.session_state:
        st.session_state.agent1_output = None
    if 'agent2_output' not in st.session_state:
        st.session_state.agent2_output = None
    if 'agent3_output' not in st.session_state:
        st.session_state.agent3_output = None
    if 'use_llm' not in st.session_state:
        st.session_state.use_llm = True


def get_agent1(use_llm: bool):
    """Get Agent 1 based on mode."""
    if use_llm:
        try:
            from utils.llm_client import LLMClient
            from agents.agent1_analysis_llm import Agent1AnalysisLLM
            
            # Check for API keys - Try OpenAI first (Anthropic may have no credits)
            if os.getenv("OPENAI_API_KEY"):
                client = LLMClient(provider="openai")
                return Agent1AnalysisLLM(llm_client=client), "openai"
            elif os.getenv("ANTHROPIC_API_KEY"):
                client = LLMClient(provider="anthropic")
                return Agent1AnalysisLLM(llm_client=client), "anthropic"
        except Exception as e:
            st.warning(f"LLM not available: {e}. Using mock mode.")
    
    # Fallback to mock mode
    from agents.agent1_analysis import Agent1Analysis
    return Agent1Analysis(), "mock"


def reset_all():
    """Reset everything."""
    st.session_state.current_step = 1
    st.session_state.query = ""
    st.session_state.agent1_output = None
    st.session_state.agent2_output = None
    st.session_state.agent3_output = None


def main():
    """Main app."""
    init_session()
    
    # Header
    st.markdown(f"# 📍 {DEFAULT_PROFILE.name} Visibility Agent")
    st.markdown("**Three-Agent System for Business Discoverability**")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # API Key status
        has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        
        st.markdown("**API Keys:**")
        st.markdown(f"- Anthropic: {'✅' if has_anthropic else '❌'}")
        st.markdown(f"- OpenAI: {'✅' if has_openai else '❌'}")
        
        st.session_state.use_llm = st.checkbox(
            "Use LLM (Claude/GPT)", 
            value=st.session_state.use_llm,
            disabled=not (has_anthropic or has_openai)
        )
        
        st.markdown("---")
        st.markdown("## 📍 Business Profile")
        st.markdown(f"**{DEFAULT_PROFILE.name}**")
        st.markdown(f"📍 {DEFAULT_PROFILE.address}")
        st.markdown(f"🏷️ {DEFAULT_PROFILE.primary_category}")
        
        st.markdown("---")
        
        # Progress
        st.markdown("## 📊 Progress")
        steps = ["Query", "Agent 1", "Agent 2", "Agent 3"]
        for i, step in enumerate(steps, 1):
            if i < st.session_state.current_step:
                st.markdown(f"✅ Step {i}: {step}")
            elif i == st.session_state.current_step:
                st.markdown(f"🔵 **Step {i}: {step}**")
            else:
                st.markdown(f"⚪ Step {i}: {step}")
        
        st.markdown("---")
        if st.button("🔄 Start Over", use_container_width=True):
            reset_all()
            st.rerun()
    
    # Main content based on current step
    if st.session_state.current_step == 1:
        render_step1()
    elif st.session_state.current_step == 2:
        render_step2()
    elif st.session_state.current_step == 3:
        render_step3()
    elif st.session_state.current_step == 4:
        render_step4()


def render_step1():
    """Step 1: Enter query."""
    st.markdown("## Step 1: Enter Your Question")
    
    st.markdown("Ask about your business visibility:")
    
    example_keyword = (
        DEFAULT_PROFILE.target_keywords[0]
        if DEFAULT_PROFILE.target_keywords
        else f"{DEFAULT_PROFILE.primary_category or 'business'} near me"
    )

    query = st.text_area(
        "Your question:",
        placeholder=f"Why don't I show up when people search for '{example_keyword}'?",
        height=100,
        key="query_input"
    )

    st.markdown("**Quick examples:**")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(example_keyword.title(), use_container_width=True):
            query = f"Why don't I show up when people search for '{example_keyword}'?"
    with col2:
        if st.button("Improve local ranking", use_container_width=True):
            query = "How can I improve my local search ranking?"
    with col3:
        if st.button("Get more reviews", use_container_width=True):
            query = "How do I get more reviews for my business?"
    
    st.markdown("---")
    
    if st.button("🔍 Run Agent 1: Analyze →", type="primary", disabled=not query):
        st.session_state.query = query
        st.session_state.current_step = 2
        st.rerun()


def render_step2():
    """Step 2: Agent 1 Analysis."""
    st.markdown("## Step 2: Agent 1 - Discovery & Analysis")
    
    # Show input
    with st.expander("📥 Input to Agent 1", expanded=True):
        st.markdown(f"**Query:** {st.session_state.query}")
        st.markdown(f"**Business:** {DEFAULT_PROFILE.name}")
    
    # Run Agent 1 if needed
    if st.session_state.agent1_output is None:
        with st.spinner("🤖 Agent 1 is analyzing..."):
            try:
                agent1, mode = get_agent1(st.session_state.use_llm)
                st.info(f"Using: {mode.upper()} mode")
                result = agent1.analyze(st.session_state.query, DEFAULT_PROFILE)
                st.session_state.agent1_output = result
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
                if st.button("⬅️ Back"):
                    st.session_state.current_step = 1
                    st.rerun()
                return
    
    # Display results
    result = st.session_state.agent1_output
    st.success("✅ Agent 1 Complete!")
    
    # Get ranked results
    ranked_results = result.get("ranked_results", [])
    inferred_location = result.get("inferred_location", "Unknown")
    
    # Check if the target business is in the results
    business_name_lower = DEFAULT_PROFILE.name.lower()
    business_in_results = any(business_name_lower in r.get("name", "").lower() for r in ranked_results)
    business_rank = next((r.get("rank") for r in ranked_results if business_name_lower in r.get("name", "").lower()), None)
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Results Ranked", len(ranked_results))
    with col2:
        st.metric("Location", inferred_location[:20] + "..." if len(inferred_location) > 20 else inferred_location)
    with col3:
        if business_in_results:
            st.metric(f"{DEFAULT_PROFILE.name} Rank", f"#{business_rank}")
        else:
            st.metric(f"{DEFAULT_PROFILE.name} Rank", "❌ Not Found")
    
    # Tabs for results
    tab1, tab2 = st.tabs(["📊 Ranked Results", "📋 Full Output"])
    
    with tab1:
        if ranked_results:
            for r in ranked_results:
                rank = r.get("rank", "?")
                name = r.get("name", "Unknown")
                address = r.get("address", "")
                reason_tokens = r.get("reason_tokens", [])
                
                # Highlight the target business
                if business_name_lower in name.lower():
                    st.markdown(f"**#{rank} 📍 {name}** ⬅️ YOUR BUSINESS")
                else:
                    st.markdown(f"**#{rank} {name}**")
                
                if address:
                    st.markdown(f"   📍 {address}")
                if reason_tokens:
                    st.markdown(f"   🏷️ {', '.join(reason_tokens)}")
                st.markdown("---")
        else:
            st.warning("No ranked results returned from LLM")
    
    with tab2:
        st.json(result)
    
    # Context passed to Agent 2
    st.markdown("---")
    st.markdown("### 📤 Context passed to Agent 2:")
    with st.expander("See context", expanded=False):
        context = {
            "query": result.get("query", ""),
            "inferred_location": inferred_location,
            "business_in_results": business_in_results,
            "business_rank": business_rank,
            "ranked_results": [{"rank": r.get("rank"), "name": r.get("name")} for r in ranked_results[:5]]
        }
        st.json(context)
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Query"):
            st.session_state.current_step = 1
            st.session_state.agent1_output = None
            st.rerun()
    with col2:
        if st.button("📋 Run Agent 2: Plan Actions →", type="primary"):
            st.session_state.current_step = 3
            st.rerun()


def render_step3():
    """Step 3: Agent 2 Action Planning."""
    st.markdown("## Step 3: Agent 2 - Action Planning")
    
    # Show input from Agent 1 (ranked results)
    with st.expander("📥 Input from Agent 1 (Ranked Results)", expanded=True):
        ranked_results = st.session_state.agent1_output.get("ranked_results", [])
        inferred_location = st.session_state.agent1_output.get("inferred_location", "Unknown")
        st.markdown(f"**Location:** {inferred_location}")
        st.markdown(f"**{len(ranked_results)} ranked results:**")
        for r in ranked_results[:10]:
            rank = r.get("rank", "?")
            name = r.get("name", "Unknown")
            st.markdown(f"{rank}. **{name}**")
    
    # Run Agent 2 if needed
    if st.session_state.agent2_output is None:
        with st.spinner("🤖 Agent 2 is analyzing ranking and planning actions..."):
            try:
                # Pass LLM client to Agent 2 so it can analyze the ranking
                from utils.llm_client import LLMClient
                llm_client = None
                if os.getenv("OPENAI_API_KEY"):
                    llm_client = LLMClient(provider="openai")
                elif os.getenv("ANTHROPIC_API_KEY"):
                    llm_client = LLMClient(provider="anthropic")
                
                agent2 = Agent2ActionPlanning(llm_client=llm_client)
                result = agent2.plan_actions(st.session_state.agent1_output, DEFAULT_PROFILE)
                st.session_state.agent2_output = result.dict()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())
                return
    
    # Display results
    result = st.session_state.agent2_output
    st.success("✅ Agent 2 Complete!")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Actions", result.get("total_actions", 0))
    with col2:
        st.metric("⚡ Automated", result.get("automated_count", 0))
    with col3:
        st.metric("✋ Manual", result.get("manual_count", 0))
    
    # Display actions
    actions = result.get("actions", [])
    
    tab1, tab2, tab3 = st.tabs(["⚡ Automated", "✋ Manual", "📊 Full Output"])
    
    with tab1:
        automated = [a for a in actions if a.get("automation_level") == "fully_automated"]
        if automated:
            for action in automated:
                st.markdown(f"🤖 **{action.get('title', 'Unknown')}**")
                st.markdown(f"> {action.get('description', '')[:150]}")
                st.markdown(f"Priority: {action.get('priority', 'medium').upper()}")
                st.markdown("---")
        else:
            st.info("No automated actions")
    
    with tab2:
        manual = [a for a in actions if a.get("automation_level") == "manual"]
        if manual:
            for action in manual:
                st.markdown(f"✋ **{action.get('title', 'Unknown')}**")
                st.markdown(f"> {action.get('description', '')[:150]}")
                st.markdown(f"Time: {action.get('time_required', 'N/A')}")
                st.markdown("---")
        else:
            st.info("No manual actions")
    
    with tab3:
        st.json(result)
    
    # Context passed to Agent 3
    st.markdown("---")
    st.markdown("### 📤 Context passed to Agent 3:")
    with st.expander("See context", expanded=False):
        context = {
            "actions_to_execute": [
                {"title": a.get("title"), "type": a.get("action_type"), "automation": a.get("automation_level")}
                for a in actions
            ]
        }
        st.json(context)
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Agent 1"):
            st.session_state.current_step = 2
            st.session_state.agent2_output = None
            st.rerun()
    with col2:
        if st.button("⚙️ Run Agent 3: Execute →", type="primary"):
            st.session_state.current_step = 4
            st.rerun()


def render_step4():
    """Step 4: Agent 3 Execution."""
    st.markdown("## Step 4: Agent 3 - Execution")
    
    # Show input from Agent 2
    with st.expander("📥 Input from Agent 2", expanded=True):
        actions = st.session_state.agent2_output.get("actions", [])
        st.markdown(f"**{len(actions)} actions to execute:**")
        for a in actions[:5]:
            auto = "⚡" if a.get("automation_level") == "fully_automated" else "✋"
            st.markdown(f"- {auto} {a.get('title', 'Unknown')}")
    
    # Run Agent 3 if needed
    if st.session_state.agent3_output is None:
        with st.spinner("🤖 Agent 3 is executing actions..."):
            try:
                agent3 = Agent3Execution()
                action_plan = ActionPlan(**st.session_state.agent2_output)
                result = agent3.execute_actions(action_plan, DEFAULT_PROFILE)
                st.session_state.agent3_output = result
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())
                return
    
    # Display results
    result = st.session_state.agent3_output
    st.success("✅ Agent 3 Complete! All agents finished.")
    
    # Metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅ Completed", result.get("completed_count", 0))
    with col2:
        st.metric("❌ Failed", result.get("failed_count", 0))
    
    # Generated Materials
    st.markdown("### 📄 Generated Materials")
    
    materials = result.get("generated_materials", {})
    if materials:
        for action_id, material in materials.items():
            mat_type = material.get("type", "unknown").replace("_", " ").title()
            with st.expander(f"📝 {mat_type}", expanded=True):
                st.markdown(f"**Usage:** {material.get('usage', 'N/A')}")
                content = material.get("content")
                if isinstance(content, str):
                    st.code(content[:2000], language="text")
                elif isinstance(content, list):
                    for item in content[:10]:
                        if isinstance(item, dict):
                            st.markdown(f"- **{item.get('name')}**: {item.get('url')} ({item.get('priority')})")
                        else:
                            st.markdown(f"- {item}")
                elif isinstance(content, dict):
                    st.json(content)
    else:
        st.info("No materials generated")
    
    # Full output
    with st.expander("📊 Full Agent 3 Output", expanded=False):
        st.json(result)
    
    # Summary
    st.markdown("---")
    st.markdown("## 🎉 Complete Flow Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Agent 1")
        st.markdown(f"✅ Found {len(st.session_state.agent1_output.get('issues', []))} issues")
    with col2:
        st.markdown("### Agent 2")
        st.markdown(f"✅ Created {st.session_state.agent2_output.get('total_actions', 0)} actions")
    with col3:
        st.markdown("### Agent 3")
        st.markdown(f"✅ Generated {len(materials)} materials")
    
    # Download report
    st.markdown("---")
    full_report = {
        "query": st.session_state.query,
        "timestamp": datetime.now().isoformat(),
        "agent1_analysis": st.session_state.agent1_output,
        "agent2_action_plan": st.session_state.agent2_output,
        "agent3_execution": st.session_state.agent3_output
    }
    
    st.download_button(
        "📥 Download Full Report (JSON)",
        data=json.dumps(full_report, indent=2, default=str),
        file_name=f"visibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True
    )
    
    if st.button("🔄 Start New Query", type="primary", use_container_width=True):
        reset_all()
        st.rerun()


if __name__ == "__main__":
    main()
