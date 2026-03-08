import json
import os
import instructor
from openai import OpenAI
from src.schema import EnronMemory

client = instructor.patch(
    OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"),
    mode=instructor.Mode.JSON,
)

PROGRESS_FILE = "processed_files.json"

def clean_enron_email(text):
    if "\n\n" in text:
        return text.split("\n\n", 1)[1].strip()
    return text.strip()

def is_relevant(text):
    """
    Generalized Business Relevance Filter with Quality Threshold.
    Filters out short logistical noise (under 150 chars).
    """
    intent_indicators = [
        "assign", "approve", "budget", "deadline", "contract", 
        "agreement", "milestone", "decision", "finalize", "delay"
    ]
    value_indicators = ["quarterly", "expenditure", "allocation", "authorization"]
    
    text_lower = text.lower()
    has_intent = any(ind in text_lower for ind in intent_indicators)
    has_value = any(val in text_lower for val in value_indicators)
    
    # 150 threshold is essential to avoid 'Breakfast' and 'Forwarding' junk
    return (has_intent or has_value) and len(text) > 150

def extract_from_file(file_path):
    with open(file_path, 'r', errors='ignore') as f:
        raw_content = f.read()
    
    filename = os.path.basename(file_path)
    clean_content = clean_enron_email(raw_content)

    # Use the generalized relevance gate
    if not is_relevant(clean_content):
        return []

    try:
        data = client.chat.completions.create(
            model="llama3",
            response_model=EnronMemory,
            messages=[
                {
                    "role": "system", 
                    # In src/extractor.py
                    "content": """You are a Corporate Memory Auditor. Your goal is to extract ONLY high-stakes business facts.
                    
                    STRICT REJECTION RULES (Anti-Absurdity):
                    1. REJECT 'Forwarding': Receiving or forwarding an email is NOT an assignment.
                    2. REJECT 'Logistics': Times, meals, and room numbers are NEVER Budget or Deadlines.
                    3. REJECT 'CC Lists/Signatures': Do not extract people just for being in headers or signatures.
                    4. NO 'NIL' VALUES: If you cannot find a specific dollar amount, task, or date, return an empty list [].
                    
                    EXTRACTION CRITERIA (High-Fidelity):
                    - BUDGET_ALLOCATION: Only for explicit financial resources or dollar amounts.
                    - DEADLINE: Only for project milestones or contractual completion dates.
                    - ASSIGNMENT: Only for explicit, high-value tasks delegated (e.g., 'Draft this contract').
                    - STATUS: Only for the definitive state of a project (e.g., 'Approved', 'Delayed').
                    - ENTITY: Use Full Names for People. Project names must be proper nouns.
                    
                    If no business-critical fact exists with evidence, return an empty list []."""
                },
                {"role": "user", "content": f"Source ID: {filename}\n\nContent: {clean_content}"}
            ],
        )
        # Ensure evidence is tagged with the source filename
        if data and data.claims:
            for claim in data.claims:
                claim.evidence.source_id = filename
            return data.claims
        return []
    except Exception: 
        return []

def load_processed_list():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_processed_list(processed_set):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(list(processed_set), f)

def process_directory(directory_path):
    all_claims = []
    processed_files = load_processed_list()
    
    all_files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    files_to_process = [f for f in all_files if f not in processed_files and not f.endswith(('.json', '.pkl'))]
    
    if not files_to_process:
        print("--- Phase 1: Extraction ---")
        print("No new files to process.")
        return []

    print("--- Phase 1: Extraction ---")
    print(f"Analyzing {len(files_to_process)} substantive files for business milestones...")
    
    for filename in files_to_process:
        file_path = os.path.join(directory_path, filename)
        claims = extract_from_file(file_path)
        all_claims.extend(claims)
        processed_files.add(filename)
    
    save_processed_list(processed_files)
    print(f"Extraction complete. Found {len(all_claims)} business-critical claims.")
    return all_claims