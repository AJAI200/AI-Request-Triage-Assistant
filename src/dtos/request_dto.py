from pydantic import BaseModel, Field

class TriageRequestDTO(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="The incoming unstructured client request text")

class ApproveDraftDTO(BaseModel):
    final_text: str = Field(..., min_length=1, description="The human-reviewed final email text to dispatch")
