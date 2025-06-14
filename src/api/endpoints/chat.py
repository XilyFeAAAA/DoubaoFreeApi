from fastapi import APIRouter, Body, Query, HTTPException
from src.service import chat_completion, delete_conversation
from src.model.response import CompletionResponse, DeleteResponse
from src.model.request import CompletionRequest


router = APIRouter()


@router.post("/completions", response_model=CompletionResponse)
async def api_completions(completion: CompletionRequest = Body()):
    """
    豆包聊天补全接口(目前仅支持文字消息e和图片消息)
    1. 如果是新聊天 conversation_id, section_id**不填**
    2. 如果沿用之前的聊天, 则沿用**第一次对话**返回的 conversation_id 和 section_id, 会话池会使用之前的参数
    3. 目前如果使用未登录账号，那么不支持上下文
    """
    try:
        text, imgs, conv_id, msg_id, sec_id = await chat_completion(
            prompt=completion.prompt,
            guest=completion.guest,
            conversation_id=completion.conversation_id,
            section_id=completion.section_id,
            attachments=completion.attachments,
            use_auto_cot=completion.use_auto_cot,
            use_deep_think=completion.use_deep_think
        )
        return CompletionResponse(
            text=text, 
            img_urls=imgs, 
            conversation_id=conv_id, 
            messageg_id=msg_id, 
            section_id=sec_id
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/delete", response_model=DeleteResponse)
async def api_delete(conversation_id: str = Query()):
    """
    删除聊天
    1. conversation_id 不存在也会提示成功
    2. 建议在聊天结束时都调用函数，避免创建过多对话
    """
    try:
        ok, msg = await delete_conversation(conversation_id)
        return DeleteResponse(
            ok=ok,
            msg=msg
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))