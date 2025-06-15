import os
import json
import random
from pydantic import BaseModel
from loguru import logger
from .fetcher import DoubaoAutomator

class DoubaoSession(BaseModel):
    """豆包API会话配置"""
    cookie: str
    device_id: str
    tea_uuid: str
    web_id: str
    room_id: str
    x_flow_trace: str
    
    def to_dict(self) -> dict[str, str]:
        """转换为字典"""
        return {
            "cookie": self.cookie,
            "device_id": self.device_id,
            "tea_uuid": self.tea_uuid,
            "web_id": self.web_id,
            "room_id": self.room_id,
            "x_flow_trace": self.x_flow_trace,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, str]) -> 'DoubaoSession':
        return cls(**data)


class SessionPool:
    """豆包API会话池，管理多个账号配置"""
    def __init__(self, config_file: str = "session.json"):
        # conversation_id -> DoubaoSession
        self.session_map: dict[str, DoubaoSession] = {}
        self.auth_sessions: list[DoubaoSession] = []
        self.guest_sessions: list[DoubaoSession] = [] 
        self.config_file = config_file
        self.load_from_file()
    
    def create_session(
        self,
        guest: bool,
        cookie: str,
        device_id: str,
        tea_uuid: str,
        web_id: str,
        room_id: str,
        x_flow_trace: str
    ) -> DoubaoSession:
        """创建新会话配置"""
        session = DoubaoSession(
            cookie=cookie,
            device_id=device_id,
            tea_uuid=tea_uuid,
            web_id=web_id,
            room_id=room_id,
            x_flow_trace=x_flow_trace
        )
        if guest:
            self.guest_sessions.append(session)
        else:
            self.auth_sessions.append(session)
    
    def get_session(self, conversation_id: str | None = None, guest: bool = False) -> DoubaoSession:
        """获取会话配置，如果不存在则随机"""
        if conversation_id is None:
            if guest:
                return random.choice(self.guest_sessions) if self.auth_sessions else None
            else:
                return random.choice(self.auth_sessions) if self.guest_sessions else None
        else:
            return self.session_map.get(conversation_id)
    
    def set_session(self, conversation_id: str, session: DoubaoSession):
        """将会话与conversation_id关联"""
        self.session_map[conversation_id] = session
    
    def del_session(self, session: DoubaoSession):
        """删除会话"""
        if session.is_logged:
            self.auth_sessions.remove(session)
        else:
            self.guest_sessions.remove(session)
        self.save_to_file()
    
    def save_to_file(self):
        """保存会话配置到文件"""
        try:
            data = [session.to_dict() for session in (self.auth_sessions + self.guest_sessions)]
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.debug(f"会话配置已保存到文件: {self.config_file}")
        except Exception as e:
            logger.error(f"保存会话配置到文件失败: {str(e)}")
    
    def load_from_file(self):
        """从文件加载会话配置"""
        if not os.path.exists(self.config_file):
            return logger.warning(f"会话配置文件不存在: {self.config_file}")
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for session_data in data:
                self.create_session(guest=False, **session_data)
            
            logger.info(f"已从文件加载会话配置")
        except Exception as e:
            logger.error(f"从文件加载会话配置失败: {str(e)}")
    
    async def fetch_guest_session(self, num: int):
        for _ in range(num):
            automator = DoubaoAutomator()
            self.create_session(
                guest=True,
                **(await automator.run_automation())
            )


session_pool = SessionPool()

__all__ = [
    "DoubaoSession",
    "SessionPool",
    "session_pool"
] 