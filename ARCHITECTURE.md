# Business Visibility Optimization System - Architecture

## Overview

This system uses a multi-agent architecture to solve business discoverability problems. The system helps local businesses improve their online visibility by analyzing competitors, understanding ranking issues, determining actionable steps, and executing improvements.

## System Flow

```
Business Query → Agent 1 (Analysis) → Agent 2 (Action Planning) → Agent 3 (Execution) → Feedback Loop
```

## Three-Agent Architecture

### Agent 1: Discovery & Analysis Agent
**Purpose:** Analyzes competitors and identifies ranking/SEO issues

**Responsibilities:**
- Receive business query (e.g., "restaurants near me", "best bar downtown")
- Search for businesses matching query requirements
- Analyze ranking factors (SEO, reviews, listings, social presence)
- Diagnose why the target business is not ranking well
- Generate detailed analysis report with rankings and reasons

**Capabilities:**
- Web search and discovery
- SEO analysis (on-page, off-page, technical)
- Competitor analysis
- Local SEO factors (Google My Business, Yelp, etc.)
- Review sentiment analysis
- Social media presence analysis

**Output:** Structured analysis with:
- Ranked list of competing businesses
- Ranking explanation for each
- Specific issues identified for the target business
- SEO gap analysis
- Missing opportunities

### Agent 2: Action Planning Agent
**Purpose:** Determines allowed actions based on analysis

**Responsibilities:**
- Review Agent 1's analysis
- Identify actionable items from findings
- Categorize actions by type and priority
- Check action feasibility and permissions
- Generate action plan with allowed operations

**Capabilities:**
- Action classification (technical SEO, content, listings, social)
- Priority scoring (high/medium/low impact, difficulty)
- Permission checking (what can be automated vs. manual)
- Resource requirement analysis

**Output:** Action plan with:
- List of allowed actions
- Priority ranking
- Estimated impact
- Required resources
- Dependencies

### Agent 3: Action Execution Agent
**Purpose:** Executes allowed actions on behalf of the business

**Responsibilities:**
- Take approved action plan from Agent 2
- Execute automated actions (within allowed scope)
- Generate content/suggestions for manual actions
- Track execution status
- Report results back

**Capabilities:**
- Automated technical fixes (meta tags, schema markup)
- Content generation (descriptions, blog posts)
- Listing updates (where APIs allow)
- Report generation for manual tasks
- Action tracking and verification

**Output:** Execution report with:
- Completed actions
- Generated content/materials
- Manual action instructions
- Verification status
- Next steps

## Allowed Actions (Scope)

### Automated Actions (Agent 3 can execute directly):
1. **Technical SEO:**
   - Generate/update meta tags
   - Create schema markup (JSON-LD)
   - Generate sitemaps
   - Fix technical issues (if website access granted)

2. **Content Generation:**
   - Write business descriptions
   - Create blog post drafts
   - Generate social media content
   - Write review response templates

3. **Structured Data:**
   - Generate LocalBusiness schema
   - Create review snippets markup
   - Event/food menu markup

4. **Reports & Documentation:**
   - Create optimization reports
   - Generate competitor analysis docs
   - Create action item checklists

### Manual Actions (Agent 3 provides guidance for):
1. **Platform Updates:**
   - Google My Business edits
   - Yelp profile updates
   - Social media posting
   - Directory submissions

2. **Third-party Services:**
   - Claiming listings
   - Review management
   - Paid advertising setup

3. **Website Changes:**
   - Structural changes (if no CMS access)
   - Server configuration
   - Certificate installation

## Technology Stack

- **Language:** Python 3.9+
- **LLM Framework:** OpenAI GPT-4 / Claude / Local models
- **Agent Orchestration:** LangChain / Custom orchestrator
- **Data Storage:** SQLite/PostgreSQL for query history
- **APIs:** Google Places, Yelp, social media APIs (where available)
- **Web Scraping:** BeautifulSoup, Selenium (for analysis)
- **Content Generation:** LLM APIs for content creation

## Data Flow

```
1. Business Query Input
   ↓
2. Agent 1: Analysis
   - Searches competitors
   - Analyzes the target business's current state
   - Generates diagnostic report
   ↓
3. Agent 2: Action Planning
   - Reviews analysis
   - Identifies allowed actions
   - Prioritizes actions
   - Creates action plan
   ↓
4. Agent 3: Execution
   - Executes automated actions
   - Generates materials for manual actions
   - Tracks completion
   ↓
5. Results Report
   - Summary of improvements
   - Status of actions
   - Recommendations for next iteration
```

## Implementation Structure

```
generative_seo/
├── agents/
│   ├── agent1_analysis.py      # Discovery & Analysis Agent
│   ├── agent2_action_planning.py  # Action Planning Agent
│   └── agent3_execution.py     # Execution Agent
├── core/
│   ├── orchestrator.py         # Main flow controller
│   ├── business_profile.py     # Business data model
│   └── allowed_actions.py      # Action definitions
├── services/
│   ├── search_service.py       # Business discovery
│   ├── seo_analyzer.py         # SEO analysis
│   ├── content_generator.py    # Content creation
│   └── listing_manager.py      # Listing management
├── utils/
│   ├── llm_client.py           # LLM wrapper
│   └── validators.py           # Input validation
└── main.py                     # Entry point
```

## Key Features

1. **Iterative Improvement:** Business can query multiple times, each iteration building on previous insights
2. **Transparency:** Each agent explains its reasoning
3. **Actionable Insights:** Focus on concrete, executable actions
4. **Safety:** Clear separation between automated and manual actions
5. **Context Awareness:** Agents maintain context across queries

## Example Query Flow

**Query:** "Why don't I show up when people search for 'bar near Main Street'?"

**Agent 1 Response:**
- Found 15 competing bars in the area
- Top 3 competitors: [list with reasons]
- Target business issues:
  - Missing Google My Business optimization
  - Weak keyword usage on website
  - No local citations
  - Limited review count

**Agent 2 Response:**
- Allowed actions:
  1. Generate optimized GMB description (automated)
  2. Create local citation list (automated)
  3. Generate blog post about "best <category> in <neighborhood>" (automated)
  4. Update GMB profile (manual - requires business verification)
  5. Submit to citation sites (manual - requires accounts)

**Agent 3 Response:**
- Completed:
  - Generated GMB description
  - Created citation list with 20 sites
  - Generated blog post draft
- Manual steps:
  - [Instructions for GMB update]
  - [Citation submission checklist]
