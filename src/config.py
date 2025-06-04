import os
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(override=True)

class DoubaoConfig(BaseModel):
    """豆包API配置"""
    cookie: str
    x_ms_token: str
    device_id: str
    tea_uuid: str
    web_id: str
    ms_token: str
    a_bogus: str
    room_id: str
    x_flow_trace: str
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls(
            cookie=os.getenv("DOUBAO_COOKIE", ""),
            x_ms_token=os.getenv("DOUBAO_X_MS_TOKEN", ""),
            device_id=os.getenv("DOUBAO_DEVICE_ID", ""),
            tea_uuid=os.getenv("DOUBAO_TEA_UUID", ""),
            web_id=os.getenv("DOUBAO_WEB_ID", ""),
            ms_token=os.getenv("DOUBAO_MS_TOKEN", ""),
            a_bogus=os.getenv("DOUBAO_A_BOGUS", ""),
            room_id=os.getenv("DOUBAO_ROOM_ID", ""),
            x_flow_trace=os.getenv("DOUBAO_X_FLOW_TRACE", "")
        )

class AppConfig(BaseModel):
    """应用配置"""
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8000"))
    debug: bool = os.getenv("APP_DEBUG", "False").lower() == "true"
    
    # 豆包API配置
    doubao: DoubaoConfig = DoubaoConfig.from_env()

# 全局配置实例
config = AppConfig() 