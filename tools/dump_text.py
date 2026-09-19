"""面向玩家的文本：底表 + 查重 + 术语一致性（lang 的底表，见 `docs/ROADMAP.md` §7）。

为什么要有它：lang 的工作量不在"支持几门语言"，而在**把系统层写死的中文句子抽成模板**。
抽之前得先知道**到底有多少条、都在哪、哪些重复、哪些是同一概念的几种写法**——
三件事放在同一份语料（同一张表）上，口径才不会打架：

  ① 底表：来源文件 / 行号 / 文本 / 汉字数 —— 搬运（`t()` 化）按表逐块做，才不会边搬边漏；
  ② 查重：占位符归一化后**完全相同**的成句文本（≥ `--dup-min-cjk` 个汉字）；
  ③ 术语：同一概念被写成几种说法 —— 词族计数 + **少数派逐处列出**。
     词族登记在本工具里、**不抄进 `docs/STYLE.md`**（STYLE 只留"一个概念一个词"这条规则）；
     次数一律**现算**，所以词表不会和代码漂移。
  ④ 数值变化动词：**消耗 / 流失 / 伤害 / 回复 是已定义的四种**（各管各的语义）；
     `减少` 未定义，是代表 消耗/流失/伤害 的**泛称**；`损失 / 扣除 / 失去` 是**漂移**，应改齐。
  ⑤ 概率写法：规范是 **`数字%可能`**（`25%可能xxxx`）；`数字%概率` 是要改的漂移。

字符串分三类，只有第一类才是"文案"（`docs/ROADMAP.md` §7）：
① 玩家可见文案（查重/术语才有意义）；② 数据键（`path`/tag/性别…，**必须全库一致且禁止翻译**，
重复是对的）；③ 开发文本（docstring / 注释，与玩家无关）。
本工具**只按"含汉字数"粗筛，不假装能自动分这三类**：数据键多半短（被阈值滤掉），
开发文本仍会混进来（人在看表时一眼可辨）。**别把表里的每一行都当"要翻译"。**

判据（很好用）：**少数派才是漂移** —— 出现个位数的写法多半是最近随手写的，
上百次的才是稳定用法。所以工具报的是"多数派 vs 少数派"，**改不改由人定**（它只盘点、不做判据）。

用法::

    python tools/dump_text.py                       # 全量：底表 + 查重 + 术语
    python tools/dump_text.py --min-cjk 8           # 只导成句文本（≥8 个汉字）
    python tools/dump_text.py --out D:\\tmp\\text     # 指定输出目录（默认系统临时目录）
    python tools/dump_text.py --quiet               # 只打印计数

产物（写进 `--out`）：`text_table.tsv`（底表）/ `text_report.txt`（汇总 + 查重 + 术语）。
退出码恒为 0：这是**只读的盘点工具**，不是闸门。
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
PY_DIRS = (ROOT / "weiren_game", ROOT / "dlc")
HTML_PATH = ROOT / "weiren_game" / "webui" / "index.html"

LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'')
CJK = re.compile(r"[\u4e00-\u9fff]")
PLACEHOLDER = re.compile(r"\{[^{}]*\}")

# 词族：同一概念的各种写法。**放在工具里、不抄进 `docs/STYLE.md`** —— STYLE 只留
# "一个概念一个词"这条规则；词表一旦抄进文档就会和代码漂移（`docs/ROADMAP.md` §7 末尾）。
# 顺序：多数派在前（列表只影响报表的阅读顺序，不影响计数）。
FAMILIES = (
    ("理智 / 理智值", ("理智", "理智值")),
    ("生命 / 生命值", ("生命", "生命值")),
    ("层数 / 层", ("层", "层数")),
    ("免疫 / 抵御 / 不受 / 免受", ("免疫", "抵御", "不受", "免受")),
    ("概率 / 可能 / 几率", ("概率", "可能", "几率")),
    ("获得 / 获取 / 得到", ("获得", "获取", "得到")),
    ("每局 / 本局 / 每次对局", ("每局", "本局", "每次对局")),
    ("移除 / 取消 / 清除 / 解除", ("移除", "取消", "清除", "解除")),
    ("触发 / 发动 / 生效", ("触发", "发动", "生效")),
    ("使 / 令 / 让", ("使", "令", "让")),
    ("提升 / 增加 / 提高 / 上涨", ("提升", "增加", "提高", "上涨")),
    ("降低 / 下降", ("降低", "下降")),
    ("房客 / 角色 / 住户", ("房客", "角色", "住户")),
    ("回合 / 轮", ("回合", "轮")),
)

# 数值变化动词（产品规范）：**消耗 / 流失 / 伤害 / 回复 是已定义的四种**，各自代表一种结算，
# 不能互相替换；`减少` 没有定义过，是**泛称**（代表 消耗/流失/伤害，泛指时可用）；
# `损失 / 扣除 / 失去` 是**漂移**，应逐处改齐上面四个。
VALUE_VERBS = (
    ("defined", ("消耗", "流失", "伤害", "回复")),
    ("umbrella", ("减少",)),
    ("drift", ("损失", "扣除", "失去")),
)
VERB_TAGS = {
    "defined": "规范（已定义）",
    "umbrella": "泛称（未定义）",
    "drift": "漂移（应改齐）",
}

# 概率写法：规范 `数字%可能`；`数字%概率`（含"的"）是要改的漂移。`几率` 单独列出。
PROB_CANON = re.compile(r"\d\s*%\s*可能")
PROB_DRIFT = re.compile(r"\d\s*%\s*的?\s*概率")


def _source_files() -> list[pathlib.Path]:
    paths: list[pathlib.Path] = []
    for base in PY_DIRS:
        paths.extend(sorted(base.rglob("*.py")))
    if HTML_PATH.exists():
        paths.append(HTML_PATH)
    return paths


def collect_rows(min_cjk: int) -> list[tuple[str, int, str, int]]:
    """取语料：每行里的引号字面量（含 f-string 的形状），归一化后按汉字数过滤。

    归一化两件事：`{…}` 占位符 → `{}`（f-string 的表达式部分收成一个洞），
    全角空格与连续空白收成单个半角空格。**汉字数按归一化后的文本数**（占位符里的
    表达式不是玩家文本，也不算数）。返回 [(相对路径, 行号, 文本, 汉字数)]。
    注释行（`#` 开头）整行跳过；HTML 里的注释会被收进来（人在看表时剔除）。
    """
    rows: list[tuple[str, int, str, int]] = []
    for path in _source_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            for match in LITERAL.finditer(line):
                raw = match.group(1)
                if raw is None:
                    raw = match.group(2)
                if not raw:
                    continue
                key = " ".join(PLACEHOLDER.sub("{}", raw).replace("\u3000", " ").split())
                cjk = len(CJK.findall(key))
                if cjk < min_cjk:
                    continue
                rows.append((rel, number, key, cjk))
    return rows


def duplicate_groups(
    rows: list[tuple[str, int, str, int]], min_cjk: int
) -> tuple[list[tuple[str, list[str]]], int]:
    """查重：归一化后完全相同的成句文本。返回 (分组, 参与统计的文本条数)。"""
    places: dict[str, list[str]] = collections.defaultdict(list)
    for rel, number, key, cjk in rows:
        if cjk < min_cjk:
            continue
        places[key].append("%s:%d" % (rel, number))
    groups = [(key, spots) for key, spots in places.items() if len(spots) > 1]
    groups.sort(key=lambda item: (-len(item[1]), item[0]))
    return groups, len(places)


def family_counts(
    rows: list[tuple[str, int, str, int]]
) -> list[tuple[str, list[tuple[str, list[str]]]]]:
    """按登记的词族数各写法出现多少次、出现在哪（子串计，含更长词里的复用）。

    每处带**原句**（`文件:行  文本`），才好逐条改（见 `docs/ROADMAP.md` §7）。
    """
    out = []
    for title, variants in FAMILIES:
        counts = []
        for variant in variants:
            hits = ["%s:%d  %s" % (rel, number, key)
                    for rel, number, key, _ in rows if variant in key]
            counts.append((variant, hits))
        out.append((title, counts))
    return out


def style_metrics(rows: list[tuple[str, int, str, int]]) -> list[str]:
    """粗粒度风格指标 —— **只做提示、不做判据**（见 `docs/ROADMAP.md` §7）。"""
    cjk_total = sum(cjk for _, _, _, cjk in rows)
    de = sum(key.count("的") for _, _, key, _ in rows)
    passive = [(rel, number) for rel, number, key, _ in rows if "被" in key]
    density = (100.0 * de / cjk_total) if cjk_total else 0.0
    return [
        "「的」密度：%d / %d 汉字 = 每百字 %.1f 个" % (de, cjk_total, density),
        "含「被…」被动句的文本：%d 条" % len(passive),
    ]


def value_verb_counts(
    rows: list[tuple[str, int, str, int]]
) -> list[tuple[str, str, list[str]]]:
    """数值变化动词：规范 / 泛称 / 漂移各出现多少、出现在哪。"""
    out = []
    for kind, verbs in VALUE_VERBS:
        for verb in verbs:
            hits = ["%s:%d  %s" % (rel, number, key)
                    for rel, number, key, _ in rows if verb in key]
            out.append((kind, verb, hits))
    return out


def probability_report(
    rows: list[tuple[str, int, str, int]]
) -> tuple[list[str], list[str], list[str]]:
    """概率写法：返回 (符合 `数字%可能` 的，写成 `数字%概率` 的，含 `几率` 的)。

    只看**带 `%` 的文本**；`概率+25%`、`概率-6%` 这类**修正量**不是事件概率，不在此列
    （它们的 `%` 前不是概率数字）。标记符号（`*`）先去掉再判。
    """
    canon, drift, odd = [], [], []
    for rel, number, key, _ in rows:
        if "%" not in key:
            continue
        spot = "%s:%d  %s" % (rel, number, key)
        plain = key.replace("*", "")
        if PROB_CANON.search(plain):
            canon.append(spot)
        elif PROB_DRIFT.search(plain):
            drift.append(spot)
        if "几率" in key:
            odd.append(spot)
    return canon, drift, odd


def build_report(
    rows: list[tuple[str, int, str, int]],
    groups: list[tuple[str, list[str]]],
    sentence_total: int,
    families: list[tuple[str, list[tuple[str, list[str]]]]],
    min_cjk: int,
    dup_min_cjk: int,
) -> str:
    lines: list[str] = []
    lines.append("面向玩家的文本盘点（min-cjk=%d / dup-min-cjk=%d）" % (min_cjk, dup_min_cjk))
    lines.append("语料：%d 条；其中 ≥%d 汉字的成句文本 %d 条、重复组 %d 组。"
                 % (len(rows), dup_min_cjk, sentence_total, len(groups)))
    lines.append("")

    lines.append("## 按来源汇总（谁家的文本最多 = 收拢的重点）")
    per_file: collections.Counter[str] = collections.Counter()
    for rel, _, _, _ in rows:
        per_file[rel] += 1
    for rel, count in per_file.most_common(25):
        lines.append("   %5d  %s" % (count, rel))
    lines.append("")

    lines.append("## 查重（≥%d 汉字、归一化后完全相同）" % dup_min_cjk)
    if not groups:
        lines.append("   （无）")
    for key, spots in groups:
        lines.append("   x%d  %s" % (len(spots), key))
        lines.append("        %s" % "  ".join(spots))
    lines.append("")

    lines.append("## 术语：同一概念的几种写法（多数派 vs 少数派）")
    for title, counts in families:
        used = [(variant, hits) for variant, hits in counts if hits]
        if len(used) < 2:
            variant, hits = (used[0] if used else (counts[0][0], []))
            lines.append("== %s：只用「%s」x%d（一致）" % (title, variant, len(hits)))
            continue
        used.sort(key=lambda item: -len(item[1]))
        lines.append("== %s" % title)
        for rank, (variant, hits) in enumerate(used):
            tag = "多数派" if rank == 0 else "漂移"
            lines.append("   %-6s x%-4d %s" % (variant, len(hits), tag))
            if rank:
                for spot in hits:
                    lines.append("        %s" % spot)
    lines.append("")

    lines.append("## 数值变化动词（规范：消耗 / 流失 / 伤害 / 回复；泛称：减少；漂移：损失 / 扣除 / 失去）")
    for kind, verb, hits in value_verb_counts(rows):
        lines.append("   %-6s x%-4d %s" % (verb, len(hits), VERB_TAGS[kind]))
        if kind == "drift":
            for spot in hits:
                lines.append("        %s" % spot)
    lines.append("")

    canon, drift, odd = probability_report(rows)
    lines.append("## 概率写法（规范：`数字%可能`）")
    lines.append("   符合 `数字%%可能`：%d 处" % len(canon))
    lines.append("   写成 `数字%%概率`（应改 `可能`）：%d 处" % len(drift))
    for spot in drift:
        lines.append("        %s" % spot)
    if odd:
        lines.append("   含 `几率`（不在规范里）：%d 处" % len(odd))
        for spot in odd:
            lines.append("        %s" % spot)
    lines.append("")

    lines.append("## 粗粒度风格指标（只做提示，不做判据）")
    for line in style_metrics(rows):
        lines.append("   " + line)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="导出面向玩家的文本底表 + 查重 + 术语一致性")
    parser.add_argument("--min-cjk", type=int, default=4, help="收进语料的最少汉字数（默认 4）")
    parser.add_argument("--dup-min-cjk", type=int, default=8, help="算重复的最少汉字数（默认 8）")
    parser.add_argument("--out", default="", help="输出目录（默认系统临时目录）")
    parser.add_argument("--quiet", action="store_true", help="只打印计数，明细写文件")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except OSError:
                pass

    rows = collect_rows(args.min_cjk)
    groups, sentence_total = duplicate_groups(rows, args.dup_min_cjk)
    families = family_counts(rows)
    report = build_report(rows, groups, sentence_total, families,
                          args.min_cjk, args.dup_min_cjk)

    out = pathlib.Path(args.out) if args.out else pathlib.Path(tempfile.gettempdir()) / "weiren-text"
    out.mkdir(parents=True, exist_ok=True)
    table = out / "text_table.tsv"
    with table.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("file\tline\tcjk\ttext\n")
        for rel, number, key, cjk in rows:
            handle.write("%s\t%d\t%d\t%s\n" % (rel, number, cjk, key))
    (out / "text_report.txt").write_text(report, encoding="utf-8", newline="\n")

    print("语料 %d 条 / 成句 %d 条 / 重复组 %d 组 -> %s"
          % (len(rows), sentence_total, len(groups), out))
    if not args.quiet:
        print()
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
