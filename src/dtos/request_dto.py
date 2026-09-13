from pydantic import BaseModel, Field

class TriageRequestDTO(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="The incoming unstructured client request text")
