from pydantic import BaseModel, Field
from typing import Literal


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"] = Field(description="роль отправителя")
    content: str = Field(description="отправленный контент")

    
class ChatCompletionRequest(BaseModel):
    model: str = Field(description="название модели которую мы вызываем")
    messages: list[Message]
    stream: bool = Field(default=False, description="ответ по кусочкам или отдать целиком")
    temperature: float | None =  Field(default=None, description="креативность")
    max_tokens: int | None = Field(default=None, description="потолок длины ответа")