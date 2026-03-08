RAG_Knowledge_Graph: Corporate Memory Auditor

 Project Overview
This repository contains a high-fidelity pipeline for transforming unstructured corporate email corpora into a grounded, deduplicated Knowledge Graph. The system utilizes a "Quality Shield" architecture to eliminate the logistical noise and "nil" value hallucinations common in standard LLM extractions.

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

Hard Negatives: Explicitly forbids the extraction of forwarding logs, CC lists, and logistical noise such as meal times or room numbers.

Relevance Gating: A pre-processor filters out any email under 150 characters or lacking high-intent business verbs to save tokens and reduce noise.

3. Deduplication & Canonicalization
Identity Manager: Standardizes aliases (e.g., "jskillin" → "Jeff Skilling") and uses title-casing for consistency.

Junk Filtering: Utilizes regex to block time-strings and signature-block entities (e.g., "& Associates") from becoming nodes.

4. Update Semantics
Incremental Processing: Uses a processed_files.json tracker to ensure only new files are analyzed in subsequent runs.

Non-Destructive Storage: Utilizes a NetworkX MultiDiGraph to allow multiple claims between entities without overwriting historical data.

 Adaptation to Layer10
To scale this proof-of-concept to Layer10's production environment, the following adaptations are recommended:

Vector Pre-filtering: Use embeddings to cluster similar emails before extraction to further reduce token costs.

Persistent Graph Database: Migrate from serialized .pkl files to Neo4j for real-time querying across millions of nodes.

Distributed Workers: Deploy the extraction logic as serverless functions to handle massive parallel ingestion.

 How to Reproduce
Setup Environment: pip install -r requirements.txt.

Local LLM: Ensure Ollama is running with the llama3 model.

Run Pipeline: Place emails in the /data directory and run python main.py.

Visualize: Run streamlit run app.py to explore the Grounded Memory Trail and Relationship Map.
