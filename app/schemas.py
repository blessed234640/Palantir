from pydantic import BaseModel, Field
from typing import Literal


class Message(BaseModel):
    model: str = Field(description="название модели которую мы вызываем")
    role: str = Field(Literal["system", "user", "assistant", "tool"], description="роль отправителя")
    content: str = Field(description="отправленный контент")

    
class ChatCompletionRequest(BaseModel):
    messages: list[Message]
    stream: bool | None = Field(description="ответ по кусочкам или отдать целиком")
    temperature: float | None =  Field(description="креативность")
    max_tokens: int | None = Field(description="потолок длины ответа")