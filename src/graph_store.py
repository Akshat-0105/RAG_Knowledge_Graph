import networkx as nx
import pickle
import os
# FIXED: Explicitly import the standardized methods for noise filtering
from src.identity import get_entity_id, canonicalize_name, get_merge_log

class KnowledgeGraph:
    def __init__(self):
        self.G = nx.MultiDiGraph() # MultiDiGraph allows multiple "claims" between same nodes
        # Attach the shared merge log for the UI Deduplication Audit
        self.identity_manager = type('obj', (object,), {'merge_log': get_merge_log()})

    def save_graph(self, filename="graph_data.pkl"):
        """Saves the graph to a file on the disk."""
        with open(filename, 'wb') as f:
            pickle.dump(self.G, f)
        print(f"Graph saved to {filename}")

    @staticmethod
    def load_graph(filename="graph_data.pkl"):
        """Loads the graph from a file if it exists."""
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                new_kg = KnowledgeGraph()
                new_kg.G = pickle.load(f)
                return new_kg
        return KnowledgeGraph() # Return a fresh one if no file exists
    
    def add_claim(self, claim):
        """Adds a business claim to the graph with a strict noise gate."""
        # 1. Get stable IDs and standardized names from the IdentityManager
        entity_id = get_entity_id(claim.entity_name)
        display_name = canonicalize_name(claim.entity_name)
        
        # 2. HARD GATE: Exit immediately if flagged as logistics or junk
        # This prevents 'Breakfast' or 'Saturday' from ever becoming nodes.
        if entity_id == "FILTERED_NODE" or display_name == "(Logistics/Noise)":
            return 

        # 3. Ensure the high-value entity node exists
        if not self.G.has_node(entity_id):
            self.G.add_node(entity_id, label=display_name, type="ENTITY")

        val = str(claim.claim_value).lower()
        if val in ["nil", "none", "unknown", "n/a"]:
            return
            
        # 4. Create a unique ID for the claim node to handle revisions
        claim_node_id = f"CLAIM_{claim.claim_type}_{entity_id}_{claim.evidence.source_id}"
        
        # 5. Add the factual claim with full provenance metadata
        self.G.add_node(claim_node_id, 
                        type="CLAIM",
                        claim_type=claim.claim_type,
                        value=claim.claim_value,
                        source=claim.evidence.source_id,
                        quote=claim.evidence.quote,
                        confidence_score=getattr(claim, 'confidence_score', 0.0),
                        extraction_version=getattr(claim, 'extraction_version', 'v1.0'))
        
        # 6. Link Entity to the Claim with a semantic relation
        self.G.add_edge(entity_id, claim_node_id, relation="HAS_FACT")

    def get_summary(self):
        """Returns the current scale of the validated memory graph."""
        return f"Graph has {self.G.number_of_nodes()} nodes and {self.G.number_of_edges()} edges."

# Test Logic
if __name__ == "__main__":
    kg = KnowledgeGraph()
    print("Graph Store initialized.")