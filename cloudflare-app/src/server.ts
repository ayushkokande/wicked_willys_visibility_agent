import { createWorkersAI } from "workers-ai-provider";
import { routeAgentRequest } from "agents";
import { AIChatAgent, type OnChatMessageOptions } from "@cloudflare/ai-chat";
import {
  streamText,
  generateText,
  convertToModelMessages,
  pruneMessages,
  tool,
  stepCountIs
} from "ai";
import { z } from "zod";

// ── Types ────────────────────────────────────────────────────────────

interface BusinessProfile {
  name: string;
  address: string;
  phone?: string;
  website?: string;
  primaryCategory?: string;
  secondaryCategories?: string[];
  targetKeywords?: string[];
  reviewCount?: number;
  averageRating?: number;
}

interface AnalysisRecord {
  query: string;
  timestamp: string;
  rankedResults: number;
  businessFound: boolean;
  businessRank: number | null;
}

interface SEOAgentState {
  businessProfile: BusinessProfile | null;
  analysisHistory: AnalysisRecord[];
}

// ── System prompts ───────────────────────────────────────────────────

const MAIN_SYSTEM_PROMPT = `You are an expert Local SEO Visibility Optimization Agent. You help local businesses improve their visibility in local search results (Google Maps, Google Search, Yelp, etc.).

Your workflow follows a proven 3-step pipeline:

**Step 1 — Discovery & Analysis**
When a user asks about their search visibility, use the \`analyzeLocalSearch\` tool to simulate local search rankings and identify where their business stands vs competitors.

**Step 2 — Diagnosis & Planning**
Explain WHY the business ranks where it does using five local-search factors:
- Relevance — keyword alignment with the query
- Proximity — distance to the searcher's implied location
- Prominence — review count, citations, backlinks, domain authority
- Trust — rating quality, NAP consistency, verification status
- Freshness — recent reviews, updated content, active social presence

Group evidence into three buckets:
- **Brand** — official website and owned properties
- **Social** — UGC platforms (Instagram, Reddit, YouTube)
- **Earned** — independent media, review sites, directories

**Step 3 — Execution**
Generate actionable SEO materials using the available tools:
- Schema markup (JSON-LD) for structured data
- Meta tags for on-page SEO
- Citation/directory submission lists
- Content and review strategy recommendations

Important rules:
- Always start by checking if a business profile is saved. If not, ask the user for their business details before running analysis.
- Be specific and actionable — no generic advice.
- Explain technical concepts in plain language.
- When generating content, weave in the business's target keywords naturally.
- Use markdown formatting for clear, readable responses.
- After analysis, proactively suggest which tools to run next.`;

const ANALYSIS_PROMPT = `You are a local search ranking simulator. Given a search query and business context, generate realistic local search results that mirror what Google Maps / Google Local Pack would show.

Output ONLY valid JSON matching this structure (no markdown fences, no extra text):
{
  "query": "the search query",
  "location_context": "inferred searcher location",
  "ranked_results": [
    {
      "rank": 1,
      "name": "Business Name",
      "address": "Full address",
      "rating": 4.5,
      "review_count": 250,
      "distance_estimate": "0.2 mi",
      "relevance_signals": ["signal1", "signal2"],
      "why_ranked_here": "Brief explanation of ranking position"
    }
  ],
  "target_business_analysis": {
    "found_in_results": false,
    "rank": null,
    "issues": [
      {
        "factor": "prominence",
        "severity": "high",
        "description": "What the gap is",
        "recommendation": "What to do about it"
      }
    ],
    "strengths": [],
    "top_competitors": [
      { "name": "Competitor", "why_they_rank": "reason" }
    ]
  }
}

Rules:
- Generate 5–8 realistic results with real-sounding names appropriate for the location and category.
- Rankings must reflect realistic local-search factors (relevance, proximity, prominence, trust, freshness).
- The target business may or may not appear — be realistic based on the profile data.
- Every issue must include a concrete, actionable recommendation.`;

// ── Citation directory data ──────────────────────────────────────────

const CITATION_DIRECTORIES = [
  { name: "Google Business Profile", url: "https://business.google.com", priority: "critical", categories: ["all"] },
  { name: "Yelp for Business", url: "https://biz.yelp.com", priority: "critical", categories: ["all"] },
  { name: "Apple Business Connect", url: "https://businessconnect.apple.com", priority: "high", categories: ["all"] },
  { name: "Bing Places", url: "https://www.bingplaces.com", priority: "high", categories: ["all"] },
  { name: "Facebook Business", url: "https://www.facebook.com/business", priority: "high", categories: ["all"] },
  { name: "TripAdvisor for Business", url: "https://www.tripadvisor.com/Owners", priority: "high", categories: ["bar", "restaurant", "cafe", "hotel"] },
  { name: "Foursquare", url: "https://foursquare.com", priority: "medium", categories: ["all"] },
  { name: "YellowPages", url: "https://www.yellowpages.com", priority: "medium", categories: ["all"] },
  { name: "Better Business Bureau", url: "https://www.bbb.org", priority: "medium", categories: ["all"] },
  { name: "Zomato", url: "https://www.zomato.com", priority: "medium", categories: ["bar", "restaurant", "cafe"] },
  { name: "OpenTable", url: "https://restaurant.opentable.com", priority: "high", categories: ["restaurant"] },
  { name: "Untappd", url: "https://untappd.com", priority: "medium", categories: ["bar"] },
  { name: "BeerMenus", url: "https://www.beermenus.com", priority: "medium", categories: ["bar"] },
  { name: "Chamber of Commerce", url: "https://www.chamberofcommerce.com", priority: "medium", categories: ["all"] },
  { name: "Manta", url: "https://www.manta.com", priority: "low", categories: ["all"] },
  { name: "Nextdoor Business", url: "https://business.nextdoor.com", priority: "medium", categories: ["all"] },
];

// ── Agent ────────────────────────────────────────────────────────────

export class ChatAgent extends AIChatAgent<Env, SEOAgentState> {
  initialState: SEOAgentState = {
    businessProfile: null,
    analysisHistory: []
  };

  async onChatMessage(_onFinish: unknown, options?: OnChatMessageOptions) {
    const workersai = createWorkersAI({ binding: this.env.AI });
    const model = workersai("@cf/zai-org/glm-4.7-flash");

    const profile = this.state.businessProfile;
    const profileCtx = profile
      ? `\n\nSaved business profile:\n- Name: ${profile.name}\n- Address: ${profile.address}\n- Category: ${profile.primaryCategory ?? "Not set"}\n- Keywords: ${(profile.targetKeywords ?? []).join(", ") || "None"}\n- Website: ${profile.website ?? "Not set"}\n- Phone: ${profile.phone ?? "Not set"}\n- Reviews: ${profile.reviewCount ?? "Unknown"} (avg ${profile.averageRating ?? "?"}★)`
      : "\n\nNo business profile saved yet. Ask the user for their business details before running any analysis.";

    const historyCtx =
      this.state.analysisHistory.length > 0
        ? `\n\nRecent analyses (${this.state.analysisHistory.length}):\n` +
          this.state.analysisHistory
            .slice(-3)
            .map(
              (h) =>
                `• "${h.query}" — ${h.businessFound ? `Ranked #${h.businessRank}` : "Not found"} (${h.rankedResults} results, ${h.timestamp})`
            )
            .join("\n")
        : "";

    const result = streamText({
      model,
      system: MAIN_SYSTEM_PROMPT + profileCtx + historyCtx,
      messages: pruneMessages({
        messages: await convertToModelMessages(this.messages),
        toolCalls: "before-last-2-messages"
      }),
      tools: {
        // ── Save / retrieve business profile (state persistence) ───
        saveBusinessProfile: tool({
          description:
            "Save or update the user's business profile. Call this when the user provides business details like name, address, category, keywords, etc.",
          inputSchema: z.object({
            name: z.string().describe("Business name"),
            address: z.string().describe("Full street address including city, state, zip"),
            phone: z.string().optional().describe("Phone number"),
            website: z.string().optional().describe("Website URL"),
            primaryCategory: z
              .string()
              .optional()
              .describe("Primary category (e.g. Bar, Restaurant, Cafe)"),
            secondaryCategories: z
              .array(z.string())
              .optional()
              .describe("Additional categories"),
            targetKeywords: z
              .array(z.string())
              .optional()
              .describe("Target search keywords the business wants to rank for"),
            reviewCount: z.number().optional().describe("Current review count"),
            averageRating: z.number().optional().describe("Average star rating 1–5")
          }),
          execute: async (data) => {
            this.setState({ ...this.state, businessProfile: data });
            return {
              saved: true,
              summary: `Profile saved for "${data.name}" at ${data.address}`
            };
          }
        }),

        getBusinessProfile: tool({
          description: "Retrieve the currently saved business profile",
          inputSchema: z.object({}),
          execute: async () => {
            return this.state.businessProfile ?? { error: "No profile saved yet." };
          }
        }),

        // ── Local search analysis (Agent 1 + 2 pipeline) ────────────
        analyzeLocalSearch: tool({
          description:
            "Run a multi-step AI analysis pipeline: simulate local search rankings for a query and diagnose visibility gaps. Requires a saved business profile. This calls an internal LLM to generate realistic search results.",
          inputSchema: z.object({
            query: z
              .string()
              .describe(
                "The search query to analyze, e.g. 'best bars near Bleecker Street'"
              )
          }),
          needsApproval: async () => true,
          execute: async ({ query }) => {
            const bp = this.state.businessProfile;
            if (!bp) {
              return { error: "Save a business profile first." };
            }

            const userPrompt = [
              `Search query: "${query}"`,
              "",
              "Target business:",
              `- Name: ${bp.name}`,
              `- Address: ${bp.address}`,
              `- Category: ${bp.primaryCategory ?? "Local Business"}`,
              `- Keywords: ${(bp.targetKeywords ?? []).join(", ") || "none"}`,
              `- Reviews: ${bp.reviewCount ?? "unknown"}`,
              `- Rating: ${bp.averageRating ?? "unknown"}`,
              `- Website: ${bp.website ?? "none"}`,
              "",
              "Generate realistic local search results and a full diagnosis."
            ].join("\n");

            try {
              const { text } = await generateText({
                model,
                system: ANALYSIS_PROMPT,
                prompt: userPrompt
              });

              let analysis: Record<string, unknown>;
              try {
                const match = text.match(/\{[\s\S]*\}/);
                analysis = match ? JSON.parse(match[0]) : { raw_response: text };
              } catch {
                analysis = { raw_response: text };
              }

              const tba = analysis.target_business_analysis as
                | Record<string, unknown>
                | undefined;
              const found = (tba?.found_in_results as boolean) ?? false;
              const rank = (tba?.rank as number) ?? null;

              this.setState({
                ...this.state,
                analysisHistory: [
                  ...this.state.analysisHistory,
                  {
                    query,
                    timestamp: new Date().toISOString(),
                    rankedResults:
                      (analysis.ranked_results as unknown[])?.length ?? 0,
                    businessFound: found,
                    businessRank: rank
                  }
                ]
              });

              return analysis;
            } catch (err) {
              return { error: `Analysis failed: ${err}` };
            }
          }
        }),

        // ── Content generation tools (Agent 3 pipeline) ─────────────

        generateSchemaMarkup: tool({
          description:
            "Generate JSON-LD structured data (Schema.org) for the business website. Improves rich snippet eligibility in search results.",
          inputSchema: z.object({
            schemaType: z
              .enum([
                "BarOrPub",
                "Restaurant",
                "LocalBusiness",
                "FoodEstablishment",
                "CafeOrCoffeeShop"
              ])
              .describe("Schema.org type for the business"),
            openingHours: z
              .string()
              .optional()
              .describe("Opening hours, e.g. 'Mo-Su 11:00-02:00'"),
            priceRange: z
              .string()
              .optional()
              .describe("Price range, e.g. '$$'"),
            cuisineType: z
              .string()
              .optional()
              .describe("Cuisine type if applicable")
          }),
          execute: async ({ schemaType, openingHours, priceRange, cuisineType }) => {
            const bp = this.state.businessProfile;
            if (!bp) return { error: "No business profile saved." };

            const parts = bp.address.split(",").map((s) => s.trim());
            const schema: Record<string, unknown> = {
              "@context": "https://schema.org",
              "@type": schemaType,
              name: bp.name,
              address: {
                "@type": "PostalAddress",
                streetAddress: parts[0] || bp.address,
                addressLocality: parts[1] || "",
                addressRegion: parts[2]?.replace(/\d+/g, "").trim() || "",
                postalCode: parts[2]?.match(/\d+/)?.[0] || "",
                addressCountry: "US"
              }
            };
            if (bp.phone) schema.telephone = bp.phone;
            if (bp.website) schema.url = bp.website;
            if (openingHours) schema.openingHours = openingHours;
            if (priceRange) schema.priceRange = priceRange;
            if (cuisineType) schema.servesCuisine = cuisineType;
            if (bp.reviewCount && bp.averageRating) {
              schema.aggregateRating = {
                "@type": "AggregateRating",
                ratingValue: String(bp.averageRating),
                reviewCount: String(bp.reviewCount)
              };
            }

            return {
              markup: `<script type="application/ld+json">\n${JSON.stringify(schema, null, 2)}\n</script>`,
              usage:
                "Add this <script> tag inside the <head> of your website. It helps Google understand your business and enables rich snippets."
            };
          }
        }),

        generateMetaTags: tool({
          description:
            "Generate SEO meta tags (title, description, Open Graph, geo) for a page on the business website.",
          inputSchema: z.object({
            pageType: z
              .enum(["homepage", "about", "menu", "contact", "events"])
              .describe("Which page the meta tags are for")
          }),
          execute: async ({ pageType }) => {
            const bp = this.state.businessProfile;
            if (!bp) return { error: "No business profile saved." };

            const kw = (bp.targetKeywords ?? []).join(", ");
            const cat = bp.primaryCategory ?? "local business";
            const locality = bp.address.split(",")[1]?.trim() ?? "the area";
            const desc = `${bp.name} — your premier ${cat} at ${bp.address}. ${kw ? `Discover us for ${(bp.targetKeywords ?? []).slice(0, 3).join(", ")}.` : ""}`;

            const titles: Record<string, string> = {
              homepage: `${bp.name} | Best ${cat} in ${locality}`,
              about: `About ${bp.name} | ${locality} ${cat}`,
              menu: `Menu | ${bp.name}`,
              contact: `Contact ${bp.name} | Directions & Hours`,
              events: `Events at ${bp.name} | ${locality}`
            };

            const tags = [
              `<title>${titles[pageType]}</title>`,
              `<meta name="description" content="${desc}">`,
              kw && `<meta name="keywords" content="${kw}">`,
              `<meta property="og:title" content="${titles[pageType]}">`,
              `<meta property="og:description" content="${desc}">`,
              `<meta property="og:type" content="business.business">`,
              bp.website && `<meta property="og:url" content="${bp.website}">`,
              `<meta name="geo.placename" content="${bp.name}">`,
              `<meta name="robots" content="index, follow">`
            ]
              .filter(Boolean)
              .join("\n");

            return { tags, usage: `Add these to the <head> of your ${pageType} page.` };
          }
        }),

        generateCitationList: tool({
          description:
            "Generate a prioritized list of directories and citation sites where the business should be listed, with NAP consistency guidance.",
          inputSchema: z.object({
            category: z
              .enum(["bar", "restaurant", "cafe", "retail", "service", "general"])
              .describe("Business category for targeted directory recommendations")
          }),
          execute: async ({ category }) => {
            const bp = this.state.businessProfile;
            if (!bp) return { error: "No business profile saved." };

            const relevant = CITATION_DIRECTORIES.filter(
              (d) => d.categories.includes("all") || d.categories.includes(category)
            ).map(({ categories: _c, ...rest }) => rest);

            return {
              directories: relevant,
              total: relevant.length,
              nap_guidance: {
                name: bp.name,
                address: bp.address,
                phone: bp.phone ?? "[ADD PHONE NUMBER]",
                website: bp.website ?? "[ADD WEBSITE]",
                rule: "Your Name, Address, and Phone (NAP) must be IDENTICAL across every listing. Even small differences (St vs Street, Suite vs Ste) hurt local SEO."
              }
            };
          }
        }),

        // ── Client-side tool: browser provides the result ────────────
        getUserLocation: tool({
          description:
            "Get the user's approximate location from their browser. Useful for location-aware search analysis.",
          inputSchema: z.object({})
        })
      },
      stopWhen: stepCountIs(5),
      abortSignal: options?.abortSignal
    });

    return result.toUIMessageStreamResponse();
  }
}

// ── Worker entrypoint ────────────────────────────────────────────────

export default {
  async fetch(request: Request, env: Env) {
    return (
      (await routeAgentRequest(request, env)) ||
      new Response("Not found", { status: 404 })
    );
  }
} satisfies ExportedHandler<Env>;
