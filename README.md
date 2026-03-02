# PyChat - 你的休闲搭子

<div align="center">

一个基于 Python 的多人在线聊天应用，支持账户管理、两步验证、实时聊天和玩家状态同步。

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/Version-v2.1.1%20Beta-orange)](Update%20msgs.md)

</div>

---

## 项目简介

PyChat 是一个基于 Python 的多人在线聊天服务器，支持基本的账户注册、登录、两步验证和消息广播功能。未来将开发基于 GUI 的 "PyChat Launcher" 和扩展市场。

### 主要特性

- **账户管理** - 注册、登录、两步验证（可选）、密码安全存储、账户恢复
- **实时聊天** - 支持文本消息和表情符号，消息广播给所有在线用户
- **玩家状态** - 每个玩家有位置、皮肤、表情状态等属性，服务器维护并同步这些状态
- **服务器性能** - 使用多线程处理多个客户端连接，确保响应速度和稳定性
- **数据安全** - 使用 SQLite 数据库存储账户信息，密码使用哈希和盐进行安全存储
- **可扩展性** - 服务器设计为模块化，便于未来添加更多功能
- **Host 处理** - 服务器自动选择可用 IP 地址作为 Host，并广播给所有客户端

---

## 快速开始

### 环境要求

- Python 3.8 或更高版本

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/Git32-Design/Python-Chat.git
cd "Python Chat - Project #003"
```

2. （可选）安装依赖
```bash
pip install -r requirements.txt
```

### 启动方式

#### 方式一：使用启动脚本（推荐）

Windows 用户直接运行：
```bash
Start.bat
```

脚本会自动启动服务器和客户端。

#### 方式二：手动启动

1. 首先启动服务器
```bash
python server.py
```

2. 然后在新的终端启动客户端
```bash
python client.py
```

---

## 使用指南

### 注册账号

输入 `.regist` 指令，按提示输入：
```
.regist 用户名 密码 [启用2FA]
```
- 如需启用两步验证，在末尾添加 `true`
- 启用 2FA 后会在桌面生成恢复码，登录时需要使用

### 登录

输入 `.login` 指令，按提示输入：
```
.login 用户名 密码 [恢复码]
```
- 如果启用了 2FA，必须在末尾添加恢复码

### 聊天

登录成功后，直接输入消息即可发送给所有在线用户。

### 查看帮助

输入 `.help` 查看所有可用指令。

---

## 项目结构

```
PyChat - Project #003/
├── server.py              # 服务器核心
├── client.py              # 客户端核心
├── Start.bat              # 启动脚本
├── accounts.db            # 账号数据库
├── backgrounds/           # 背景素材
├── emotes/              # 表情素材
├── fonts/               # 字体文件
├── skins/               # 角色皮肤
├── tests/               # 测试文件
├── Update msgs.md       # 更新日志
└── README.md            # 项目说明
```

---

## 更新日志

### v2.1.1 Beta (2026-03-02)
- 扩展 `Player` 类元数据（状态码、健康值、延迟、分数等）
- 添加头部文档说明

### v1.0.0 Alpha (2026-02-26)
- 初始版本发布
- 基础聊天功能
- 账户注册与登录
- 两步验证支持

### 预计：v3.2.1 Production
- 扩展市场功能
- PyChat Launcher 启动器
- PyGame Launcher 集成

查看完整更新日志：[Update msgs.md](Update%20msgs.md)

---

## 团队贡献

| 角色 | 贡献者 | 职责 |
|------|--------|------|
| 素材设计 | Git32-Design | 使用 Pixilart 工具绘制素材 |
| 代码设计 | Tencent Cloud CodeBuddy | 使用 Tencent Cloud CodeBuddy 工具编写 |
| 代码实现 | ChatGPT-5 (GitHub Copilot) | 辅助编写与修复代码 |

---

## 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 未来规划

- [ ] PyChat Launcher 图形界面
- [ ] 扩展市场 (PCE Marketplace)
- [ ] 开发者工具
- [ ] PyGame Launcher 集成
- [ ] 好友系统
- [ ] 私聊功能
- [ ] 游戏内活动

---

## 联系我们

如有问题或建议，欢迎提交 Issue 或 Pull Request！

<div align="center">

**Made with ❤️ by Git32-Design & Team**

</div>
