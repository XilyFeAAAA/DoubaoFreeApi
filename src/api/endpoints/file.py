from fastapi import APIRouter, Body, Query, HTTPException
from src.service import upload_file
from src.model.response import UploadResponse


router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def api_upload(file_type: int = Query(), file_name: str = Query(), file_bytes: bytes = Body()):
    """上传图片或文件到豆包服务器"""
    try:
        return await upload_file(file_type, file_name, file_bytes)
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
