from fastapi import APIRouter
from .endpoints import chat
from .endpoints import file

router = APIRouter()

# 注册各个模块的路由
router.include_router(chat.router, prefix="/chat", tags=["聊天"])
router.include_router(file.router, prefix="/file", tags=["文件"])