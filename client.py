# client.py

"""
NoticeInfo
---------------------------|
Project: PyChat - Client core implementation 客户端核心
Author: ChatGPT/Tencent Cloud CodeBuddy/Git32-Design
Description:
这是一个基于Python的多人在线聊天服务器，支持基本的账户注册、登录、两步验证和消息广播功能。以后会开发出基于GUI的“PyChat Launcher”，现以Batch语言实现server和client先后执行。
Created: 2026-02-26
Latest update: 2026-03-02
License: MIT License
Features:
- 账户管理：注册、登录、两步验证（可选）、密码安全存储、账户恢复
- 实时聊天：支持文本消息和表情符号，消息广播给所有在线用户
- 玩家状态：每个玩家有位置、皮肤、表情状态等属性，服务器维护并同步这些状态
- 服务器性能：使用多线程处理多个客户端连接，确保响应速度和稳定性
- 数据安全：使用SQLite数据库存储账户信息，密码使用哈希和盐进行安全存储，防止泄露风险
- 可扩展性：服务器设计为模块化，便于未来添加更多功能（如好友系统、私聊、游戏内活动等）
- Host处理：服务器会自动选择一个可用的IP地址作为Host，并广播给所有客户端。以Client配置连接IP地址
Main Designs:
Git32-Design - 素材设计，使用Pixilart工具绘制
TC Codebuddy - 代码设计，使用Tencent Cloud CodeBuddy工具编写
Copilot(ChatGPT-5) - 代码实现，使用GitHub Copilot（基于ChatGPT-5）辅助编写与修复
======
OnlineInfo
---------------------------|
Access: 0 Users
Stars: 0 Stars
Commits: 99.09%
"""

import pygame
import socket
import threading
import pickle
import os
import sys
import time
from typing import Optional, Dict, Any, List

# ----------------- 前置配置 ------------------
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ------------------- 配置 -------------------
SERVER_HOST = '192.168.1.104'
SERVER_PORT = 12345
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
FPS = 60
PLAYER_SPEED = 5
EMOTE_DURATION = 2.0

# ------------------- 资源加载 -------------------
def load_images():
    skins = [pygame.image.load(f'skins/skin_{i}.png') for i in range(3)]
    backgrounds = [pygame.image.load(f'backgrounds/bg_{i}.png') for i in range(2)]
    emotes = {i: pygame.image.load(f'emotes/emote_{i}.png') for i in range(5)}
    return skins, backgrounds, emotes

# ------------------- 混合字体渲染函数 -------------------
def render_mixed_text(text, font_en, font_cn, color=(255,255,255)):
    """
    渲染混合英文和中文的文本。
    text: 要渲染的字符串
    font_en: 英文字体（如 Fira Code）
    font_cn: 中文字体（如 MS YaHei）
    color: 文字颜色
    返回一个包含整个文本的 Surface
    """
    def is_chinese(ch):
        return '\u4e00' <= ch <= '\u9fff'  # 常用汉字范围

    segments = []
    if not text:
        return pygame.Surface((0,0))

    current_seg = ""
    current_font = font_cn if is_chinese(text[0]) else font_en

    for ch in text:
        if (is_chinese(ch) and current_font is font_cn) or (not is_chinese(ch) and current_font is font_en):
            current_seg += ch
        else:
            segments.append((current_seg, current_font))
            current_seg = ch
            current_font = font_cn if is_chinese(ch) else font_en
    if current_seg:
        segments.append((current_seg, current_font))

    surfaces = []
    total_width = 0
    max_height = 0
    for seg_text, font in segments:
        surf = font.render(seg_text, True, color)
        surfaces.append(surf)
        total_width += surf.get_width()
        max_height = max(max_height, surf.get_height())

    result = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
    x_offset = 0
    for surf in surfaces:
        result.blit(surf, (x_offset, 0))
        x_offset += surf.get_width()
    return result

# ------------------- 玩家类 -------------------
# Please extend player information to hex status code and more attributes in the future.
class Player:
    """玩家数据结构：
    - 增强了状态字段（status_hex）和常见属性（health, score, ping 等）
    - 提供 to_dict 和 update_from_dict 便于网络序列化/更新
    """
    def __init__(
        self,
        pid: int,
        x: float,
        y: float,
        skin_id: int,
        username: Optional[str] = None,
        logged_in: bool = False,
        status_hex: str = "0x0",
        health: int = 100,
        max_health: int = 100,
        score: int = 0,
        ping_ms: int = 0,
        status_flags: Optional[Dict[str, bool]] = None,
        inventory: Optional[List[Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[float] = None,
        last_seen: Optional[float] = None,
        is_admin: bool = False,
    ):
        self.id = pid
        self.x = x
        self.y = y
        self.skin_id = skin_id

        # 认证/显示信息
        self.username = username
        self.logged_in = logged_in

        # 状态（用于快速以十六进制或位掩码表示复合状态）
        self.status_hex = status_hex

        # 生存/分数/延迟等
        self.health = health
        self.max_health = max_health
        self.score = score
        self.ping_ms = ping_ms

        # 可扩展的标志和物品/元数据
        self.status_flags: Dict[str, bool] = status_flags or {}
        self.inventory: List[Any] = inventory or []
        self.metadata: Dict[str, Any] = metadata or {}

        # 时间戳
        self.created_at = created_at if created_at is not None else time.time()
        self.last_seen = last_seen if last_seen is not None else time.time()

        # 权限
        self.is_admin = is_admin

        # 表情相关（原有字段，保留）
        self.current_emote = None
        self.emote_timer = 0

    def update_emote(self, dt: float):
        if self.current_emote is not None:
            self.emote_timer -= dt
            if self.emote_timer <= 0:
                self.current_emote = None

    def to_dict(self) -> Dict[str, Any]:
        """将玩家数据导出为字典，便于网络传输或调试。"""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'skin': self.skin_id,
            'username': self.username,
            'logged_in': self.logged_in,
            'emote': self.current_emote,
            'emote_timer': self.emote_timer,
            'status_hex': self.status_hex,
            'health': self.health,
            'max_health': self.max_health,
            'score': self.score,
            'ping_ms': self.ping_ms,
            'status_flags': self.status_flags,
            'inventory': self.inventory,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'last_seen': self.last_seen,
            'is_admin': self.is_admin,
        }

    def update_from_dict(self, pdata: Dict[str, Any]):
        """从服务器/字典更新玩家字段：
        - 接受服务器的命名（例如 'skin'）并进行映射到本地属性
        - 只更新已知字段，其余保存在 metadata 中
        """
        # 基本位置/外观
        if 'x' in pdata:
            self.x = pdata['x']
        if 'y' in pdata:
            self.y = pdata['y']
        if 'skin' in pdata:
            self.skin_id = pdata['skin']

        # 标识/登录
        if 'username' in pdata:
            self.username = pdata.get('username')
        if 'logged_in' in pdata:
            self.logged_in = pdata.get('logged_in', self.logged_in)

        # 表情
        if 'emote' in pdata:
            self.current_emote = pdata.get('emote')
        if 'emote_timer' in pdata:
            self.emote_timer = pdata.get('emote_timer', self.emote_timer)

        # 增强属性
        if 'status_hex' in pdata:
            self.status_hex = pdata['status_hex']
        if 'health' in pdata:
            self.health = pdata['health']
        if 'max_health' in pdata:
            self.max_health = pdata['max_health']
        if 'score' in pdata:
            self.score = pdata['score']
        if 'ping_ms' in pdata:
            self.ping_ms = pdata['ping_ms']
        if 'status_flags' in pdata and isinstance(pdata['status_flags'], dict):
            # 合并/覆盖标志
            self.status_flags.update(pdata['status_flags'])
        if 'inventory' in pdata and isinstance(pdata['inventory'], list):
            self.inventory = pdata['inventory']
        if 'metadata' in pdata and isinstance(pdata['metadata'], dict):
            self.metadata.update(pdata['metadata'])
        if 'is_admin' in pdata:
            self.is_admin = pdata['is_admin']

        # 更新时间戳（如果服务器提供）
        if 'last_seen' in pdata:
            self.last_seen = pdata['last_seen']

    def set_status_flag(self, name: str, value: bool = True):
        self.status_flags[name] = value

    def clear_status_flag(self, name: str):
        if name in self.status_flags:
            del self.status_flags[name]

# ------------------- 摄像机类 -------------------
class Camera:
    def __init__(self, width, height):
        self.offset_x = 0
        self.offset_y = 0
        self.mode = 'follow'
        self.target = None
        self.width = width
        self.height = height
        self.zoom = 1.0

    def update(self, target_player, all_players, map_width, map_height):
        if self.mode == 'follow' and target_player:
            # 考虑缩放：世界坐标缩放后，摄像机应跟随目标位置
            self.offset_x = target_player.x * self.zoom - self.width // 2
            self.offset_y = target_player.y * self.zoom - self.height // 2
        elif self.mode == 'global':
            self.offset_x = 0
            self.offset_y = 0
        # 限制偏移量，防止超出缩放后的地图范围
        self.offset_x = max(0, min(self.offset_x, map_width * self.zoom - self.width))
        self.offset_y = max(0, min(self.offset_y, map_height * self.zoom - self.height))

# ------------------- 聊天输入框类 -------------------
class ChatInput:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.active = False
        self.font = pygame.font.Font(None, 24)  # 临时默认字体

        # 加载字体
        base_dir = os.path.dirname(__file__)
        font_en_path = os.path.join(base_dir, 'fonts', 'FiraCode-Bold.ttf')
        font_cn_path = os.path.join(base_dir, 'fonts', 'msyh.ttf')  # 或其他中文字体

        if os.path.exists(font_en_path):
            self.font_en = pygame.font.Font(font_en_path, 24)
        else:
            self.font_en = pygame.font.Font(None, 24)  # 默认字体

        if os.path.exists(font_cn_path):
            self.font_cn = pygame.font.Font(font_cn_path, 24)
        else:
            self.font_cn = pygame.font.Font(None, 24)  # 默认字体

    def handle_event(self, event):
        if not self.active:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                text = self.text
                self.text = ""
                print(f"[DEBUG] 回车，提交文本: '{text}'")
                return text
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                print(f"[DEBUG] 退格，当前文本: '{self.text}'")
            # Ctrl+C 复制
            elif event.key == pygame.K_c and (event.mod & pygame.KMOD_CTRL):
                pygame.scrap.init()
                pygame.scrap.put(pygame.SCRAP_TEXT, self.text.encode('utf-8'))
                print(f"[DEBUG] 已复制: '{self.text}'")
            # Ctrl+V 粘贴
            elif event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL):
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    root.withdraw()
                    clipboard = root.clipboard_get()
                    root.destroy()
                    self.text += clipboard
                    print(f"[DEBUG] 已粘贴: '{clipboard}'")
                except:
                    print("[DEBUG] 粘贴失败")
            # 其他功能键忽略
        elif event.type == pygame.TEXTINPUT and self.active:
            self.text += event.text
            print(f"[DEBUG] TEXTINPUT: '{event.text}'，当前文本: '{self.text}'")
        return None

    def draw(self, screen):
        color = (0, 255, 0) if self.active else (200, 200, 200)
        pygame.draw.rect(screen, color, self.rect, 2)

        # 使用混合字体渲染文本
        text_surf = render_mixed_text(self.text, self.font_en, self.font_cn)
        screen.blit(text_surf, (self.rect.x + 5, self.rect.y + 5))

# ------------------- 聊天历史类 -------------------
class ChatHistory:
    def __init__(self, x, y, width, height, max_messages=100):
        self.rect = pygame.Rect(x, y, width, height)
        self.messages = []
        self.max_messages = max_messages
        self.text = ""
        self.active = False
        self.font = pygame.font.Font(None, 20)

        # 加载字体
        base_dir = os.path.dirname(__file__)
        font_en_path = os.path.join(base_dir, 'fonts', 'FiraCode-Bold.ttf')
        font_cn_path = os.path.join("C:\\Windows\\", 'fonts', 'msyh.ttc')  # 或其他中文字体
        if os.path.exists(font_en_path):
            self.font_en = pygame.font.Font(font_en_path, 24)
            print(f"[DEBUG] 英文字体加载成功: {font_en_path}")
        else:
            self.font_en = pygame.font.Font(None, 24)  # 默认字体
            print(f"[DEBUG] 英文字体加载失败，使用默认字体: {font_en_path}")

        if os.path.exists(font_cn_path):
            self.font_cn = pygame.font.Font(font_cn_path, 24)
            print(f"[DEBUG] 中文字体加载成功: {font_cn_path}")
        else:
            self.font_cn = pygame.font.Font(None, 24)  # 默认字体
            print(f"[DEBUG] 中文字体加载失败，使用默认字体: {font_cn_path}")

    def add_message(self, username, text):
        self.messages.append((username, text))
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def draw(self, screen):
        y_offset = self.rect.bottom - 10
        for username, text in reversed(self.messages):
            display_text = f"{username}: {text}"
            # 使用混合字体渲染
            text_surf = render_mixed_text(display_text, self.font_en, self.font_cn)
            y_offset -= text_surf.get_height() + 2
            if y_offset < self.rect.top:
                break
            screen.blit(text_surf, (self.rect.x + 5, y_offset))

# ------------------- 客户端主类 -------------------
class GameClient:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Python Chat ———— 你的Python休闲搭子")
        self.clock = pygame.time.Clock()
        self.running = True

        # 网络
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server()

        # 资源
        self.skins, self.backgrounds, self.emotes = load_images()
        self.current_bg_id = 0

        # 游戏状态
        self.local_player = None
        self.local_player_id = None
        self.players = {}
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.map_width = 2000
        self.map_height = 2000

        # UI
        self.chat_input = ChatInput(10, SCREEN_HEIGHT-40, 400, 30)
        self.chat_history = ChatHistory(10, SCREEN_HEIGHT-300, 400, 250)

        # 启动接收线程
        self.recv_thread = threading.Thread(target=self.receive_loop)
        self.recv_thread.daemon = True
        self.recv_thread.start()

        # 表情快捷映射
        self.emote_map = {
            ":]": 0,
            ":D": 1,
            ":O": 2,
            ":(": 3,
            ";]": 4,
        }
        print(f"背景数量: {len(self.backgrounds)}")
        pygame.key.start_text_input()  # 启用系统输入法

    def connect_to_server(self):
        try:
            self.sock.connect((SERVER_HOST, SERVER_PORT))
            print("已连接到服务器")
        except Exception as e:
            print("无法连接到服务器:", e)
            sys.exit(1)

    def send(self, data):
        try:
            self.sock.send(pickle.dumps(data))
            print(f"[DEBUG] 发送消息: {data}")  # 调试输出
        except Exception as e:
            print("发送失败:", e)

    def receive_loop(self):
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                msg = pickle.loads(data)
                print(f"[DEBUG] 收到消息: {msg}")  # 调试输出

                if isinstance(msg, dict) and 'type' not in msg:
                    self.update_players_from_dict(msg)
                elif msg.get('type') == 'init':
                    self.local_player_id = msg['your_id']
                    print(f"我的ID是 {self.local_player_id}")
                elif msg.get('type') == 'chat':
                    self.chat_history.add_message(msg['username'], msg['text'])
                    self.trigger_emote_from_text(msg['player_id'], msg['text'])
                elif msg.get('type') == 'register_response':
                    self.handle_register_response(msg)
                elif msg.get('type') == 'login_response':
                    self.handle_login_response(msg)
                elif msg.get('type') == 'change_bg':
                    self.current_bg_id = msg['bg_id']
            except Exception as e:
                print("接收错误:", e)
                break

    def update_players_from_dict(self, players_dict):
        for pid, pdata in players_dict.items():
            if pid not in self.players:
                # 只提供最小构造参数，随后统一更新以处理新字段
                self.players[pid] = Player(pid, pdata.get('x', 0), pdata.get('y', 0), pdata.get('skin', 0))

            # 使用统一方法从字典更新玩家属性（包括新加的字段）
            try:
                self.players[pid].update_from_dict(pdata)
            except Exception as e:
                # 出错时回退到逐个设置以保证兼容性
                print(f"更新玩家 {pid} 时出错，回退并记录错误: {e}")
                self.players[pid].x = pdata.get('x', self.players[pid].x)
                self.players[pid].y = pdata.get('y', self.players[pid].y)
                self.players[pid].skin_id = pdata.get('skin', self.players[pid].skin_id)
                self.players[pid].username = pdata.get('username')
                self.players[pid].logged_in = pdata.get('logged_in', False)
                self.players[pid].current_emote = pdata.get('emote')
                self.players[pid].emote_timer = pdata.get('emote_timer', 0)

            if pid == self.local_player_id:
                self.local_player = self.players[pid]

    def trigger_emote_from_text(self, player_id, text):
        for symbol, emote_id in self.emote_map.items():
            if symbol in text:
                if player_id in self.players:
                    self.players[player_id].current_emote = emote_id
                    self.players[player_id].emote_timer = EMOTE_DURATION
                break

    def handle_register_response(self, msg):
        if msg['success']:
            if msg.get('recovery_code'):
                self.save_recovery_code(msg['recovery_code'])
                self.chat_history.add_message("系统", "注册成功！2FA恢复码已保存到桌面。")
            else:
                self.chat_history.add_message("系统", "注册成功！")
        else:
            self.chat_history.add_message("系统", f"注册失败：{msg['message']}")

    def save_recovery_code(self, code):
        import ctypes
        # 获取Windows系统真实的桌面路径
        try:
            from ctypes import wintypes
            CSIDL_DESKTOP = 0
            SHGFP_TYPE_CURRENT = 0
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_DESKTOP, 0, SHGFP_TYPE_CURRENT, buf)
            desktop = buf.value
        except:
            # 降级方案：使用环境变量
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        
        if not os.path.exists(desktop):
            desktop = os.path.expanduser("~")
        
        filename = f"2FA_Code_{int(time.time())}.txt"
        filepath = os.path.join(desktop, filename)
        with open(filepath, 'w') as f:
            f.write(f"Recovery Code: {code}\n")
            f.write("请妥善保管此恢复码，登录时需要提供。\n")

    def handle_login_response(self, msg):
        if msg['success']:
            if self.local_player:
                self.local_player.logged_in = True
            self.chat_history.add_message("系统", "登录成功！")
        else:
            self.chat_history.add_message("系统", f"登录失败：{msg['message']}")

    def process_command(self, text):
        if text.startswith(".regist "):
            parts = text.split()
            if len(parts) < 3:
                self.chat_history.add_message("系统", "格式错误：.regist <用户名> <密码> [是否启用2FA:true/false]")
                return True
            username = parts[1]
            password = parts[2]
            two_factor = False
            if len(parts) >= 4:
                two_factor = parts[3].lower() == 'true'
            self.send({"type": "register", "username": username, "password": password, "two_factor": two_factor})
            self.chat_history.add_message("系统", f"注册请求已发送，请等待响应...")
            return True

        elif text.startswith(".login "):
            parts = text.split()
            if len(parts) < 3:
                self.chat_history.add_message("系统", "格式错误：.login <用户名> <密码> [恢复码]")
                return True
            username = parts[1]
            password = parts[2]
            recovery = parts[3] if len(parts) >= 4 else None
            self.send({"type": "login", "username": username, "password": password, "recovery_code": recovery})
            self.chat_history.add_message("系统", f"登录请求已发送，请等待响应...")
            return True
        elif text.startswith(".help"):
            self.chat_history.add_message("系统", "命令列表：.regist <用户名> <密码> [true/false] - 注册账号（可选2FA）")
            self.chat_history.add_message("系统", "         .login <用户名> <密码> [恢复码] - 登录账号（如果启用2FA需要恢复码）")
            self.chat_history.add_message("系统", "         .help - 显示此帮助信息")
            self.chat_history.add_message("系统", "快捷键：F1跟随视角，F2全局视角，F3自由视角，1-3切换皮肤，B切换背景，F5-F9触发表情")
            self.chat_history.add_message("系统", "此程序还未完善，画风简陋，功能有限，更多功能敬请期待！此程序适合电脑课与同学交流和互动，已发布Github以便同学下载，欢迎提出Issues以便完善！电脑课不建议启用2FA状态码qwq")
            return True
        return False

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                # 鼠标点击激活输入框
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.chat_input.rect.collidepoint(event.pos):
                        self.chat_input.active = True
                    else:
                        self.chat_input.active = False

                # 处理输入框（只调用一次）
                result = self.chat_input.handle_event(event)
                if result is not None:
                    print(f"[DEBUG] 主循环收到结果: '{result}'")
                    if not self.process_command(result):
                        if self.local_player:
                            self.send({"type": "chat",
                                       "player_id": self.local_player.id,
                                       "username": self.local_player.username or "游客",
                                       "text": result})
                        else:
                            print("[DEBUG] local_player 为 None，无法发送聊天消息")
                            self.chat_history.add_message("系统", "请先等待角色出现或登录后再发送聊天消息")

                # 快捷键（不影响输入）
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1:
                        self.camera.mode = 'follow'
                    elif event.key == pygame.K_F2:
                        self.camera.mode = 'global'
                    elif event.key == pygame.K_F3:
                        self.camera.mode = 'free'
                    elif event.key == pygame.K_1:
                        self.send({"type": "change_skin", "skin_id": 0})
                    elif event.key == pygame.K_2:
                        self.send({"type": "change_skin", "skin_id": 1})
                    elif event.key == pygame.K_3:
                        self.send({"type": "change_skin", "skin_id": 2})
                    elif event.key == pygame.K_F5:
                        self.send({"type": "emote", "emote_id": 0})
                    elif event.key == pygame.K_F6:
                        self.send({"type": "emote", "emote_id": 1})
                    elif event.key == pygame.K_F7:
                        self.send({"type": "emote", "emote_id": 2})
                    elif event.key == pygame.K_F8:
                        self.send({"type": "emote", "emote_id": 3})
                    elif event.key == pygame.K_F9:
                        self.send({"type": "emote", "emote_id": 4})
                        
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_EQUALS:   # = 键或 + 键（可能需要 shift）
                            self.camera.zoom = min(2.0, self.camera.zoom + 0.1)
                        elif event.key == pygame.K_MINUS:  # - 键
                            self.camera.zoom = max(0.5, self.camera.zoom - 0.1)
                        elif event.key == pygame.K_b:
                            new_bg = (self.current_bg_id + 1) % len(self.backgrounds)
                            self.send({"type": "change_bg", "bg_id": new_bg})
            # 本地玩家移动
            if self.local_player:
                keys = pygame.key.get_pressed()
                dx = dy = 0
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    dx = -PLAYER_SPEED
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    dx = PLAYER_SPEED
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    dy = -PLAYER_SPEED
                if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    dy = PLAYER_SPEED
                if dx != 0 or dy != 0:
                    self.local_player.x += dx
                    self.local_player.y += dy
                    self.local_player.x = max(0, min(self.local_player.x, self.map_width - 32))
                    self.local_player.y = max(0, min(self.local_player.y, self.map_height - 32))
                    self.send({"type": "move", "id": self.local_player.id,
                               "x": self.local_player.x, "y": self.local_player.y})

            # 更新表情
            for player in self.players.values():
                player.update_emote(dt)

            # 更新摄像机
            if self.local_player:
                self.camera.update(self.local_player, self.players, self.map_width, self.map_height)

            # 渲染
            # 获取缩放后的背景表面（可以缓存以提高性能）
            bg = self.backgrounds[self.current_bg_id]
            # 缩放背景到当前地图大小乘以缩放因子
            scaled_bg = pygame.transform.scale(bg, (int(self.map_width * self.camera.zoom), int(self.map_height * self.camera.zoom)))
            # 截取摄像机视野部分
            self.screen.blit(scaled_bg, (0, 0), (self.camera.offset_x, self.camera.offset_y, SCREEN_WIDTH, SCREEN_HEIGHT))

            for player in self.players.values():
                screen_x = player.x - self.camera.offset_x
                screen_y = player.y - self.camera.offset_y
                skin_img = self.skins[player.skin_id]
                self.screen.blit(skin_img, (screen_x, screen_y))
                
                if player.username:
                    # 区分本地玩家和其他玩家的名字
                    is_local_player = (player.id == self.local_player_id)
                    font_size = 28 if is_local_player else 24
                    font = pygame.font.Font(None, font_size)
                    
                    # 本地玩家使用特殊颜色（亮粉色），其他玩家使用黄色
                    name_color = (255, 105, 180) if is_local_player else (255, 255, 0)
                    name_surf = font.render(player.username, True, name_color)
                    
                    # 计算居中位置
                    name_x = screen_x + 16 - name_surf.get_width() // 2
                    name_y = screen_y - 30 if player.current_emote is None else screen_y - 55
                    
                    # 简化描边：只绘制4个方向的黑色描边（减少渲染次数）
                    outline_color = (0, 0, 0)
                    for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        outline_surf = font.render(player.username, True, outline_color)
                        self.screen.blit(outline_surf, (name_x + ox, name_y + oy))
                    
                    # 绘制名字
                    self.screen.blit(name_surf, (name_x, name_y))
                if player.current_emote is not None:
                    emote_img = self.emotes[player.current_emote]
                    emote_rect = emote_img.get_rect(center=(screen_x + 16, screen_y - 40))
                    self.screen.blit(emote_img, emote_rect)

            self.chat_input.draw(self.screen)
            self.chat_history.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        self.sock.close()

if __name__ == '__main__':
    client = GameClient()
    client.run()