# Agent 操作规则（给本环境 AI agent）

## 环境边界

- 本 agent 跑在 opencode 容器/沙箱里，**无法 SSH 到任何服务器**
- **无法直接执行 PowerShell/cmd**：所有 `bash` 工具调用在 Linux 容器内
- 唯一可用通道：本地文件读写 (`read`/`write`/`edit`) + `bash` 跑本地命令（git、grep、npm、python、docker 仅限本地守护进程）
- 远程服务器操作（scp + 服务器终端命令）**100% 由用户执行**

## 当前工作流（用户真实使用方式）

**用户在阿里云 ECS 控制台用 VNC 远程终端操作服务器**（不是通过本地 SSH 转发）。

- ❌ **禁止**输出 `ssh root@... "..."` 这种命令（用户本地 SSH 不通）
- ✅ 服务器命令按 **「在服务器终端直接敲」** 格式输出（用户从 VNC 输入框粘过去执行）

## 输出脚本规范

**任何涉及服务器操作的命令，必须显式标注：**

```
=== 🖥️ 本地操作（你在本地 PowerShell 跑） ===
scp 本地文件  服务器路径

=== 🖥️ 服务器操作（你在阿里云 VNC 终端敲，或复制粘贴） ===
cd /path/to/project
docker compose up -d --force-recreate xxx

=== 📱 手机/浏览器操作（你在浏览器/手机上点） ===
http://...
```

**禁止**：
- ❌ 输出 `ssh root@... "..."`（用户本地无法 SSH 出去）
- ❌ 把服务器命令混在本 agent 的执行步骤里
- ❌ 用 `&&` 把本地+服务器操作串成一个看似一锅端的脚本

**服务器脚本文件**：
- 放在 `scripts/server/` 子目录（不是 `scripts/`）
- 文件名后缀 `_server.sh` 或 `_server.ps1`
- `scripts/server/README.md` 必须说明每个脚本的用法 + 服务器 VNC 终端入口

## git 操作

- 本 agent 可用：commit、status、log、diff、branch、stash（**仅本地仓库**）
- 本 agent **不能**：push、fetch、pull（除非有配好的 SSH key，且用户明确同意）
- 远程操作明确交给用户：scp 上传 + 服务器 git pull

## 当前项目的关键事实

- 服务器：root@39.106.217.235（Aliyun ECS），Aliyun Linux
- 项目根：**`/hongmen-after-sales/`**（不是 `/root/hongmen-after-sales/`）
- 部署模式：`docker compose`（不是裸跑）
- 前端 Dockerfile 是**多阶段**：builder 跑 `npm run build`，再 COPY dist 到 nginx
- **前端 build 失败时 dist 不存在**，`/usr/share/nginx/html/js/` 是空的
- vue-cli 4 + vant@2.12 + 自带 input type="date"

## 验证闭环纪律

每次"部署完成"必须给用户**具体的验证命令**，让用户跑完反馈结果：
```bash
# 服务器侧（用户跑）
ssh root@39.106.217.235 "<检查命令>"

# 客户端（用户跑）
http://<域名>:<端口>/<路径>?<破缓存参数>
```

**禁止**：说"部署完了"而不给可验证命令 — 这是自嗨。

## 已知 PUA 教训（来自本项目历史）

1. **别假设 SSH 通** — 验证过不通，要永远走"用户执行"路径
2. **别只 `docker compose build` 不 `--force-recreate`** — 旧镜像还跑着，新代码进不去
3. **改代码前先看 build 输出有没有进 dist** — `grep -c "关键词" dist/js/app.*.js`
4. **Vant 2 vs 3 区别** — `v-model:show` 是 Vant 3 语法，Vant 2 用 `value` prop
5. **HTML5 `<input type="date">` 在 Vant 2 是稳的** — 别瞎套 van-calendar
6. **判据一定要匹配 Vue 编译产物** — Vue 把 `type="date"` 编译成 `type:"date"`（冒号），不是 `type="date"`（等号）。**grep 源码用等号，grep dist 用冒号**，否则永远"看不到"实际产物。HTML 里写等号，编译后变冒号 —— 这是 webpack/JS 对象的固有规则。
7. **判据用 ≥2 个独立匹配** — 一个匹配可能是巧合，至少要两个才能确认：
   - 字段名（如 `appointment_date`）出现次数
   - 独有标记（如 `minDateStr`）出现次数
   - 旧代码标记（如 `van-calendar`、`apptMode`）出现次数（应为 0）
   - 这三个 grep 一起，对应"代码改动 + 旧代码已清"两个维度
8. **PowerShell 文件读取要用 `-Encoding UTF8`** — 默认 UTF-16，会让中文乱码、`IndexOf` 也匹配不到。Linux 服务器 grep 默认 UTF-8，没这问题。