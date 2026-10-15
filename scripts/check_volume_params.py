#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""check_volume_params.py — 卷参数混用守卫（开工门）

作用：扫描卷工作目录的 scripts/，检测 lvse 基准卷参数残留。复制改造后必须
退出码 0（零残留）才允许开工；非 0 = 逐条列出残留，禁止开工。

六类检查（高危项标 ⚠️，漏改=静默错配或错源）：
  1. 路径/文件名    lvse 卷目录、基准源 PDF、sz05 模板路径
  2. sha12 锚定     ac0de6d04eba / 6d347c2b6efc / c59ff1414c34 / 9030f0b5672d
  3. 编码/章码正则  ⚠️ 20- 前缀、012\d{3} 章码、12001 区块码（静默错配，危害最大）
  4. 数量断言      487/77/53/1437/227/2919/652（漏改=门控恒红，能暴露）
  5. 页码偏移      OFFSET = 9 / toc_pages [6, 9] / 分区 +5
  6. 卷特有文案    绿色建筑/lvse/LV-/册说明 9 条/屋顶花园

用法：python check_volume_params.py <卷工作目录>/scripts [--allow <关键词>]
  --allow：豁免含指定关键词的行（如复用他卷模板时，理由须记录于交付报告）。
自测：对本 skill 参考原版运行应全量检出（见 references/volume_params.md）。
"""
import os, re, sys

CHECKS = [
    # (类别, 编译正则, 说明)
    ("路径/文件名", re.compile(r"quota-extract-lvse|quota-extract-sz05|1773816825515128"), "基准卷路径/源文件名"),
    ("路径/文件名", re.compile(r"lvse_quota\.db|lvse_items\.json|lvse_toc\.json|lvse_desc_rules\.json"), "基准产物名"),
    ("sha12 锚定", re.compile(r"ac0de6d04eba|6d347c2b6efc|c59ff1414c34|9030f0b5672d"), "基准源指纹（换值禁删断言）"),
    ("编码/章码 ⚠️", re.compile(r"20-\\d|\b20-\d|\"20-\"|'20-'|CODE_PREFIX = \"20-\"|012\\d|012\d{3}|\"01200|'01200|12001|12002|12003|12004"), "子目前缀/章码/区块码（静默错配）"),
    ("数量断言", re.compile(r"\b487\b|\b1437\b|\b227\b|\"77\"|\b77\b|\"53\"|\b2919\b|\b652\b"), "基准卷计数"),
    ("页码偏移", re.compile(r"OFFSET = 9\b|toc_pages.{0,4}\[6, 9\]|\+ 5\b.{0,20}目录|offset.{0,6}9"), "分区 offset"),
    ("卷特有文案", re.compile(r"绿色建筑|辽住建〔2025〕25|屋顶花园|垂直绿化|透水地面|LV-|册说明未设人工三档|md 源提取卷"), "基准卷文案"),
]
FILES = ("*.py", "*.mjs")


def scan(scripts_dir, allows):
    hits = []
    for fn in sorted(os.listdir(scripts_dir)):
        if fn == "check_volume_params.py":  # 守卫自身 docstring 含基准特征词，跳过
            continue
        if not any(fn.endswith(pat.strip("*")) or fn == pat for pat in FILES):
            continue
        path = os.path.join(scripts_dir, fn)
        if not os.path.isfile(path):
            continue
        for ln, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
            if any(a in line for a in allows):
                continue
            for cat, pat, desc in CHECKS:
                if pat.search(line):
                    hits.append((fn, ln, cat, desc, line.strip()[:100]))
                    break  # 每行报首类，防重复计数
    return hits


def main():
    args = sys.argv[1:]
    allows = []
    while "--allow" in args:
        i = args.index("--allow")
        allows.append(args[i + 1])
        del args[i:i + 2]
    if not args:
        print(__doc__)
        sys.exit(2)
    hits = scan(args[0], allows)
    if not hits:
        print("PASS: 零残留（%d 项检查全过）——可以开工" % len(CHECKS))
        sys.exit(0)
    print("FAIL: 检出 %d 处基准卷残留，禁止开工：" % len(hits))
    for fn, ln, cat, desc, line in hits:
        print(f"  {fn}:{ln} [{cat}·{desc}] {line}")
    sys.exit(1)


if __name__ == "__main__":
    main()
