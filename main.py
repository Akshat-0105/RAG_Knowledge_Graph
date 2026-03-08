from src.extractor import process_directory
from src.graph_store import KnowledgeGraph

def run_pipeline():
    # 1. Load existing memory or start fresh
    kg = KnowledgeGraph.load_graph()
    
    # 2. Run Extraction
    # NOTE: The 'Phase 1' header is already handled inside process_directory
    claims = process_directory("data")
    
    if not claims:
        # This only prints if the extractor found nothing new to process
        print("No new business-critical claims to add.")
    else:
        # 3. Load NEW claims into the Graph
        print("\n--- Phase 2: Building Memory Graph ---")
        for c in claims:
            # Per-claim print remains silenced to prevent terminal clutter
            kg.add_claim(c)
        
        # 4. Save the updated graph back to disk
        kg.save_graph()
        
    # 5. Final Report
    # Displays the total number of professional nodes/edges
    print(f"\nPipeline Complete! {kg.get_summary()}")
    return kg

if __name__ == "__main__":
    graph = run_pipeline()