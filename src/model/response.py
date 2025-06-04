from pydantic import BaseModel
import uuid


class CompletionResponse(BaseModel):
    text: str
    img_urls: list[str]
    conversation_id: str
    messageg_id: str
    section_id: str
    
    
class UploadResponse(BaseModel):
    key: str
    name: str
    type: str
    file_review_state: int
    file_parse_state: int
    identifier: str
    option: dict | None = None
    md5: str | None = None
    size: int | None = None
    

class ImageResponse(BaseModel):
    key: str
    name: str
    option: dict
    type: str = "vlm_image"
    file_review_state: int = 3
    file_parse_state: int = 3
    identifier: str = str(uuid.uuid1())


class FileResponse(BaseModel):
    key: str
    name: str
    md5: str
    size: int
    type: str = "file"
    file_review_state: int = 1
    file_parse_state: int = 3
    identifier: str = str(uuid.uuid1())
    

class DeleteResponse(BaseModel):
    ok: bool
    msg: str