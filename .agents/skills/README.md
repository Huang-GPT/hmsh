# Project-level Skills (hmsh)

本目录的 skill **只在 hmsh 项目内使用**——不是全局 skill。

## 现有 skill

### deploy-via-ssh-bat

**用途**：从 opencode agent 容器远程部署代码到 Linux 服务器。

**为什么有这个 skill**：
- opencode agent 容器调 OpenSSH 客户端会 hang（PowerShell 容器兼容性 bug）
- 14 次返工后沉淀的"唯一 100% 稳定"部署方案
- 用户跑 .bat 脚本（不是 PowerShell），脚本调 ssh.exe

**何时触发**：
- 用户说"部署到服务器""发布到阿里云""远程执行"
- 任何需要 SSH 到 Linux 服务器的场景
- **不适用**：SaaS API（用 composio-connect）、纯本地文件操作

详见 `deploy-via-ssh-bat/SKILL.md`