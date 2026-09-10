# 自动推送+部署 agent：新增用户500修复（c6ad377）
# 用户授权自研：网络/凭证就绪的机器上跑，自动完成 push -> 服务器 pull/rebuild -> 验证闭环
# 用法：
#   set GITHUB_TOKEN=<你的token>  （仅需 repo 权限，一次性）
#   python scripts\push_deploy_agent.py
# 说明：
#   1) push 走 HTTPS（沙箱/部分机器 22 端口被拦，HTTPS 80/443 通常可达）
#   2) 服务器操作走 SSH（magic.pem，需本机到 39.106.217.235 的 22 端口可达）
#   3) 每步打印输出，判据不过即停并报错；token 只存内存，绝不落盘/进 git
import os
import subprocess
import sys

REPO = "C:\\hongmen-after-sales"
KEY = os.path.join(os.path.expanduser("~"), ".ssh", "magic.pem")
REMOTE = "root@39.106.217.235"
SERVER_SCRIPT = "/hongmen-after-sales/scripts/server/deploy_user_fix_server.sh"
EXPECT_COMMIT = "c6ad377"

failures = []


def run(cmd, **kw):
    print(f"\n$ {cmd}")
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", **kw)
    out = (p.stdout or "") + (p.stderr or "")
    print(out[:3000])
    return p.returncode, out


def ssh(cmd):
    return run(f'ssh -i "{KEY}" -o ConnectTimeout=10 -o BatchMode=yes '
               f'-o IdentitiesOnly=yes {REMOTE} "{cmd}"')


def main():
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print("缺少 GITHUB_TOKEN：set GITHUB_TOKEN=<token> 后再跑（token 需 repo 权限）")
        sys.exit(2)

    # 1) push（HTTPS，token 只在本次命令里用，不进 git config）
    rc, _ = run(
        "git push https://x-access-token:"
        + token + "@github.com/Huang-GPT/hmsh.git master",
        cwd=REPO, timeout=120,
    )
    # 抹掉 shell 历史里的 token 痕迹提示
    if rc != 0:
        print("PUSH 失败，停止。检查 token 权限/网络。")
        sys.exit(1)

    # 2) 服务器 git 确认
    rc, out = ssh("git -C /hongmen-after-sales log --oneline -3")
    if rc != 0 or EXPECT_COMMIT not in out:
        print("服务器尚未拉取？继续执行 pull 流程。")

    # 3) 服务器一键部署（含验证）
    rc, _ = ssh(f"bash {SERVER_SCRIPT}")
    if rc != 0:
        print("服务器部署脚本非 0 退出，请看上面输出。")
        sys.exit(1)

    print("\n=== agent 执行完毕：核对上面 4 个判据，全过才算成功 ===")


if __name__ == "__main__":
    main()
