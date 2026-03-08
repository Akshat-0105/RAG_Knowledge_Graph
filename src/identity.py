import re

class IdentityManager:
    def __init__(self):
        # Maps raw alias -> Canonical Name
        # Only persistent, cross-corpus mappings should live here.
        self.mappings = {
            "skilling@enron.com": "Jeff Skilling",
            "jeff.skilling@enron.com": "Jeff Skilling",
            "jskillin": "Jeff Skilling"
        }
        
        # Track merges for the UI "Deduplication Audit" tab
        self.merge_log = [] 

    def is_junk_entity(self, name):
        """
        Generalized logic to identify non-business entities.
        Uses regex and substring matching to catch logistics across any corpus.
        """
        name_low = name.lower().strip()
        
        # 1. Pattern Match: Catch ANY time-like strings (e.g., '7:45 A.M.', '1:30 PM')
        if re.search(r'\d{1,2}:\d{2}', name_low): 
            return True
        
        # 2. Pattern Match: Catch standalone years or counts (e.g., '2004', '105')
        if name_low.isdigit(): 
            return True

        # 3. Substring Match: Filter common administrative/temporal noise
        # This catches "Time: 7:45" or "Saturday, Dec 9" via substring detection.
        junk_indicators = [
            "today", "total", "average", "breakfast", "lunch", 
            "dinner", "room", "floor", "daily", "monday", 
            "tuesday", "wednesday", "thursday", "friday", 
            "saturday", "sunday", "time:", "date:", "contact:"
        ]
        if any(word in name_low for word in junk_indicators): 
            return True
        
        if len(name.split()) < 2 and not name_low.endswith(".com"):
            return True
        
        signature_indicators = ["& associates", "international", "group", "consulting", "inc.", "corp."]
        if any(ind in name_low for ind in signature_indicators):
            return True

        return False

    def canonicalize_name(self, name):
        """Standardizes name and tracks the transformation."""
        # First, check if the entity is logistical noise
        if self.is_junk_entity(name):
            return "(Logistics/Noise)"

        raw_name = name.lower().strip()
        
        # Structural removal of common noise prefixes
        processed_name = raw_name.replace("project ", "").replace("the ", "")
        
        # Fuzzy Match: Collapse informal names into full canonical identities
        if processed_name in ["jeff", "jeffrey"]:
            return "Jeff Skilling"

        # Apply mapping or convert to Title Case
        canonical = self.mappings.get(processed_name, processed_name.title())
        
        # Log merges for the Audit Tab if the name changed significantly
        if raw_name != canonical.lower() and canonical != "(Logistics/Noise)":
            self.merge_log.append({
                "Original": name,
                "Canonical": canonical,
                "Type": "Identity Resolution"
            })
            
        return canonical

    def get_entity_id(self, name):
        """Creates a stable ID for the graph nodes."""
        clean = self.canonicalize_name(name)
        
        # Route junk entities to a single ID that the GraphStore can reject
        if clean == "(Logistics/Noise)":
            return "FILTERED_NODE"
            
        # Create a clean ID like PERS_JEFF_SKILLING
        safe_id = re.sub(r'[^a-z0-9]', '_', clean.lower())
        return safe_id.upper()

# --- EXPORT FOR SYSTEM-WIDE USE ---
# Initialize once to share the merge_log across all modules.
_manager = IdentityManager()

get_entity_id = _manager.get_entity_id
canonicalize_name = _manager.canonicalize_name
get_merge_log = lambda: _manager.merge_log