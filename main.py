import json
import time
import uuid
import base64
import asyncio
import logging
import os
import ssl
from typing import Dict, Any, List
from aiohttp import ClientSession, WSMsgType
from aiohttp_socks import ProxyConnector
from config import CONFIG

# 禁用SSL证书验证
ssl._create_default_https_context = ssl._create_unverified_context


my_proxy = CONFIG["my_proxy"] 
user_id = CONFIG["user_id"]


def get_application_path():
    """获取应用程序路径"""
    return os.path.dirname(os.path.abspath(__file__))


class GrassClientManager:
    def __init__(self, configs: List[Dict]):
        """
        初始化客户端管理器
        :param configs: 账号配置列表
        """
        self.configs = configs
        self.logger = self._setup_manager_logger()
        # 创建一个共享的SSL上下文
        self.ssl_context = self._create_ssl_context()

    def _setup_manager_logger(self) -> logging.Logger:
        """设置管理器日志"""
        logger = logging.getLogger('grass_manager')
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    @staticmethod
    def _create_ssl_context():
        """创建SSL上下文"""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context

    async def run(self):
        """运行所有客户端"""
        clients = [GrassClient(config, self.ssl_context) for config in self.configs]
        await asyncio.gather(*(client.connect() for client in clients))


class GrassClient:
    DIRECTOR_SERVER = "https://director.getgrass.io"
    PING_INTERVAL = 2 * 60  # 2分钟
    BASE_DELAY = 1  # 初始延迟1秒
    MAX_DELAY = 125  # 最大延迟125秒
    DEFAULT_HEADERS = {
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'none'
    }

    def __init__(self, config: Dict, ssl_context):
        self._parse_config(config)
        self.ssl_context = ssl_context
        self.logger = self._setup_logger()
        self._init_state()

    def _parse_config(self, config: Dict):
        """解析配置"""
        self.user_id = config['user_id']
        self.browser_id = config['browser_id']
        self.user_agent = config['user_agent']
        proxy_parts = config['proxy'].split(':')
        self.PROXY_HOST = proxy_parts[0]
        self.PROXY_PORT = int(proxy_parts[1])
        self.PROXY_USER = proxy_parts[2]
        self.PROXY_PASS = proxy_parts[3]

    def _init_state(self):
        """初始化状态变量"""
        self.ws = None
        self.is_connected = False
        self.last_live_timestamp = 0
        self.retries = 0
        self.current_session = None
        self.session = None
        self.reconnect_delay = 5
        self.ping_task = None

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        # 使用当前目录下的logs文件夹
        logs_dir = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)

        safe_proxy_host = self.PROXY_HOST.replace(
            ':', '_').replace('/', '_').replace('\\', '_')
        random_suffix = str(uuid.uuid4())[:8]

        logger = logging.getLogger(
            f'websocket_client_{safe_proxy_host}_{random_suffix}')
        logger.setLevel(logging.INFO)

        # 创建文件处理器
        log_file = os.path.join(
            logs_dir, f'{safe_proxy_host}_{self.PROXY_PORT}_{self.PROXY_USER}_{random_suffix}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    async def _create_session(self) -> ClientSession:
        """创建session"""
        if self.session:
            return self.session

        connector = ProxyConnector.from_url(
            f'socks5://{self.PROXY_USER}:{self.PROXY_PASS}@{self.PROXY_HOST}:{self.PROXY_PORT}',
            ssl=self.ssl_context,
            limit=5
        )
        self.session = ClientSession(connector=connector)
        return self.session

    async def authenticate(self) -> Dict:
        """认证信息"""
        return {
            "browser_id": self.browser_id,
            "user_id": self.user_id,
            "user_agent": self.user_agent,
            "timestamp": int(time.time()),
            "device_type": "extension",
            "version": "1.0.0"
        }

    async def checkin(self) -> Dict[str, Any]:
        """设备签到"""
        try:
            if not self.session:
                self.session = await self._create_session()

            data = {
                "browserId": self.browser_id,
                "deviceType": "extension",
                "extensionId": "ilehaonighjijnmpnagapkhpcdbhclfg",
                "userAgent": self.user_agent,
                "userId": self.user_id,
                "version": "5.1.1",
            }

            headers = {**self.DEFAULT_HEADERS, 'user-agent': self.user_agent}
            
            async with self.session.post(
                f"{self.DIRECTOR_SERVER}/checkin",
                json=data,
                timeout=30,
                ssl=self.ssl_context,
                headers=headers
            ) as response:
                 # 检查响应状态
                if response.status == 503:
                    print(f"grass 服务器暂时不可用(503)")
                    return None  # 返回None，让connect方法处理重试逻辑

                response.raise_for_status()

                # 检查响应类型
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type:
                    text = await response.text()
                    json_data = json.loads(text)
                    print(f"获取ip成功: {json_data['destinations'][0]}，代理可用！")
                    try:
                        return json_data
                    except json.JSONDecodeError:
                        print("无法解析响应为JSON")
                        return None

                return await response.json()

        except asyncio.TimeoutError:
            print("请求超时")
            return None
        except Exception as e:
            print(f"Checkin failed: {e}")
            return None

    async def perform_http_request(self, params: Dict) -> Dict:
        """执行HTTP请求（异步版本）"""
        HEADERS_TO_REPLACE = [
            'origin', 'referer', 'access-control-request-headers',
            'access-control-request-method', 'access-control-allow-origin',
            'cookie', 'date', 'dnt', 'trailer', 'upgrade'
        ]

        try:
            headers = params.get('headers', {})
            request_headers = {
                k.lower(): v for k, v in headers.items()
                if k.lower() in HEADERS_TO_REPLACE
            }

            body = None
            if params.get('body'):
                body = base64.b64decode(params['body'])

            async with self.session.request(
                method=params.get('method', 'GET'),
                url=params['url'],
                headers=request_headers,
                data=body,
                allow_redirects=False,
                timeout=10
            ) as response:
                content = await response.read()
                # 将响应头的key转换为小写
                response_headers = {
                    k.lower(): v for k, v in response.headers.items()}

                # 如果是重定向
                if response.status in [301, 302, 303, 307, 308]:
                    return {
                        "url": str(response.url),
                        "status": response.status,
                        "status_text": "",  # 改为空字符串
                        "headers": response_headers,
                        "body": ""
                    }

                return {
                    "url": str(response.url),
                    "status": response.status,
                    "status_text": "",  # 改为空字符串
                    "headers": response_headers,
                    "body": base64.b64encode(content).decode('utf-8')
                }

        except Exception as e:
            print(f"HTTP request error: {str(e)}")  # 添加错误详情
            return {
                "url": params.get('url'),
                "status": 400,
                "status_text": str(e),  # 添加错误信息
                "headers": {},
                "body": ""
            }

    async def send_message(self, message: Dict):
        """发送消息"""
        try:
            if self.is_connected and self.ws and not self.ws.closed:
                message_str = json.dumps(message)
                print(f"↑ 成功处理请求！")
                await self.ws.send_json(message)
        except Exception as e:
            print(f"发送消息错误: {e}")
            self.is_connected = False

    async def start_ping_loop(self):
        """异步ping循环"""
        print("开始运行发送脚本：")
        ping_count = 0
        last_ping_time = time.time()
        
        while self.is_connected:
            try:
                current_time = time.time()
                # 检查连接存活状态
                if current_time - self.last_live_timestamp > 129:
                    print(
                        f"连接似乎已断开，最后活动时间: {time.strftime('%H:%M:%S', time.localtime(self.last_live_timestamp))}, "
                        f"当前时间: {time.strftime('%H:%M:%S', time.localtime(current_time))}, "
                        f"间隔: {int(current_time - self.last_live_timestamp)}秒")
                    self.is_connected = False
                    break

                # 每120秒发送一次PING
                if current_time - last_ping_time >= self.PING_INTERVAL:
                    ping_count += 1
                    ping_message = {
                        "id": str(uuid.uuid4()),
                        "version": "1.0.0",
                        "action": "PING",
                        "data": {}
                    }
                    print(f"发送第 {ping_count} 次PING")
                    await self.send_message(ping_message)
                    last_ping_time = current_time
                    print(f"PING已发送，下次PING将在 {self.PING_INTERVAL} 秒后发送")

                await asyncio.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                print(f"Ping循环错误: {e}")
                break

        print(
            f"Ping循环结束，总共发送了 {ping_count} 次PING，"
            f"最后活动时间: {time.strftime('%H:%M:%S', time.localtime(self.last_live_timestamp))}")

    async def handle_message(self, message):
        """处理收到的消息"""
        try:
            data = json.loads(message)
            print(f"成功获取服务信息！")
            
            if data.get("action") == "HTTP_REQUEST":
                result = await self.perform_http_request(data["data"])
                
                # 检查HTTP请求的状态码
                if result["status"] != 200:
                    print(f"HTTP请求返回非200状态码: {result['status']}，准备重新连接...")
                    self.is_connected = False
                    if self.ws and not self.ws.closed:
                        await self.ws.close()  # 主动关闭WebSocket连接
                    return
                
                response = {
                    "id": data["id"],
                    "origin_action": "HTTP_REQUEST",
                    "result": result
                }
                await self.send_message(response)
            
            elif data.get("action") == "PONG":
                print("收到PONG响应")
                response = {
                    "id": data["id"],
                    "origin_action": "PONG"
                }
                await self.send_message(response)
                
        except json.JSONDecodeError:
            print(f"无效的消息格式: {message}")
        except Exception as e:
            print(f"消息处理错误: {e}")
            # 发生错误时也主动关闭连接
            self.is_connected = False
            if self.ws and not self.ws.closed:
                await self.ws.close()

    async def connect(self):
        """建立并维护WebSocket连接"""
        while True:
            try:
                if not self.session:
                    connector = ProxyConnector.from_url(
                        f'socks5://{self.PROXY_USER}:{self.PROXY_PASS}@{self.PROXY_HOST}:{self.PROXY_PORT}',
                        ssl=self.ssl_context
                    )
                    self.session = ClientSession(connector=connector)

                checkin_data = await self.checkin()
                if not checkin_data:
                    print(f"当前代理不可用，请正确配置，等待 {self.reconnect_delay} 秒后重试...")
                    await asyncio.sleep(self.reconnect_delay)
                    # 增加重连延迟，最大60秒
                    self.reconnect_delay = min(self.reconnect_delay * 2, self.MAX_DELAY)
                    continue

                ws_url = f"ws://{checkin_data['destinations'][0]}?token={checkin_data['token']}"
                print(f"正在连接到WebSocket服务器: {checkin_data['destinations'][0]}")

                async with self.session.ws_connect(
                    ws_url,
                    headers={
                        'accept': '*/*',
                        'accept-language': 'zh-CN,zh;q=0.9',
                        'cache-control': 'no-cache',
                        'content-type': 'application/json',
                        'origin': 'chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi',
                        'pragma': 'no-cache',
                        'priority': 'u=1, i',
                        'sec-fetch-dest': 'empty',
                        'sec-fetch-mode': 'cors',
                        'sec-fetch-site': 'none',
                        'user-agent': self.user_agent
                    },
                    timeout=30,
                    heartbeat=30
                ) as ws:
                    self.ws = ws
                    self.is_connected = True
                    self.last_live_timestamp = time.time()
                    self.reconnect_delay = 5
                    
                    print(f"WebSocket连接已建立 - {time.strftime('%H:%M:%S')}")

                    # 启动ping任务
                    ping_task = asyncio.create_task(self.start_ping_loop())

                    try:
                        async for msg in ws:
                            if msg.type == WSMsgType.TEXT:
                                self.last_live_timestamp = time.time()
                                await self.handle_message(msg.data)
                            elif msg.type == WSMsgType.CLOSED:
                                print(f"WebSocket连接被服务器关闭，关闭码: {ws.close_code}，原因: {ws.close_code or '未知'}")
                                break
                            elif msg.type == WSMsgType.ERROR:
                                print(f"WebSocket错误: {ws.exception() if ws.exception() else 'Unknown error'}")
                                if ws.exception():
                                    print(f"错误详情: {str(ws.exception())}")
                                break
                            elif msg.type == WSMsgType.CLOSE:
                                print(f"收到WebSocket关闭帧，关闭码: {ws.close_code}，原因: {ws.close_code or '未知'}")
                                break
                            elif msg.type == WSMsgType.CLOSING:
                                print("WebSocket正在关闭中...")
                                break
                            elif msg.type == WSMsgType.CLOSED:
                                print(f"WebSocket已关闭，关闭码: {ws.close_code}")
                                break
                    except Exception as e:
                        print(f"WebSocket消息处理错误: {e}")
                    finally:
                        close_status = f"关闭码: {ws.close_code}" if ws.close_code else "无关闭码"
                        close_code = f"原因: {ws.close_code}" if ws.close_code else "无关闭原因"
                        print(f"WebSocket连接结束 - {time.strftime('%H:%M:%S')} - {close_status} - {close_code}")
                        self.is_connected = False
                        ping_task.cancel()
                        try:
                            await ping_task
                        except asyncio.CancelledError:
                            pass

            except Exception as e:
                print(f"连接错误: {e}，等待 {self.reconnect_delay} 秒后重试...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.MAX_DELAY)

                if self.session:
                    await self.session.close()
                    self.session = None

def print_banner():
    """打印脚本启动横幅"""
    banner = """
╔════════════════════════════════════════════════════════════════╗
║                     Grass 项目自动化脚本                          
╠════════════════════════════════════════════════════════════════╣
║  脚本持续更新，当前插件版本5.1.1                                                               ║
║  说明:                                                          ║
║     grass项目脚本免费提供，免费、免费  别花钱去买了                 ║
║                                                                ║
║  注意事项:                                                       ║
║    - 该脚本需要配置代理，代理自己解决                                ║
║    -  有问题可以联系wx: mbg2024001                                                           ║
╚════════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def main():
    """主函数"""
    # 创建客户端管理器
    print_banner()
    cg = [
    {
    "user_id": user_id,
    "browser_id": "8da92b17-6ef9-5d3b-b5c4-5ee4f5c5fef7",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.71 Safari/537.36",
    "proxy": my_proxy
    },
    ]
    manager = GrassClientManager(cg)
    await manager.run()

if __name__ == "__main__":
    asyncio.run(main())
