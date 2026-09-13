from pydantic import BaseModel

class LoginRequestDTO(BaseModel):
    username: str
    password: str

class UserInfoDTO(BaseModel):
    id: int
    username: str
    role: str

class TokenResponseDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfoDTO
