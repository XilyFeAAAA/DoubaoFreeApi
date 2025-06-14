from src.model.response import FileResponse, ImageResponse
from src.config import config
from requests_aws4auth import AWS4Auth
from fastapi import HTTPException
from loguru import logger
import os
import aiohttp
import httpx
import json
import uuid
import hashlib
import binascii

# ------ CONFIG ------- 
DEVICE_ID = config.doubao.device_id
TEA_UUID = config.doubao.tea_uuid
MS_TOKEN = config.doubao.ms_token
WEB_ID = config.doubao.web_id
A_BOGUS = config.doubao.a_bogus
COOKIE = config.doubao.cookie
X_MS_TOKEN = config.doubao.x_ms_token
ROOM_ID = config.doubao.room_id
X_FLOW_TRACE = config.doubao.x_flow_trace
# ------ PARAMS -------
params = "&".join([
    "aid=497858",
    f"device_id={DEVICE_ID}",
    "device_platform=web",
    "language=zh",
    "pc_version=2.20.0",
    "pkg_type=release_version",
    "real_aid=497858",
    "region=CN",
    "samantha_web=1",
    "sys_region=CN",
    f"tea_uuid={TEA_UUID}",
    "use-olympus-account=1",
    "version_code=20800",
    f"web_id={WEB_ID}",
    f"msToken={MS_TOKEN}",
    f"a_bogus={A_BOGUS}"
])



async def chat_completion(prompt: str, conversation_id: str, section_id: str = None, 
                        attachments: list[dict] = [], use_auto_cot: bool = False, use_deep_think: bool = False):
    local_msg_id = str(uuid.uuid4())
    local_conv_id = f"local_{int(uuid.uuid4().int % 10000000000000000)}"
    # ------ URL -------
    url = "https://www.doubao.com/samantha/chat/completion?" + params
    # ------ BODY -------
    body = {
        "completion_option": {
            "is_regen": False,
            "with_suggest": False,
            "need_create_conversation": conversation_id == "0",
            "launch_stage": 1,
            "use_auto_cot": use_auto_cot,
            "use_deep_think": use_deep_think
        },
        "conversation_id": conversation_id,
        "local_conversation_id": local_conv_id,
        "local_message_id": local_msg_id,
        "messages": [
            {
                "content": json.dumps({"text": prompt}),
                "content_type": 2001,
                "attachments": attachments,
                "references": []
            }
        ]
    }
    if section_id is not None:
        body["section_id"] = section_id
    # ------ HEADERS -------
    headers = {
        'content-type': 'application/json',
        'accept': 'text/event-stream',
        'agw-js-conv': 'str',
        'cookie': COOKIE,
        'x-ms-token': X_MS_TOKEN,
        'origin': "https://www.doubao.com",
        'referer': f"https://www.doubao.com/chat/{ROOM_ID}",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
        "x-flow-trace": X_FLOW_TRACE
    }
    logger.debug(f"请求豆包API，会话ID: {conversation_id}, 本地消息ID: {local_msg_id}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, json=body) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"豆包API对话补全失败: {response.status}, 详情: {error_text}")
                return await handle_sse(response)
    except Exception as e:
        raise Exception(f"豆包API请求失败: {str(e)}")
    

async def handle_sse(response: aiohttp.ClientResponse):
    buffer = ""
    conversation_id = ""
    message_id = ""
    section_id = ""
    texts = []
    image_urls = []
    
    async for chunk in response.content.iter_chunked(1024):
        buffer += chunk.decode('utf-8', errors='replace')
        
        if 'event: gateway-error' in buffer:
            error_match = buffer.find('data: {')
            if error_match != -1:
                try:
                    error_data = json.loads(buffer[error_match + 6:].split('\n')[0])
                    raise Exception(f"服务器返回网关错误: {error_data.get('code')} - {error_data.get('message')}")
                except Exception as e:
                    raise Exception(f"服务器返回网关错误: {buffer}")
        
        events = buffer.split('\n\n')
        buffer = events.pop()
        
        for evt in events:
            print(evt)
            lines = evt.strip().split('\n')
            data_line = next((l for l in lines if l.startswith('data: ')), None)
            if not data_line:
                continue
                
            try:
                evt_obj = json.loads(data_line[6:])
                event_type = evt_obj.get('event_type')
                event_data = json.loads(evt_obj.get('event_data', '{}'))
                if event_type == 2001:
                    # 流消息                      
                    if not (msg := event_data.get('message')): continue
                    
                    content_type = msg.get('content_type')
                    if content_type in [10000, 2001, 2008]:
                        # 文字消息
                        text =  json.loads(msg.get('content', '{}')).get('text', )
                        if text:
                            texts.append(text)
                    elif content_type == 2074:
                        # 图片消息
                        creations = json.loads(msg.get('content', '{}')).get('creations', [])
                        for creation in creations:
                            image_info = creation.get('image', {})
                            # 只处理status为2的完成图片
                            if image_info.get('status') == 2:
                                url = (image_info.get('image_ori', {}).get('url') or 
                                       image_info.get('image_raw', {}).get('url') or 
                                       image_info.get('image_thumb', {}).get('url'))
                                
                                if url and url not in image_urls:
                                    image_urls.append(url)
                    else:
                        logger.warning(f"未知的消息类型 {content_type}")
                elif event_type == 2002:
                    # 流开始
                    conversation_id = event_data.get("conversation_id")
                    message_id = event_data.get("message_id")
                    section_id = event_data.get("section_id")
                    logger.debug(f"SSE流开始: 会话ID={conversation_id}, 消息ID={message_id}")
                elif event_type == 2003:
                    # 流结束
                    text =  "".join(texts)
                    text = text.lstrip('\n').rstrip("\n")
                    logger.debug(f"SSE流结束: 获取到文本长度={len(text)}, 图片数量={len(image_urls)}")
                    return text, image_urls, conversation_id, message_id, section_id
                else:
                    logger.warning(f"未知的流类型 {event_type}")
            except Exception as e:
                raise Exception(f"解析SSE失败: {str(e)}")


async def upload_file(file_type: int, file_name: str, file_data: bytes) -> FileResponse | ImageResponse:
    """
    上传文件到豆包服务器，返回附件信息
    总体流程为：
    1. 通过 prepare-upload 拿到 AWS 凭证
    2. 通过 apply-upload 提交文件元信息
    3. 通过 upload 上传文件数据
    4. 通过 commit-upload 确认上传
    """
    logger.debug(f"开始上传文件: {file_name}, 类型: {file_type}, 大小: {len(file_data)} 字节")
    # ------ HEADERS -------
    DEFAULT_HEADERS = {
        'content-type': 'application/json',
        'cookie': COOKIE,
        'x-ms-token': X_MS_TOKEN,
        'origin': "www.doubao.com",
        'referer': "https://www.doubao.com/chat/",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
    }
    # 由于 AWS4Auth 不支持 Aiohttp, 所以采用异步库 HTTPX
    async with httpx.AsyncClient() as client:
        # PREPARE UPLOAD
        prepare_url = "https://www.doubao.com/alice/resource/prepare_upload?" + params
        prepare_payload = {
            "resource_type": file_type,  # 文档类型 1;图片类型 2; 
            "scene_id": "5",
            "tenant_id": "5"
        }
        resp = await client.post(url=prepare_url, headers=DEFAULT_HEADERS, json=prepare_payload)
        prepare_data = resp.json()
        upload_info = prepare_data.get("data", {})
        # APPLY UPLOAD
        service_id = upload_info.get("service_id")
        session_token = upload_info.get("upload_auth_token", {}).get("session_token")
        access_key = upload_info.get("upload_auth_token", {}).get("access_key")
        secret_key = upload_info.get("upload_auth_token", {}).get("secret_key")
        file_size = len(file_data)
        if not '.' in file_name:
            return HTTPException(status_code=500, detail="文件名格式错误，注意附带后缀名")
        file_ext = os.path.splitext(file_name)[1]
        apply_url = f"https://imagex.bytedanceapi.com/?Action=ApplyImageUpload&Version=2018-08-01&ServiceId={service_id}&NeedFallback=true&FileSize={file_size}&FileExtension={file_ext}"
        # 构建 AWS4Auth
        auth = AWS4Auth(access_key, secret_key, 'cn-north-1', "imagex", session_token=session_token)
        applu_request = client.build_request(
            method="GET",
            url=apply_url,
            headers={
                "origin": "https://www.doubao.com",
                "reference": "https://www.doubao.com",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
                }
            )
        auth.__call__(applu_request) 
        resp = await client.send(applu_request)
        data = resp.json()
        upload_address = data.get("Result", {}).get("UploadAddress", {})
        if not (infos := upload_address.get("StoreInfos", [])):
            return HTTPException(status_code=500, detail="Apply Upload 返回 StoreInfos列表为空")
        store_info = infos[0]
        store_url = store_info.get("StoreUri")
        store_auth = store_info.get("Auth")
        session_key = upload_address.get("SessionKey")
        # UPLOAD
        upload_url = f"https://tos-d-x-hl.snssdk.com/upload/v1/{store_url}"
        crc32 = format(binascii.crc32(file_data) & 0xFFFFFFFF, '08x')
        upload_headers = {
            "authorization": store_auth,
            "origin": "https://www.doubao.com",
            "reference": "https://www.doubao.com",
            "host": "tos-d-x-hl.snssdk.com",
            "content-type": "application/octet-stream",
            "content-disposition": 'attachment; filename="undefined"',
            "content-crc32": crc32
        }
        resp = await client.post(upload_url, content=file_data, headers=upload_headers)
        data = resp.json()
        if not (msg := data.get("message")) == "Success":
            return HTTPException(status_code=500, detail=f"上传消息失败 {msg}")
        # COMMIT UPLOAD
        commit_url = f"https://imagex.bytedanceapi.com/?Action=CommitImageUpload&Version=2018-08-01&ServiceId={service_id}"
        commit_payload = {"SessionKey": session_key}
        commit_headers = {
            "origin": "https://www.doubao.com",
            "referer": "https://www.doubao.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        }
        # AWS4AUTH
        commit_request = client.build_request(
            method="POST",
            url=commit_url,
            headers=commit_headers,
            json=commit_payload
        )
        auth.__call__(commit_request)
        resp = await client.send(commit_request)
        data = resp.json()
        if not (results := data.get("Result", {}).get("PluginResult", [])):
            return HTTPException(status_code=500, detail="Commit Upload 返回 PluginResult 为空")
        result = results[0]
        # RETURN ATTACHMENT
        if file_type == 1:
            return FileResponse(
                key=result.get("ImageUri"),
                name=file_name,
                md5=result.get("ImageMd5") or hashlib.md5(file_data).hexdigest(),
                size=result.get("ImageSize")
            )
        elif file_type == 2:
            return ImageResponse(
                key=result.get("ImageUri"),
                name=file_name,
                option={
                    "height": result.get("ImageHeight"),
                    "width": result.get("ImageWidth")
                }
            )


async def delete_conversation(conversation_id: str) -> tuple[bool, str]:
    # ------ URL -------
    url = "https://www.doubao.com/samantha/thread/delete?" + params
    # ------ BODY -------
    body = { "conversation_id": conversation_id}
    # ------ HEADERS -------
    headers = {
        "cookie": COOKIE,
        "origin": "https://www.doubao.com",
        "referer": "https://www.doubao.com/chat/" + conversation_id,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body) as response:
                if response.status != 200:
                    return False, f"请求状态错误: {response.status}"
        return True, ""
    except Exception as e:
        return False, f"请求失败: {str(e)}"
    
__all__ = [
    "delete_conversation",
    "chat_completion",
    "upload_file"
]