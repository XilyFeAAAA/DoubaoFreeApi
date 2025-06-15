import asyncio
import urllib.parse
from playwright.async_api import async_playwright


class DoubaoAutomator:
    
    async def capture_request(self, request):
        """捕获请求信息"""
        # 只捕获API相关的请求
        if 'https://www.doubao.com/samantha/chat/completion' in request.url:
            # 解析URL参数
            url_parts = urllib.parse.urlparse(request.url)
            query_params = dict(urllib.parse.parse_qsl(url_parts.query))
            
            # 提取所需参数
            headers = dict(request.headers)
            
            self.device_id = query_params.get('device_id')
            self.web_id = query_params.get('web_id')
            self.tea_uuid = self.web_id
            self.room_id = headers.get('referer', '').split("/", )[-1]
            self.x_flow_trace = headers.get('x-flow-trace', '')
            
            self.captured = True
    
    async def run_automation(self, message_text="你好，请介绍一下自己"):
        """运行自动化流程"""
        self.captured = False
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=False,  # 设置为True可以无头模式运行
                args=['--disable-blink-features=AutomationControlled']
            )
            
            # 创建新页面
            page = await browser.new_page()
            
            # 设置用户代理
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            # 监听请求和响应
            page.on('request', self.capture_request)
            
            try:
                # 访问豆包网站
                print("正在访问 www.doubao.com...")
                await page.goto('https://www.doubao.com', wait_until='networkidle')
                
                # 等待页面加载完成
                print("等待页面加载...")
                await page.wait_for_load_state('networkidle')
                
                input_element = await page.wait_for_selector('textarea[data-testid="chat_input_input"]', timeout=5000)
                
                if input_element:
                    # 输入文本
                    await input_element.fill(message_text)
                    
                    # 尝试按回车键发送
                    await input_element.press('Enter')
                    print("已发送消息，等待响应...")
                    
                    # 等待请求被捕获或超时
                    wait_time, max_wait_time = 0, 3
                    while not self.captured and wait_time < max_wait_time:
                        await asyncio.sleep(1)
                        wait_time += 1
                        print(f"等待请求捕获中... {wait_time}/{max_wait_time}秒")
                    
                    if self.captured:
                        print("请求已成功捕获，等待响应完成...")
                        cookies = await page.context.cookies()
                        cookie_string = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
                        self.cookie = cookie_string
                    else:
                        raise Exception(f"等待超时，未能捕获请求。请尝试增加等待时间或检查网络连接。")
                else:
                    raise Exception("未找到输入框，尝试手动查看页面结构...")
                
                
            except Exception as e:
                raise Exception(f"自动化过程中出错: {e}")
            
            finally:
                await browser.close()

            return {
                "cookie": self.cookie,
                "device_id": self.device_id,
                "tea_uuid": self.tea_uuid,
                "web_id": self.web_id,
                "room_id": self.room_id,
                "x_flow_trace": self.x_flow_trace
            }
