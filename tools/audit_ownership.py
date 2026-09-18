"""归属边界自检：外部 PR 只准动「开放区」（`dlc/`、`resourcepacks/`）。

本仓库只有两类目录开放给外部贡献 —— `dlc/`（内容包）与 `resourcepacks/`（资源包）；
其余一切（`weiren_game/` 核心与内置内容、`tools/`、`tests/`、`docs/`、`design/`、根文件）
是自留区，只由仓库作者维护。规则与提交路径见 `CONTRIBUTING.md`。

用法::

    python tools/audit_ownership.py --base origin/main
    python tools/audit_ownership.py --files weiren_game/engine.py dlc/foo/pack.json
    python tools/audit_ownership.py --base origin/main --trusted OWNER

这个工具用在 `.github/workflows/ownership-guard.yml`（PR 检查）。
作者与协作者本人（`--trusted`）直接跳过：在自留区工作是作者的正当行为，
这里挡的只是**外部**改动，所以它也**不进** AGENTS.md 的「每次改完的固定动作」。
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

# 开放区：外部可自由增删（内容包 / 资源包）。
OPEN_PREFIXES = ("dlc/", "resourcepacks/")
# 这些关联的人被视为"自己人"：OWNER=作者，MEMBER=组织成员，COLLABORATOR=协作者。
TRUSTED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}


def is_open(path: str) -> bool:
    """路径是否属于开放区（外部可自由改动）。"""
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.startswith(OPEN_PREFIXES)


def changed_files(base: str) -> list[str]:
    """列出 `base...HEAD` 之间的改动文件（重命名/删除/新增都算）。"""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACDMRTUXB", f"{base}...HEAD"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"git diff 失败（基线 {base} 是否可取到？）：{result.stderr.strip()}")
    return [line for line in result.stdout.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    """入口：返回 0 表示通过（或跳过），1 表示触碰了自留区。"""
    parser = argparse.ArgumentParser(
        description="归属边界自检：外部 PR 只准动 dlc/ 与 resourcepacks/"
    )
    parser.add_argument(
        "--base", default="origin/main",
        help="对比基线（默认 origin/main），按 <base>...HEAD 求改动",
    )
    parser.add_argument("--files", nargs="*", help="直接给改动清单（给了就不查 git）")
    parser.add_argument(
        "--trusted", default="",
        help="作者关联（OWNER/MEMBER/COLLABORATOR）：命中则跳过检查",
    )
    parser.add_argument("--actor", default="", help="PR 发起者的 GitHub 登录名")
    parser.add_argument(
        "--trusted-actors", default="",
        help="额外授权的账号（逗号分隔；缺省读环境变量 WEIREN_TRUSTED_ACTORS）",
    )
    parser.add_argument("--quiet", action="store_true", help="只在违规时输出")
    args = parser.parse_args(argv)

    if args.trusted.strip().upper() in TRUSTED_ASSOCIATIONS:
        print(f"归属检查跳过：{args.trusted} 是作者/协作者，自留区的改动属正当行为。")
        return 0
    allowlisted = args.trusted_actors or os.environ.get("WEIREN_TRUSTED_ACTORS", "")
    allowed = {name.strip().lower() for name in allowlisted.split(",") if name.strip()}
    if args.actor.strip().lower() in allowed:
        print(f"归属检查跳过：{args.actor} 是作者授权的创作工具。")
        return 0

    files = list(args.files) if args.files else changed_files(args.base)
    violations = [path for path in files if not is_open(path)]
    if not violations:
        if not args.quiet:
            print(
                f"归属检查通过：{len(files)} 个改动全部落在开放区"
                f"（{'、'.join(OPEN_PREFIXES)}）。"
            )
        return 0

    print("归属检查未通过：以下文件属于自留区，只由仓库作者维护 ——")
    for path in violations:
        print(f"  - {path}")
    print("")
    print(f"开放区只有：{'、'.join(OPEN_PREFIXES)}。")
    print("要改核心或内置内容，请先开 issue 说明（见 CONTRIBUTING.md）；")
    print("新增内容请放进 dlc/ 或 resourcepacks/。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
