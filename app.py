from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.router import router
from src.config import config
import uvicorn


app = FastAPI(
    title="豆包API服务",
    description="轻量级豆包API代理服务",
    version="0.1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("app:app", host=config.host, port=config.port, reload=config.debug)
