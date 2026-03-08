import streamlit as st
import networkx as nx
from streamlit_agraph import agraph, Node, Edge, Config
from main import run_pipeline

st.set_page_config(page_title="Layer10 Corporate Memory", layout="wide")

# 1. Run/Load the pipeline
@st.cache_resource
def get_graph():
    return run_pipeline()

kg = get_graph()

# --- 2. UPDATED GLOBAL CONFIGURATION (Centered Physics) ---
# We use 'forceAtlas2Based' solver for more professional, centered clustering.
graph_config = Config(
    width=1400, 
    height=800, 
    directed=True, 
    nodeHighlightBehavior=True, 
    highlightColor="#F7A7A6", 
    collapsible=False,
    # --- CENTERING & STABILITY SETTINGS ---
    # Stabilization ensures the physics 'settle' in the center before rendering.
    stabilization=True,
    fit=True,
    physics=True,
    physics_config={
        "forceAtlas2Based": {
            "gravitationalConstant": -150, # Lower repulsion for small node counts
            "centralGravity": 0.05,        # Stronger pull to the 0,0 coordinate
            "springLength": 150,           # Keeps claims tight to their entities
            "springConstant": 0.08,
            "damping": 0.4,
            "avoidOverlap": 1 
        },
        "solver": "forceAtlas2Based" # Better for centered, organic layouts
    }
)

# --- 3. SIDEBAR: Filters ---
st.sidebar.header("Memory Stats")
# Correctly identify node types from the Graph Store
st.sidebar.write(f"Total Entities: {len([n for n, d in kg.G.nodes(data=True) if d['type']=='ENTITY'])}")
st.sidebar.write(f"Total Facts: {len([n for n, d in kg.G.nodes(data=True) if d['type']=='CLAIM'])}")
st.sidebar.markdown("---")

st.sidebar.header("Global Filters")
min_conf = st.sidebar.slider("Minimum Confidence Score", 0.0, 1.0, 0.0)
claim_types = list(set([d['claim_type'] for n, d in kg.G.nodes(data=True) if d['type']=='CLAIM']))
type_filter = st.sidebar.multiselect("Filter by Claim Type", options=claim_types, default=claim_types)

# --- 4. MAIN UI TABS ---
tab1, tab2, tab3 = st.tabs(["📁 Memory Trail", "🕸️ Relationship Graph", "🔍 Deduplication Audit"])

with tab1:
    st.title("Grounded Memory Trail")
    # Entity search via standardized labels
    entities = [d['label'] for n, d in kg.G.nodes(data=True) if d['type']=='ENTITY']
    search_query = st.selectbox("Select an Entity to see Memory:", options=sorted(entities))

    if search_query:
        st.subheader(f"History for: {search_query}")
        target_node = [n for n, d in kg.G.nodes(data=True) if d.get('label') == search_query][0]
        claims = [n for n in kg.G.neighbors(target_node)]
        
        # Sort so newest file is at the top for temporal reasoning
        claims.sort(key=lambda x: kg.G.nodes[x]['source'], reverse=True)
        latest_source = kg.G.nodes[claims[0]]['source'] if claims else None
        
        for c_id in claims:
            data = kg.G.nodes[c_id]
            
            # Apply Sidebar Filters
            if data.get('confidence_score', 0.0) < min_conf: continue
            if data['claim_type'] not in type_filter: continue
            
            is_latest = "🟢 (LATEST)" if data['source'] == latest_source else "⚪ (HISTORICAL)"
            with st.expander(f"{is_latest} {data['claim_type']}: {data['value']}"):
                st.write(f"**Evidence Quote:** \"{data['quote']}\"")
                st.caption(f"Source: {data['source']} | Confidence: {data.get('confidence_score', 'N/A')} | Engine: {data.get('extraction_version', 'v1.0')}")

with tab2:
    st.title("Visual Entity Relationship Map")
    
    # Filter visible elements based on sidebar confidence
    visible_claims = [n for n, d in kg.G.nodes(data=True) if d['type']=='CLAIM' and d.get('confidence_score', 0.0) >= min_conf]
    visible_entities = [n for n, d in kg.G.nodes(data=True) if d['type']=='ENTITY']
    
    # Optimized Node Generation
    nodes = []
    for n in visible_entities + visible_claims:
        d = kg.G.nodes[n]
        is_entity = d['type'] == 'ENTITY'
        
        nodes.append(Node(
            id=n, 
            label=d.get('label', n), 
            size=40 if is_entity else 20, 
            color="#1f77b4" if is_entity else "#ff7f0e",
            # --- HIGH-VISIBILITY FONT CONTRACT ---
            # White text against dark nodes, with shadow for clarity
            font={
                'size': 20 if is_entity else 14, 
                'color': 'white', # Changed from 'black'
                'face': 'Arial, Helvetica, sans-serif',
                # Add a stroke width to create a text 'outline' or shadow
                # This ensures visibility if the background becomes lighter
                'strokeWidth': 2, 
                'strokeColor': 'black' # Creates a black shadow around the white text
            }
        ))

    # Define edges based on the visible nodes
    edges = [Edge(source=u, target=v) for u, v in kg.G.edges() if u in visible_entities and v in visible_claims]

    if nodes:
        # Pass the globally defined config here
        agraph(nodes=nodes, edges=edges, config=graph_config)
    else:
        st.warning("No nodes match your current filters.")

with tab3:
    st.title("Deduplication & Identity Audit")
    st.markdown("Inspect aliases and merged entities as required by the specification.")
    
    # Access the log from the graph store's identity manager
    if hasattr(kg, 'identity_manager') and kg.identity_manager.merge_log:
        st.table(kg.identity_manager.merge_log)
    else:
        st.info("No identity merges detected in current session.")