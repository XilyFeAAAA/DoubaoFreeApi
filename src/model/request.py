from pydantic import BaseModel

class CompletionRequest(BaseModel):
    prompt: str 
    attachments: list[dict] = []
    conversation_id: str = "0" 
    section_id: str | None = None


class AttachmentRequest(BaseModel):
    key: str
    name: str
    type: str
    file_review_state: int
    file_parse_state: int
    identifier: str
    option: dict | None = None
    md5: str | None = None
    size: int | None = None


class UploadRequest(BaseModel):
    file_type: int
    file_name: str
    file_bytes: bytes