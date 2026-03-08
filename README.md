RAG_Knowledge_Graph: Corporate Memory Auditor


 Project Overview
This repository contains a high-fidelity pipeline for transforming unstructured corporate email corpora into a grounded, deduplicated Knowledge Graph. The system utilizes a "Quality Shield" architecture to eliminate logistical noise and "nil" value hallucinations common in standard LLM extractions.


 Technical Architecture & Decisions
1. Ontology
We focus on five high-stakes business primitives to ensure the graph provides actionable intelligence:

DEADLINE: Project milestones or contractual completion dates.

STATUS: Definitive states of a project (e.g., 'Approved', 'Delayed').

ASSIGNMENT: Explicit, high-value tasks delegated between entities.

BUDGET_ALLOCATION: Explicit financial resources or dollar amounts.

DECISION: Formal resolutions or approved paths forward.

2. Extraction Contract
To prevent "absurdity," the system employs a Strict Rejection Contract within the LLM prompt:

Hard Negatives: Explicitly forbids the extraction of forwarding logs, CC lists, and logistical noise (e.g., meals or room numbers).

Relevance Gating: A pre-processor filters out emails under 150 characters or those lacking high-intent business verbs to reduce token waste and noise.

3. Deduplication & Canonicalization
Identity Manager: Standardizes aliases (e.g., "jskillin" → "Jeff Skilling") and uses title-casing for consistency.

Junk Filtering: Utilizes regex and substring matching to block time-strings and signature-block entities (e.g., "& Associates") from becoming nodes.

4. Update Semantics
Incremental Processing: Uses a processed_files.json tracker to ensure only new files are analyzed in subsequent runs.

Non-Destructive Storage: Utilizes a NetworkX MultiDiGraph to allow multiple claims between entities without overwriting historical data.


 RAG Capabilities: AI Auditor
The system includes a functional Retrieval-Augmented Generation (RAG) interface:

Fuzzy Retrieval: A custom search engine resolves natural language queries (e.g., "Jeff Skilling's update") to grounded graph nodes, handling possessives and corporate suffixes.

Context Packaging: The auditor retrieves specific "Context Packs" (claims, quotes, and sources) from the graph to serve as the LLM's only source of truth.

Hallucination Guard: The AI Auditor is instructed to answer using ONLY the retrieved graph context, ensuring every response includes a verifiable Source ID.


 Adaptation to Layer10
To scale this proof-of-concept to Layer10's production environment, the following adaptations are recommended:

Sub-graph Extraction: Implement localized neighborhood retrieval to feed only relevant clusters to the LLM context window.

Persistent Graph Database: Migrate from serialized .pkl files to Neo4j for real-time querying across millions of nodes.

Distributed Extraction: Deploy the extraction logic as serverless functions to handle massive parallel ingestion spikes.


 How to Reproduce
Setup Environment: pip install -r requirements.txt.

Local LLM: Ensure Ollama is running with the llama3 model.

Run Pipeline: Place emails in the /data directory and run python main.py.

Visualize & Query: Run streamlit run app.py to explore the Grounded Memory Trail and use the AI Auditor.
