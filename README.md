# 🧠 RAG Knowledge Graph: Corporate Memory Auditor
**An Audit-Grade Knowledge Graph Pipeline for High-Fidelity Corporate Intelligence.**

---

### 📁 Project Overview
This repository implements a **"Quality Shield"** architecture designed to transform unstructured corporate email corpora into a grounded, deduplicated Knowledge Graph. Unlike standard RAG systems, this pipeline explicitly filters out logistical noise and administrative "nil" values to ensure executive-level decision-making accuracy.

---

### 📁 Technical Architecture

#### **1. The Extraction Contract**
To ensure groundedness and prevent hallucinations, the system utilizes a **Strict Rejection Contract**:
* **High-Intent Ontology**: Captures only five business-critical primitives: `DEADLINE`, `STATUS`, `ASSIGNMENT`, `BUDGET`, and `DECISION`.
* **Hard Negatives**: Explicitly rejects forwarding logs, CC lists, and logistical noise such as meals or room numbers.
* **Relevance Gating**: A pre-processor filters emails lacking high-intent business verbs or substantive length.

#### **2. Identity & Update Semantics**
* **Canonical Identity Manager**: Resolves complex corporate aliases (e.g., `jskillin` → `Jeff Skilling`) while filtering signature-block "ghost nodes".
* **Incremental Update Semantics**: Employs a stateful tracker (`processed_files.json`) for efficient, non-destructive processing of new data into a `MultiDiGraph` store.

#### **3. RAG Capability: AI Auditor**
The system features a functional **Retrieval-Augmented Generation (RAG)** interface:
* **Fuzzy Retrieval**: Resolves natural language queries to grounded graph nodes by handling corporate suffixes and possessives.
* **Context Packaging**: The auditor retrieves specific "Context Packs" (claims and quotes) to serve as the LLM's absolute source of truth.
* **Grounding Guard**: Every response is forced to cite a verifiable Source ID from the graph.

---

### 📁 Adaptation to Layer10
To scale this proof-of-concept to Layer10’s production requirements, we recommend:
1.  **Localized Sub-graph Extraction**: Implementing neighborhood-traversal to retrieve only the relevant clusters for the LLM context.
2.  **Persistent Graph Database**: Migrating from `.pkl` serialization to **Neo4j** for real-time querying across millions of nodes.
3.  **Distributed Extraction**: Deploying logic as serverless functions to handle massive parallel ingestion spikes.

---

### 📁 How to Reproduce
1.  **Environment**: `pip install -r requirements.txt`.
2.  **Local LLM**: Ensure **Ollama** is running with the `llama3` model.
3.  **Run Pipeline**: Place emails in `/data` and execute `python main.py`.
4.  **Launch UI**: `streamlit run app.py` to explore the **Memory Trail** and **AI Auditor**.
