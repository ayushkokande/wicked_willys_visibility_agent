"""Streamlit UI for Wicked Willy's Visibility Agent - Step-by-Step Flow."""

import streamlit as st
import os
import json
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="Wicked Willy's Visibility Agent",
    page_icon="🍺",
    layout="wide"
)

# Now import the rest after page config
from core.business_profile import WICKED_WILLYS_PROFILE
from agents.agent2_action_planning import Agent2ActionPlanning
from agents.agent3_execution import Agent3Execution
from core.allowed_actions import ActionPlan

STEPS = ["Query", "Agent 1", "Agent 2", "Agent 3"]
TOTAL_STEPS = len(STEPS)

APP_STYLES = """
<style>
.app-hero {
    background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.2rem;
    color: #f9fafb;
}
.app-hero h1 {
    margin-bottom: 0.25rem;
}
.app-hero p {
    margin: 0;
    color: #e5e7eb;
}
.app-chip {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.25);
    margin-right: 0.35rem;
    margin-top: 0.35rem;
    font-size: 0.75rem;
}
.status-chip {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    background: #eef2ff;
    color: #3730a3;
    margin-right: 0.35rem;
}
</style>
"""


def init_session():
    """Initialize session state."""
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    if 'query' not in st.session_state:
        st.session_state.query = ""
    if "query_input" not in st.session_state:
        st.session_state.query_input = st.session_state.query
    if 'agent1_output' not in st.session_state:
        st.session_state.agent1_output = None
    if 'agent2_output' not in st.session_state:
        st.session_state.agent2_output = None
    if 'agent3_output' not in st.session_state:
        st.session_state.agent3_output = None
    if 'use_llm' not in st.session_state:
        st.session_state.use_llm = True
    if "agent1_mode" not in st.session_state:
        st.session_state.agent1_mode = "mock"
    if "agent2_mode" not in st.session_state:
        st.session_state.agent2_mode = "mock"
    if "llm_provider" not in st.session_state:
        st.session_state.llm_provider = "openai"


def apply_custom_styles():
    """Apply custom CSS styling."""
    st.markdown(APP_STYLES, unsafe_allow_html=True)


def get_available_llm_providers():
    """Return available LLM providers based on env vars."""
    providers = []
    if os.getenv("OPENAI_API_KEY"):
        providers.append("openai")
    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append("anthropic")
    return providers


def resolve_llm_provider(preferred_provider: Optional[str]) -> Optional[str]:
    """Resolve preferred provider against available providers."""
    providers = get_available_llm_providers()
    if not providers:
        return None
    if preferred_provider in providers:
        return preferred_provider
    return providers[0]


def get_agent1(use_llm: bool, preferred_provider: Optional[str]):
    """Get Agent 1 based on mode."""
    if use_llm:
        try:
            from utils.llm_client import LLMClient
            from agents.agent1_analysis_llm import Agent1AnalysisLLM

            provider = resolve_llm_provider(preferred_provider)
            if provider == "openai":
                client = LLMClient(provider="openai")
                return Agent1AnalysisLLM(llm_client=client), "openai"
            if provider == "anthropic":
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
    st.session_state.query_input = ""
    st.session_state.agent1_output = None
    st.session_state.agent2_output = None
    st.session_state.agent3_output = None
    st.session_state.agent1_mode = "mock"
    st.session_state.agent2_mode = "mock"


def set_query_text(value: str):
    """Set query text in session state."""
    clean_value = (value or "").strip()
    st.session_state.query_input = clean_value
    st.session_state.query = clean_value


def normalize_enum_value(value: Optional[str]) -> str:
    """Normalize enum-like values to lowercase strings."""
    if value is None:
        return ""
    text = str(value).lower()
    if "." in text:
        text = text.split(".")[-1]
    return text


def main():
    """Main app."""
    init_session()
    apply_custom_styles()

    # Header
    st.markdown(
        """
        <div class="app-hero">
            <h1>🍺 Wicked Willy's Visibility Agent</h1>
            <p><strong>Three-Agent System for Business Discoverability</strong></p>
            <div>
                <span class="app-chip">Local Search Diagnostics</span>
                <span class="app-chip">Action Planning</span>
                <span class="app-chip">Automated Execution</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    step_progress = (st.session_state.current_step - 1) / (TOTAL_STEPS - 1)
    st.progress(step_progress)
    st.caption(
        f"Step {st.session_state.current_step} of {TOTAL_STEPS}: "
        f"{STEPS[st.session_state.current_step - 1]}"
    )
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # API Key status
        has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        providers = get_available_llm_providers()
        
        st.markdown("**API Keys:**")
        st.markdown(f"- Anthropic: {'✅' if has_anthropic else '❌'}")
        st.markdown(f"- OpenAI: {'✅' if has_openai else '❌'}")
        
        if providers and st.session_state.llm_provider not in providers:
            st.session_state.llm_provider = providers[0]

        st.session_state.use_llm = st.checkbox(
            "Use LLM (Claude/GPT)", 
            value=st.session_state.use_llm,
            disabled=not providers
        )

        if providers:
            st.session_state.llm_provider = st.selectbox(
                "Preferred LLM Provider",
                options=providers,
                index=providers.index(st.session_state.llm_provider),
                disabled=not st.session_state.use_llm,
            )
        else:
            st.info("Add OPENAI_API_KEY or ANTHROPIC_API_KEY to enable LLM mode.")
        
        st.markdown("---")
        st.markdown("## 📍 Business Profile")
        st.markdown(f"**{WICKED_WILLYS_PROFILE.name}**")
        st.markdown(f"📍 {WICKED_WILLYS_PROFILE.address}")
        st.markdown(f"🏷️ {WICKED_WILLYS_PROFILE.primary_category}")
        
        st.markdown("---")
        
        # Progress
        st.markdown("## 📊 Progress")
        for i, step in enumerate(STEPS, 1):
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
    
    st.markdown("Ask about your business visibility and local ranking.")

    col_main, col_side = st.columns([2, 1], gap="large")

    with col_main:
        query = st.text_area(
            "Your question:",
            placeholder="Why don't I show up when people search for 'bar near Bleecker Street'?",
            height=110,
            key="query_input"
        )
        st.session_state.query = query
        st.caption("Tip: include a neighborhood, landmark, or intent keyword.")

    with col_side:
        st.markdown("### Flow Overview")
        st.markdown("1. **Agent 1:** Finds likely search results")
        st.markdown("2. **Agent 2:** Explains gaps + action plan")
        st.markdown("3. **Agent 3:** Executes or generates assets")
        if st.session_state.use_llm:
            st.markdown('<span class="status-chip">LLM Mode Enabled</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-chip">Mock Mode</span>', unsafe_allow_html=True)
    
    st.markdown("**Quick examples:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Bar near Bleecker Street", use_container_width=True):
            set_query_text("Why don't I show up when people search for 'bar near Bleecker Street'?")
            st.rerun()
    with col2:
        if st.button("Improve local ranking", use_container_width=True):
            set_query_text("How can I improve my local search ranking?")
            st.rerun()
    with col3:
        if st.button("Get more reviews", use_container_width=True):
            set_query_text("How do I get more reviews for my business?")
            st.rerun()
    
    st.markdown("---")
    
    if st.button("🔍 Run Agent 1: Analyze →", type="primary", disabled=not st.session_state.query):
        set_query_text(st.session_state.query)
        st.session_state.current_step = 2
        st.rerun()


def render_step2():
    """Step 2: Agent 1 Analysis."""
    st.markdown("## Step 2: Agent 1 - Discovery & Analysis")
    
    # Show input
    with st.expander("📥 Input to Agent 1", expanded=True):
        st.markdown(f"**Query:** {st.session_state.query}")
        st.markdown(f"**Business:** {WICKED_WILLYS_PROFILE.name}")
    
    # Run Agent 1 if needed
    if st.session_state.agent1_output is None:
        with st.spinner("🤖 Agent 1 is analyzing..."):
            try:
                agent1, mode = get_agent1(st.session_state.use_llm, st.session_state.llm_provider)
                st.session_state.agent1_mode = mode
                st.info(f"Using: {mode.upper()} mode")
                result = agent1.analyze(st.session_state.query, WICKED_WILLYS_PROFILE)
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
    st.markdown(f"**Mode:** {st.session_state.agent1_mode.upper()}")
    
    # Get ranked results
    ranked_results = result.get("ranked_results", [])
    inferred_location = result.get("inferred_location") or "Unknown"
    summary = result.get("summary")
    notes = result.get("notes")
    
    # Check if Wicked Willy's is in the results
    wicked_in_results = any("wicked" in r.get("name", "").lower() for r in ranked_results)
    wicked_rank = next((r.get("rank") for r in ranked_results if "wicked" in r.get("name", "").lower()), None)
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Results Ranked", len(ranked_results))
    with col2:
        st.metric("Location", inferred_location[:20] + "..." if len(inferred_location) > 20 else inferred_location)
    with col3:
        if wicked_in_results and wicked_rank:
            st.metric("Wicked Willy's Rank", f"#{wicked_rank}")
        elif wicked_in_results:
            st.metric("Wicked Willy's Rank", "Found")
        else:
            st.metric("Wicked Willy's Rank", "❌ Not Found")
    
    # Tabs for results
    tab1, tab2, tab3 = st.tabs(["📊 Ranked Results", "🧾 Table View", "📋 Full Output"])
    
    with tab1:
        if ranked_results:
            if summary:
                with st.expander("Summary", expanded=False):
                    st.markdown(summary)
            for r in ranked_results:
                rank = r.get("rank", "?")
                name = r.get("name", "Unknown")
                address = r.get("address", "")
                reason_tokens = r.get("reason_tokens", [])
                
                # Highlight Wicked Willy's
                if "wicked" in name.lower():
                    st.markdown(f"**#{rank} 🍺 {name}** ⬅️ YOUR BUSINESS")
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
        if ranked_results:
            table_rows = []
            for r in ranked_results:
                table_rows.append({
                    "Rank": r.get("rank", "?"),
                    "Business": r.get("name", "Unknown"),
                    "Address": r.get("address") or "—",
                    "Signals": ", ".join(r.get("reason_tokens", [])) or "—",
                })
            st.dataframe(table_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No results to display.")

        if notes:
            st.caption(f"Notes: {notes}")

    with tab3:
        st.json(result)
    
    # Context passed to Agent 2
    st.markdown("---")
    st.markdown("### 📤 Context passed to Agent 2:")
    with st.expander("See context", expanded=False):
        context = {
            "query": result.get("query", ""),
            "inferred_location": inferred_location,
            "wicked_in_results": wicked_in_results,
            "wicked_rank": wicked_rank,
            "ranked_results": [{"rank": r.get("rank"), "name": r.get("name")} for r in ranked_results[:5]]
        }
        st.json(context)
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Query"):
            st.session_state.current_step = 1
            st.session_state.agent1_output = None
            st.session_state.agent2_output = None
            st.session_state.agent3_output = None
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
                if st.session_state.use_llm:
                    provider = resolve_llm_provider(st.session_state.llm_provider)
                    if provider:
                        llm_client = LLMClient(provider=provider)
                        st.session_state.agent2_mode = provider
                    else:
                        st.session_state.agent2_mode = "mock"
                else:
                    st.session_state.agent2_mode = "mock"
                
                agent2 = Agent2ActionPlanning(llm_client=llm_client)
                result = agent2.plan_actions(st.session_state.agent1_output, WICKED_WILLYS_PROFILE)
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
    st.markdown(f"**Mode:** {st.session_state.agent2_mode.upper()}")
    
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

    # Agent 2 LLM report (if available)
    agent2_report = st.session_state.agent1_output.get("agent2_report")
    if agent2_report:
        with st.expander("🧠 Ranking Explanation & Evidence Plan", expanded=False):
            ranking_explanation = agent2_report.get("ranking_explanation", {})
            if ranking_explanation:
                st.markdown("**Global Reasons**")
                for reason in ranking_explanation.get("global_reasons", [])[:6]:
                    st.markdown(f"- {reason}")
            if agent2_report.get("evidence_plan"):
                st.markdown("**Evidence Plan**")
                for item in agent2_report.get("evidence_plan", [])[:6]:
                    bucket = item.get("bucket", "unknown")
                    query = item.get("query", "")
                    st.markdown(f"- {bucket.title()}: {query}")
            st.json(agent2_report)

    # Filters
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        priority_filter = st.multiselect(
            "Priority",
            options=["high", "medium", "low"],
            default=["high", "medium", "low"]
        )
    with filter_col2:
        automation_filter = st.multiselect(
            "Automation",
            options=["fully_automated", "partially_automated", "manual"],
            default=["fully_automated", "partially_automated", "manual"]
        )

    filtered_actions = []
    for action in actions:
        priority_value = normalize_enum_value(action.get("priority"))
        automation_value = normalize_enum_value(action.get("automation_level"))
        if priority_value in priority_filter and automation_value in automation_filter:
            filtered_actions.append(action)

    tab1, tab2, tab3, tab4 = st.tabs(["⚡ Automated", "🤝 Assisted", "✋ Manual", "📊 Full Output"])
    
    with tab1:
        automated = [a for a in filtered_actions if normalize_enum_value(a.get("automation_level")) == "fully_automated"]
        if automated:
            for action in automated:
                priority = normalize_enum_value(action.get("priority", "medium")).upper()
                st.markdown(f"🤖 **{action.get('title', 'Unknown')}**")
                st.markdown(f"> {action.get('description', '')}")
                st.markdown(f"Priority: {priority}")
                st.caption(action.get("estimated_impact", ""))
                st.markdown("---")
        else:
            st.info("No automated actions")
    
    with tab2:
        assisted = [a for a in filtered_actions if normalize_enum_value(a.get("automation_level")) == "partially_automated"]
        if assisted:
            for action in assisted:
                priority = normalize_enum_value(action.get("priority", "medium")).upper()
                st.markdown(f"🤝 **{action.get('title', 'Unknown')}**")
                st.markdown(f"> {action.get('description', '')}")
                st.markdown(f"Priority: {priority}")
                st.markdown(f"Time: {action.get('time_required', 'N/A')}")
                st.caption(action.get("estimated_impact", ""))
                st.markdown("---")
        else:
            st.info("No assisted actions")
    
    with tab3:
        manual = [a for a in filtered_actions if normalize_enum_value(a.get("automation_level")) == "manual"]
        if manual:
            for action in manual:
                priority = normalize_enum_value(action.get("priority", "medium")).upper()
                st.markdown(f"✋ **{action.get('title', 'Unknown')}**")
                st.markdown(f"> {action.get('description', '')}")
                st.markdown(f"Priority: {priority}")
                st.markdown(f"Time: {action.get('time_required', 'N/A')}")
                st.caption(action.get("estimated_impact", ""))
                st.markdown("---")
        else:
            st.info("No manual actions")

    with tab4:
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
            st.session_state.agent3_output = None
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
            automation = normalize_enum_value(a.get("automation_level"))
            if automation == "fully_automated":
                auto = "⚡"
            elif automation == "partially_automated":
                auto = "🤝"
            else:
                auto = "✋"
            st.markdown(f"- {auto} {a.get('title', 'Unknown')}")
    
    # Run Agent 3 if needed
    if st.session_state.agent3_output is None:
        with st.spinner("🤖 Agent 3 is executing actions..."):
            try:
                agent3 = Agent3Execution()
                action_plan = ActionPlan(**st.session_state.agent2_output)
                result = agent3.execute_actions(action_plan, WICKED_WILLYS_PROFILE)
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

    summary_text = result.get("summary")
    if summary_text:
        st.markdown("### ✅ Execution Summary")
        st.markdown(summary_text)

    manual_instructions = result.get("manual_instructions", [])
    if manual_instructions:
        st.markdown("### ✋ Manual Instructions")
        for instruction in manual_instructions[:10]:
            st.markdown(f"- {instruction}")
    
    # Generated Materials
    st.markdown("### 📄 Generated Materials")
    
    materials = result.get("generated_materials", {})
    if materials:
        for action_id, material in materials.items():
            material_type = material.get("type", "unknown")
            mat_type = material_type.replace("_", " ").title()
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
                if content is not None:
                    if isinstance(content, str):
                        download_data = content
                        file_ext = "txt"
                        mime_type = "text/plain"
                    else:
                        download_data = json.dumps(content, indent=2, default=str)
                        file_ext = "json"
                        mime_type = "application/json"
                    st.download_button(
                        "Download material",
                        data=download_data,
                        file_name=f"{material_type}_{action_id}.{file_ext}",
                        mime=mime_type,
                        use_container_width=True,
                        key=f"download_{action_id}"
                    )
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
