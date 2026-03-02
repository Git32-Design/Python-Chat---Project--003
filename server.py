# server.py

"""
NoticeInfo
---------------------------|
Project: PyChat - Server core implementation 服务端核心
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

import socket
import threading
import pickle
import sqlite3
import hashlib
import os
import random
import string
import time

# ------------------- 数据库与账户管理 -------------------
def init_db():
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS accounts
                 (username TEXT PRIMARY KEY,
                  password_hash BLOB NOT NULL,
                  two_factor_enabled INTEGER DEFAULT 0,
                  recovery_code TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def hash_password(password):
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt + key

def verify_password(stored, provided):
    salt = stored[:32]
    key = stored[32:]
    new_key = hashlib.pbkdf2_hmac('sha256', provided.encode('utf-8'), salt, 100000)
    return new_key == key

def register_account(username, password, two_factor_enabled=False):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute("SELECT username FROM accounts WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return {"success": False, "message": "用户名已存在"}
    password_hash = hash_password(password)
    recovery_code = None
    if two_factor_enabled:
        recovery_code = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    c.execute("INSERT INTO accounts (username, password_hash, two_factor_enabled, recovery_code) VALUES (?,?,?,?)",
              (username, password_hash, int(two_factor_enabled), recovery_code))
    conn.commit()
    conn.close()
    return {"success": True, "recovery_code": recovery_code}

def login_account(username, password, recovery_code=None):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute("SELECT password_hash, two_factor_enabled, recovery_code FROM accounts WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        return {"success": False, "message": "用户名或密码错误"}
    stored_hash, two_factor, stored_recovery = row
    if not verify_password(stored_hash, password):
        return {"success": False, "message": "用户名或密码错误"}
    if two_factor:
        if not recovery_code or recovery_code != stored_recovery:
            return {"success": False, "message": "需要正确的恢复码"}
    return {"success": True, "message": "登录成功", "two_factor": bool(two_factor)}

# ------------------- 服务器网络核心 -------------------
clients = []          # 所有客户端 socket 连接
clients_lock = threading.Lock()
players = {}          # player_id -> { 'x': x, 'y': y, 'skin': skin_id, 'username': str, 'emote': None, ... }
next_player_id = 0    # 用于分配新玩家ID

def broadcast(data, exclude=None):
    """向所有在线客户端广播数据"""
    with clients_lock:
        for client in clients[:]:
            if client == exclude:
                continue
            try:
                client.send(pickle.dumps(data))
            except (ConnectionResetError, BrokenPipeError):
                clients.remove(client)
            except Exception as e:
                print(f"广播错误: {e}")

def handle_client(conn, addr):
    global next_player_id
    print(f"[新连接] {addr}")
    # 分配新玩家ID
    player_id = next_player_id
    next_player_id += 1
    # 初始化该玩家的状态（未登录）
    players[player_id] = {
        'x': 100, 'y': 100,
        'skin': 0,
        'username': None,
        'logged_in': False,
        'emote': None,
        'emote_timer': 0
    }
    # 发送自己的ID给新客户端
    conn.send(pickle.dumps({"type": "init", "your_id": player_id}))
    # 然后广播所有玩家状态（让其他人知道有新玩家）
    broadcast(players)
    # 将连接加入列表
    with clients_lock:
        clients.append(conn)

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            msg = pickle.loads(data)
            msg_type = msg.get('type')

            # ---------- 移动 ----------
            if msg_type == 'move':
                players[player_id]['x'] = msg['x']
                players[player_id]['y'] = msg['y']
                broadcast(players, exclude=conn)   # 广播所有玩家状态给其他人（发送者不需要自己更新位置？但可以保留以同步其他玩家）

            # ---------- 聊天 ----------
            elif msg_type == 'chat':
                # 原样广播聊天消息（含可能的表情符号）
                broadcast(msg)

            # ---------- 注册 ----------
            elif msg_type == 'register':
                username = msg['username']
                password = msg['password']
                two_factor = msg.get('two_factor', False)
                result = register_account(username, password, two_factor)
                # 将结果返回给发送者
                response = {'type': 'register_response', 'success': result['success'], 'message': result.get('message', '')}
                if result['success'] and result.get('recovery_code'):
                    response['recovery_code'] = result['recovery_code']
                conn.send(pickle.dumps(response))

            # ---------- 登录 ----------
            elif msg['type'] == 'login':
                username = msg['username']
                password = msg['password']
                recovery = msg.get('recovery_code')
                result = login_account(username, password, recovery)
                response = {'type': 'login_response', 'success': result['success'], 'message': result.get('message', '')}
                if result['success']:
                    # 更新玩家状态
                    players[player_id]['username'] = username
                    players[player_id]['logged_in'] = True
                    # 广播给所有客户端（包含新用户名）
                    broadcast(players)
                    # 可选：广播玩家状态更新（如头顶显示名字）
                conn.send(pickle.dumps(response))

            # ---------- 皮肤切换 ----------
            elif msg_type == 'change_skin':
                new_skin = msg['skin_id']
                players[player_id]['skin'] = new_skin
                broadcast(players)   # 广播新皮肤

            # ---------- 背景切换 ----------
            elif msg_type == 'change_bg':
                # 背景切换是全局的，服务器只记录并广播
                # 假设服务器维护一个背景ID
                broadcast({'type': 'change_bg', 'bg_id': msg['bg_id']})

            # ---------- 表情触发 ----------
            elif msg_type == 'emote':
                # 玩家主动发送表情（可能通过快捷键）
                emote_id = msg['emote_id']
                players[player_id]['emote'] = emote_id
                players[player_id]['emote_timer'] = 2.0  # 持续2秒
                broadcast(players)   # 广播表情状态

            # 其他消息...

    except Exception as e:
        print(f"[错误] {addr}: {e}")
    finally:
        # 清理
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        del players[player_id]
        conn.close()
        print(f"[断开] {addr}")

def start_server(host='0.0.0.0', port=12345):
    init_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"服务器启动，监听 {host}:{port}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == '__main__':
    start_server()