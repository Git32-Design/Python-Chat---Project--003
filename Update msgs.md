# 更新节点
# v1.0.0 Alpha - Initial Commit

## 初始化

### 素材

- 背景

- 表情

- 字体

- 皮肤

- 账号数据库

### 启动

1. 必须先启动`server.py`

2. 启动`client.py`，前提：对应host的PC有运行`server.py`

### 登录

1. 输入`.login`根指令

2. 填写以后的账号名和密码，需用`Space`分割

3. 如果你注册的帐号有启用2FA验证，必须在末尾添加恢复码

### 注册

1. 输入`.regist`根指令

2. 填写以后的账号名和密码，需用`Space`分割

3. 如果需要2FA，则最后徐输入启用2FA的Boolean为true，不填默认为false不启用2FA，按`Enter`提交执行后，会在桌面生成非一次性恢复码，登陆时会用到这个二次验证恢复码

### 更多信息

- 输入`.help`查看帮助

### Wiki

- 待完善Page，无Wiki

# v2.1.1 Beta - v2.1.1: Extend `Player` class metadatas and header document

## 扩展`Python`类元数据

### 数据结构追加

1. `status_hex` - 十六进制状态码

2. `health` - 健康值

3. `ping` - 延迟

4. `score` - 分数

- 还有其他

## 头部文档

### Preview

```python
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
```
# v2.1.2 Beta - Deleted developer programs, protect against tampering

## 删除

1. 删除`server.py`，因为只需`client.py`连接的主机需要server.py，更重要的是防止`server.py`这样的核心程序被修改

2. 删除了`start.bat`，因为引用了无效的脚本，现在只需运行client就行了

# v2.2.2 Beta - Include `config.ini`, startup using `python client.py <IP>`

## 配置文件

1. 添加`config.ini`配置文件以启动时配置IP

2. 启动命令可自定义连接的IP，像这样`python client.py 127.0.0.1`

# 预计: Release 1|v3.3.3 Production/Unstable - Add extension marketplace and PyChat launcher

## 扩展市场

### 数据库

1. 扩展`extension.db`数据库

2. 添加内置市场GUI

### 开发者工具

1. 可注册为开发者，使用`.devregist`指令，注册成功后会自动打开`PyChatEXtensionDev.py`

2. 开发者可使用`.devlogin`指令登录

3. 开发者工具可上传项目至PCE Marketplace

### 扩展市场GUI

1. 可使用`.market`指令打开市场GUI

2. 可正在启动器页面点击`购物袋图标`以打开PCE Marketplace

3. 启动器可扩展游戏，以后将命名为`PyGame Launcher`(PGL)

## PyChat启动器

- 两种启动方案

1. 直接运行`client.py`来启动

2. 运行`PyGameLauncher.py`

 1. 点击PyGame市场栏

 2. 点击`PyChat - 你的休闲搭子`游戏
 
 3. 进入游戏页面点击`下载`按钮进行下载

 4. 上方提示`下载完成，即可开始游戏！`后，可点击`运行`按钮来启动游戏