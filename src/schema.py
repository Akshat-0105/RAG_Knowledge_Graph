from pydantic import BaseModel, Field
from typing import List, Literal

class Evidence(BaseModel):
    quote: str = Field(..., description="The exact sentence providing the proof")
    source_id: str = Field(..., description="The filename of the email")

class ProjectClaim(BaseModel):
    entity_name: str
    # The final, generalized corporate ontology
    claim_type: Literal["DEADLINE", "STATUS", "ASSIGNMENT", "BUDGET_ALLOCATION", "DECISION"]
    claim_value: str
    evidence: Evidence
    confidence_score: float = Field(..., ge=0, le=1)
    extraction_version: str = Field(default="v1.1-generalized")

class EnronMemory(BaseModel):
    claims: List[ProjectClaim] = Field(..., description="Validated business claims")