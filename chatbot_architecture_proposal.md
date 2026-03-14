# Chatbot Architecture & Strategy Proposal: satusatu.com

## 1. Platform Comparison & Evaluation

To build a chatbot that ingests the `sitemap.xml` and adheres to strict domain confinement and custom human-handoff UI, we must evaluate off-the-shelf SaaS solutions against a custom-built architecture.

| Feature Area | SaaS Platforms (Chatbase, Botpress, Voiceflow) | Custom Build (In-House AI Stack) |
| :--- | :--- | :--- |
| **Sitemap.xml Scraping & Sync** | **Excellent:** Chatbase and Botpress have native, easy-to-use website crawling and regular sync features out of the box. | **Moderate:** Requires setting up a custom web scraping pipeline (e.g., Scrapy, Crawlee) and scheduling cron jobs for continuous syncing. |
| **Strict Guardrails (Domain Confinement)** | **Poor to Moderate:** It is notoriously difficult to prevent SaaS "chat with your data" tools from occasionally hallucinating or responding to off-topic prompts (jailbreaks) because you lack control over the underlying retrieval and validation logic. | **Excellent (Crucial):** Complete control over the request lifecycle allows for pre-generation intent routing, strict system prompting, and post-generation validation checks to guarantee confinement. |
| **Custom UI & Handoff Buttons** | **Moderate:** While they support human handoff, tying it into custom, interactive UI elements (like specific Freshdesk/WhatsApp native buttons styling) within your domain can be clunky and restricted by their iFrame/widget constraints. | **Excellent:** You build the frontend widget (React/Vue/Svelte). You completely control how "handoff" payloads are rendered as interactive, brand-aligned buttons. |
| **Time-to-Market (MVP)** | **Fast:** Typically 1-2 weeks to prototype and deploy if requirements are flexible. | **Slower:** Typically 4-8 weeks to build the ingestion pipeline, APIs, and a production-ready frontend widget. |
| **Maintenance Overhead** | **Low:** Infrastructure is fully managed. | **High:** Requires managing cloud infrastructure, vector databases, API keys, and periodic prompt/retrieval tuning. |

### Recommendation
For satusatu.com, the **Custom Build** is strongly recommended. The "Strict Guardrails" requirement is the deciding factor. In an e-commerce/ticketing environment, suggesting non-existent products or answering off-topic queries creates immense brand risk and customer frustration that SaaS platforms cannot reliably mitigate. Furthermore, the requirement for a highly specific, graceful handoff UI necessitates a custom frontend.

---

## 2. MVP Architecture for "Custom Build"

If selecting the Custom Build route, here is the technical blueprint to engineer a highly reliable MVP.

### A. Recommended Modern AI Stack
*   **Backend Framework:** **FastAPI (Python)**. Python is the dominant language for AI/Data pipelines, and FastAPI is performant and excellent for streaming LLM responses.
*   **AI Orchestration Framework:** **LlamaIndex**. While LangChain is popular, LlamaIndex is purpose-built and vastly superior for indexing structured/semi-structured data (like crawled websites) and creating highly optimized retrieval pipelines.
*   **LLM Choice:** **Google Gemini 1.5 Flash** or **OpenAI gpt-4o-mini**. Both offer exceptional speed, low cost, and massive context windows (great for digesting large itinerary docs).
*   **Vector Database:** **Pinecone (Serverless)**. It removes the need for infrastructure management while offering high-speed semantic search.
*   **Frontend Chat Widget:** **React** or **Svelte** (embedded as a Web Component on satusatu.com).

### B. Ingestion Pipeline Architecture (The Knowledge Builder)
This pipeline runs asynchronously (e.g., daily or triggered by CMS updates).

1.  **Sitemap Crawler:** A script (using libraries like `Crawlee` or `BeautifulSoup`) parses `satusatu.com/sitemap.xml` to discover all active product and itinerary pages.
2.  **Scraping & Cleaning:** The crawler fetches each HTML page. Crucially, it must strip out headers, footers, and generic UI text to extract *only* the product descriptions, pricing, and itinerary details.
3.  **Semantic Chunking:** The cleaned text is broken into manageable "chunks" (e.g., 512 tokens). Splitting by semantic boundaries (like markdown headers) ensures complete thoughts are kept together.
4.  **Metadata Tagging:** Each chunk is tagged with metadata (e.g., `{"url": "...", "type": "attraction", "location": "Bali"}`). This is vital for accurate retrieval.
5.  **Embedding & Upsert:** The chunks are converted into vector embeddings (using `text-embedding-3-small` or similar) and pushed to **Pinecone** alongside their metadata.

### C. Retrieval/Generation Pipeline (The Real-Time RAG)
This is the synchronous API triggered when a user sends a message. It incorporates the strict guardrails.

1.  **Intent Router (Guardrail 1 - Off-Topic Prevention):**
    *   The user's query first hits a fast classification prompt (or a small fine-tuned model): *"Is this query regarding a product, ticket, or itinerary on satusatu.com? Yes/No."*
    *   If **No**, the system immediately short-circuits and returns a pre-canned response: *"I specialize in attractions and itineraries for satusatu.com. Please let me know how I can help you plan your trip with our available services."*
2.  **Semantic Retrieval:**
    *   If valid, the query is embedded and searched against the Pinecone Vector DB to find the most relevant product/itinerary chunks.
3.  **Confidence Check (Guardrail 2 - Human Handoff Gateway):**
    *   Analyze the retrieval scores. If the closest match falls below a strict similarity threshold (e.g., the user asked for a product satusatu.com doesn't sell), the system triggers the **Graceful Handoff** flow.
4.  **Conditioned Generation (Guardrail 3 - Domain Confinement):**
    *   The retrieved chunks and user query are sent to the primary LLM (Gemini 1.5) with a highly constrained System Prompt:
        > *"You are the satusatu.com concierge. You MUST ONLY use the provided Context to answer the user. Do not invent products, prices, or itineraries. If the Context does not contain the answer, you MUST reply with the exact string 'TRIGGER_HANDOFF'."*
5.  **Output Processing & UI Rendering:**
    *   If the LLM generates the response, it streams to the frontend.
    *   If the LLM outputs `'TRIGGER_HANDOFF'` (or the threshold check failed in Step 3), the backend intercepts this and sends a structured payload to the frontend.
    *   **The UI Action:** The React/Svelte widget reads the handoff payload and renders the custom message alongside the requested interactive **Freshdesk** and **WhatsApp** action buttons, cleanly handing the user off to human support.
