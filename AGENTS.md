# Agent 操作规则（给本环境 AI agent）

## 环境边界

- 本 agent 跑在 opencode 容器/沙箱里（Linux 子系统），但**有公网出站**（已验证可达 `39.106.217.235:22`）
- **Windows PowerShell 仍可用**（用户当前电脑，`C:\hmsh` 是工作目录）
- 本地能力：文件读写 + bash/PowerShell 跑本地命令（git、grep、npm、python、docker 仅限本地守护进程）
- **服务器能力**：agent 可直接 SSH 到 `root@39.106.217.235`（端口 22，私钥 `~/.ssh/magic.pem`），执行任意 Linux 命令
  - 私钥由用户提供，agent 不会传出去
  - **禁止**未经确认就跑破坏性命令：`rm -rf`、`dd`、`fdisk`、`mkfs`、对生产 DB 的 `DROP`/`DELETE` 全表、强制 `docker system prune` 等

## 当前工作流

**Agent 直接 SSH 到服务器执行**（不再需要用户从 VNC 粘命令）。

- ✅ Agent 直接 `ssh -i ~/.ssh/magic.pem root@39.106.217.235 "<cmd>"` 跑服务器命令
- 用户只在浏览器/手机上点东西时参与（如手动验证、清缓存）
- 唯一例外：用户在 ECS 控制台的强制重启、网络配置等需要人工授权的动作，仍由用户操作

## 输出脚本规范

**本地 vs 服务器 vs 客户端三类操作，要清晰标注**：

```
=== 🖥️ 本地操作（agent 在本地 PowerShell/bash 跑） ===
git status -sb

=== 🖥️ 远程执行（agent 已 SSH 到服务器） ===
ssh -i ~/.ssh/magic.pem root@39.106.217.235 "docker ps --format 'table {{.Names}}	{{.Status}}'"

=== 📱 手机/浏览器操作（用户在浏览器/手机上点） ===
http://magic666.cn:18080/product/repair?v=2
```

**禁止**：
- ❌ 把 `ssh ...` 写在 agent 自己的执行步骤里**不说明是远程执行**（用户会以为是本地命令）
- ❌ 用 `&&` 把本地 + 服务器命令串成一个看似一锅端的脚本（隐藏了「远程」这步的事实）
- ❌ 跑破坏性命令不打招呼（见环境边界）

**服务器脚本文件**：
- 不再单独放在 `scripts/server/`
- 如果有需要重复执行的服务器脚本（如一键部署），放在仓库根 `scripts/` 即可
- 文件名仍建议带 `_server` 后缀，方便区分

## git 操作

- 本地仓库：agent 完整可用（commit、status、log、diff、branch、stash、add、reset 等）
- **GitHub**（`origin -> git@github.com:Huang-GPT/hmsh.git`）：agent 可用 `~/.ssh/id_ed25519` push/pull
  - 已配 GitHub SSH key（`~/.ssh/id_ed25519` + `~/.ssh/id_ed25519.pub` 已加 GitHub）
- **服务器仓库**（`/hongmen-after-sales/.git`）：agent 直接 SSH 进去跑 `git pull`
- **禁止**：未经确认就 `git push --force`、`git reset --hard` 到已推过的分支

## 当前项目的关键事实

- 服务器：root@39.106.217.235（Aliyun ECS），Aliyun Linux
- **服务器 SSH 私钥**：`~/.ssh/magic.pem`（阿里云密钥对，RSA）。Agent 直接用，不要改密码
- 项目根：**`/hongmen-after-sales/`**（不是 `/root/hongmen-after-sales/`）
- 部署模式：`docker compose`（不是裸跑）
- 前端 Dockerfile 是**多阶段**：builder 跑 `npm run build`，再 COPY dist 到 nginx
- **前端 build 失败时 dist 不存在**，`/usr/share/nginx/html/js/` 是空的
- vue-cli 4 + vant@2.12 + 自带 input type="date"

## 验证闭环纪律

每次"部署完成"必须**自己跑验证命令**，把结果贴给用户；不能只说"应该好了"。

```bash
# 服务器侧（agent 自己跑）
ssh -i ~/.ssh/magic.pem root@39.106.217.235 "docker ps --filter name=frontend --format '{{.Status}}'"
ssh -i ~/.ssh/magic.pem root@39.106.217.235 "docker exec hongmen-frontend sh -c \"grep -oc 'minDateStr' /usr/share/nginx/html/js/app.*.js\""

# 客户端（agent 跑或用户跑）
curl -sI "http://magic666.cn:18080/product/repair?v=时间戳"
```

判据要 ≥2 个独立匹配（见 PUA #7）。

**禁止**：说"部署完了"而不贴实测输出 — 这是自嗨。

## 已知 PUA 教训（来自本项目历史）

1. ~~别假设 SSH 通~~ — 2026-08-03 验证：agent 可 SSH 到 39.106.217.235（用 magic.pem），可直接跑服务器命令。AGENTS.md "环境边界" 已更新
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
