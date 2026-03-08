import streamlit as st
import networkx as nx
from streamlit_agraph import agraph, Node, Edge, Config
from main import run_pipeline
from openai import OpenAI  # Added for RAG

st.set_page_config(page_title="Layer10 Corporate Memory", layout="wide")

# 1. Run/Load the pipeline
@st.cache_resource
def get_graph():
    return run_pipeline()

kg = get_graph()

# Initialize AI Auditor Client
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# --- 2. GLOBAL CONFIGURATION ---
graph_config = Config(
    width=1400, 
    height=800, 
    directed=True, 
    nodeHighlightBehavior=True, 
    highlightColor="#F7A7A6", 
    collapsible=False,
    stabilization=True,
    fit=True,
    physics=True,
    physics_config={
        "forceAtlas2Based": {
            "gravitationalConstant": -150, 
            "centralGravity": 0.05,        
            "springLength": 150,           
            "springConstant": 0.08,
            "damping": 0.4,
            "avoidOverlap": 1 
        },
        "solver": "forceAtlas2Based" 
    }
)

# --- 3. SIDEBAR: Filters ---
st.sidebar.header("Memory Stats")
st.sidebar.write(f"Total Entities: {len([n for n, d in kg.G.nodes(data=True) if d['type']=='ENTITY'])}")
st.sidebar.write(f"Total Facts: {len([n for n, d in kg.G.nodes(data=True) if d['type']=='CLAIM'])}")
st.sidebar.markdown("---")

st.sidebar.header("Global Filters")
min_conf = st.sidebar.slider("Minimum Confidence Score", 0.0, 1.0, 0.0)
claim_types = list(set([d['claim_type'] for n, d in kg.G.nodes(data=True) if d['type']=='CLAIM']))
type_filter = st.sidebar.multiselect("Filter by Claim Type", options=claim_types, default=claim_types)

# --- 4. MAIN UI TABS ---
tab1, tab2, tab3 = st.tabs(["📁 Memory Trail & AI Auditor", "🕸️ Relationship Graph", "🔍 Deduplication Audit"])

with tab1:
    st.title("Grounded Memory Trail")
    
    # --- SECTION A: AI AUDITOR (Natural Language Query) ---
    st.subheader("🔍 AI Auditor: Ask the Graph")
    user_query = st.text_input(
        "Enter a question (e.g., 'What was Sharon Butcher's assignment?')", 
        key="ai_auditor_input"
        )

    if user_query:
        # 1. FUZZY RETRIEVAL: Normalize query and extract keywords
        filler_words = {"what", "was", "is", "the", "a", "an", "to", "for", "of", "in", "did", "do", "update", "on"}
        query_words = [w.strip("'s").lower() for w in user_query.split() if w.lower() not in filler_words]
        
        retrieved_results = []
        for node_id, node_data in kg.G.nodes(data=True):
            if node_data.get('type') == 'CLAIM':
                # Safely find the person linked to this claim
                parent_nodes = list(kg.G.predecessors(node_id))
                entity_label = kg.G.nodes[parent_nodes[0]].get('label', '').lower() if parent_nodes else ""
                
                # Combine claim and name for searching
                search_space = (str(node_data.get('value', '')) + " " + entity_label).lower()
                
                if any(word in search_space for word in query_words if len(word) > 2):
                    # Store both the data AND the entity label for the LLM
                    retrieved_results.append({
                        "data": node_data,
                        "entity": entity_label.title()
                    })

        if retrieved_results:
            # 2. CONTEXT PACK: Map facts to specific entities so LLM knows who is who
            context_entries = []
            for item in retrieved_results[:3]:
                c = item['data']
                context_entries.append(
                    f"Entity: {item['entity']}\nFact: {c['value']}\nSource: {c['source']}\nQuote: \"{c['quote']}\""
                )
            
            context_text = "\n\n".join(context_entries)
            
            # 3. GROUNDED GENERATION: Instructions to prevent "no info" errors
            with st.spinner("Consulting corporate memory..."):
                try:
                    response = client.chat.completions.create(
                        model="llama3",
                        messages=[
                            {"role": "system", "content": "You are a Corporate Auditor. Answer using ONLY the provided Context. The 'Entity' listed is the subject of the 'Fact'. Always cite Source IDs."},
                            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {user_query}"}
                        ]
                    )
                    st.info(f"**Audit Response:** {response.choices[0].message.content}")
                    with st.expander("View Retrieved Context Pack (JSON)"):
                        st.json([r['data'] for r in retrieved_results[:3]])
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("No relevant facts found for this query.")

    st.markdown("---")
    
    # --- SECTION B: MANUAL BROWSER ---
    entities = [d['label'] for n, d in kg.G.nodes(data=True) if d['type']=='ENTITY']
    search_query = st.selectbox("Or, select an Entity to browse history:", options=sorted(entities))

    if search_query:
        st.subheader(f"History for: {search_query}")
        target_node = [n for n, d in kg.G.nodes(data=True) if d.get('label') == search_query][0]
        claims = [n for n in kg.G.neighbors(target_node)]
        claims.sort(key=lambda x: kg.G.nodes[x]['source'], reverse=True)
        latest_source = kg.G.nodes[claims[0]]['source'] if claims else None
        
        for c_id in claims:
            data = kg.G.nodes[c_id]
            if data.get('confidence_score', 0.0) < min_conf: continue
            if data['claim_type'] not in type_filter: continue
            
            is_latest = "🟢 (LATEST)" if data['source'] == latest_source else "⚪ (HISTORICAL)"
            with st.expander(f"{is_latest} {data['claim_type']}: {data['value']}"):
                st.write(f"**Evidence Quote:** \"{data['quote']}\"")
                st.caption(f"Source: {data['source']} | Confidence: {data.get('confidence_score', 'N/A')} | Engine: {data.get('extraction_version', 'v1.0')}")

with tab2:
    st.title("Visual Entity Relationship Map")
    visible_claims = [n for n, d in kg.G.nodes(data=True) if d['type']=='CLAIM' and d.get('confidence_score', 0.0) >= min_conf]
    visible_entities = [n for n, d in kg.G.nodes(data=True) if d['type']=='ENTITY']
    
    nodes = []
    for n in visible_entities + visible_claims:
        d = kg.G.nodes[n]
        is_entity = d['type'] == 'ENTITY'
        nodes.append(Node(
            id=n, 
            label=d.get('label', n), 
            size=40 if is_entity else 20, 
            color="#1f77b4" if is_entity else "#ff7f0e",
            font={'size': 20 if is_entity else 14, 'color': 'white', 'face': 'Arial', 'strokeWidth': 2, 'strokeColor': 'black'}
        ))

    edges = [Edge(source=u, target=v) for u, v in kg.G.edges() if u in visible_entities and v in visible_claims]
    if nodes:
        agraph(nodes=nodes, edges=edges, config=graph_config)
    else:
        st.warning("No nodes match your current filters.")

with tab3:
    st.title("Deduplication & Identity Audit")
    if hasattr(kg, 'identity_manager') and kg.identity_manager.merge_log:
        st.table(kg.identity_manager.merge_log)
    else:
        st.info("No identity merges detected in current session.")
