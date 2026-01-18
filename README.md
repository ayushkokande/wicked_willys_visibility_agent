# Wicked Willy's Visibility Optimization System

A multi-agent system that solves business discoverability problems by analyzing competitors, identifying SEO issues, planning actionable improvements, and executing optimizations.

## System Architecture

### Three-Agent Flow

```
Business Query 
    ↓
Agent 1: Analysis (Discovery & Diagnosis)
    ↓
Agent 2: Action Planning (Allowed Actions)
    ↓
Agent 3: Execution (Automated Actions)
    ↓
Results & Generated Materials
```

## Agents Overview

### Agent 1: Discovery & Analysis Agent
**Purpose:** Analyzes why a business isn't ranking well

**What it does:**
- Finds competing businesses for given queries
- Analyzes ranking factors (reviews, GMB, citations, SEO)
- Diagnoses specific issues (missing GMB, low reviews, etc.)
- Identifies SEO gaps and opportunities

**Output:** Comprehensive analysis with ranked competitors, identified issues, and opportunities

### Agent 2: Action Planning Agent
**Purpose:** Determines allowed actions based on analysis

**What it does:**
- Reviews Agent 1's findings
- Maps issues to specific actionable items
- Categorizes actions by automation level (automated/manual)
- Prioritizes actions by impact and urgency

**Output:** Action plan with prioritized list of allowed actions

### Agent 3: Execution Agent
**Purpose:** Executes allowed actions automatically

**What it does:**
- Executes fully automated actions (content generation, schema markup, etc.)
- Generates materials for manual actions (GMB descriptions, citation lists)
- Creates instructions for actions requiring human intervention
- Tracks execution status

**Output:** Execution report with completed actions and generated materials

## Allowed Actions

### Fully Automated (Agent 3 executes directly):
- ✅ Generate GMB descriptions
- ✅ Create schema markup (JSON-LD)
- ✅ Generate meta tags
- ✅ Create citation lists
- ✅ Generate blog posts
- ✅ Create review request templates
- ✅ Generate SEO reports

### Manual (Agent 3 provides guidance):
- 📝 Google My Business profile setup/updates
- 📝 Directory submissions
- 📝 Website structural changes
- 📝 Third-party service configuration

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Example

```python
from core.orchestrator import VisibilityOrchestrator
from core.business_profile import WICKED_WILLYS_PROFILE
from agents.agent1_analysis import Agent1Analysis
from agents.agent2_action_planning import Agent2ActionPlanning
from agents.agent3_execution import Agent3Execution

# Initialize
orchestrator = VisibilityOrchestrator(business_profile=WICKED_WILLYS_PROFILE)
agent1 = Agent1Analysis()
agent2 = Agent2ActionPlanning()
agent3 = Agent3Execution()

# Process query
query = "Why don't I show up when people search for 'bar near Bleecker Street'?"
results = orchestrator.process_query(query, agent1, agent2, agent3)

# Access results
analysis = results["agent1_analysis"]
action_plan = results["agent2_action_plan"]
execution = results["agent3_execution"]
```

### Run Example

```bash
python main.py
```

## Project Structure

```
wicked_willys_visibility_agent/
├── agents/
│   ├── agent1_analysis.py      # Discovery & Analysis Agent
│   ├── agent2_action_planning.py  # Action Planning Agent
│   └── agent3_execution.py     # Execution Agent
├── core/
│   ├── orchestrator.py         # Main flow controller
│   ├── business_profile.py     # Business data model
│   └── allowed_actions.py      # Action definitions
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

## Business Profile

The system is configured for **Wicked Willy's** at 149 Bleecker Street, but can be adapted for any business.

Default profile includes:
- Business name and address
- Target keywords
- Categories (Bar, Restaurant, Nightlife)
- SEO metrics (to be populated)

## Example Query Flow

**Query:** "Why don't I show up when people search for 'bar near Bleecker Street'?"

**Agent 1 Response:**
- Found 3 competing bars
- Top competitor: Greenwich Village Tavern (456 reviews, 4.7 rating)
- Issues identified:
  - Missing Google My Business profile (critical)
  - Low review count (high)
  - Suboptimal keyword usage (medium)

**Agent 2 Response:**
- Action plan with 5 actions:
  1. Generate optimized GMB description (automated, high priority)
  2. Set up GMB profile (manual, high priority)
  3. Create citation list (automated, medium priority)
  4. Generate keyword-optimized content (automated, medium priority)
  5. Review generation strategy (partially automated, high priority)

**Agent 3 Response:**
- Completed: Generated GMB description, citation list, content
- Manual instructions: GMB setup steps, citation submission process

## Customization

### Adding New Actions

1. Define action type in `core/allowed_actions.py`:
```python
class ActionType(str, Enum):
    YOUR_NEW_ACTION = "your_new_action"
```

2. Implement execution in `agents/agent3_execution.py`:
```python
def _execute_automated_action(self, action, business_profile):
    if action.action_type == ActionType.YOUR_NEW_ACTION:
        # Your implementation
        pass
```

3. Map in `agents/agent2_action_planning.py`:
```python
def _map_issue_to_actions(self, issue, ...):
    # Map issues to your new action type
    pass
```

### Integrating Real APIs

Replace mock data in Agent 1 with:
- Google Places API for competitor discovery
- Google My Business API for profile management
- Yelp API for competitor analysis
- SEO tools APIs (Moz, Ahrefs) for metrics

## Next Steps

1. **Integrate LLM APIs:** Connect OpenAI/Anthropic for enhanced analysis
2. **Add Real Data Sources:** Google Places, Yelp, SEO tools
3. **Build UI:** Web interface for business owners
4. **Action Tracking:** Database to track action completion over time
5. **Iterative Improvements:** Track changes and measure impact

## License

This project is designed for educational and demonstration purposes.


##
cd /Users/samprasmanueldsouza/Desktop/wicked_willys_visibility_agent/wicked_willys_visibility_agent
source venv/bin/activate
streamlit run app_interactive.py