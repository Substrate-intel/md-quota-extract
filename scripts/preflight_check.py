#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""preflight_check.py —— 开工前自检（坑 15 根治：换参三类系统性漏网一轮暴露）

在「复制 scripts/ → 换参」之后、进入管线之前跑本脚本（先于 check_volume_params）：
  A. 路径存在性：扫描全部 *.py 的路径常量（SRC/DST/ROOT/BASE/DB/NOWM/WM/TPL/MD/OUT_DIR），
     逐个验证存在（文件/目录）——Downloads/、上卷目录残留在此一轮暴露；
  B. 编码/章码正则试命中：对 md 源（或 convert 前的 PDF）试跑 CODE_RE/CH_RE，
     0 命中即红（防单/双反斜杠形态漏换——映射表写 r"20-\\d" 永不命中且不报错）；
  C. 章码[2:] 短码核对：从 idx/PDF 提取章码全集，验证「全码→短码」无碰撞
     （041101→1101；smoke 路由必须用短码，全码路由=空页假绿）；
  D. 断言占位扫描：gate/finalize/smoke 里的数量断言若仍是基准卷值（487/77/53/1437/227）
     则提示「待实测回填」（不阻断——阶段 1-2 后回填，但显式提醒防忘）；
  E. 基准残留守卫：内嵌调 check_volume_params 同类扫描（可选）。

用法：python preflight_check.py <卷工作目录> [--md <md源路径>]
退出码 0=可进管线；非 0=逐条列出阻断项。
"""
import os, re, sys, glob

FAILS, WARNS = [], []


def fail(msg): FAILS.append(msg)
def warn(msg): WARNS.append(msg)


def scan_paths(scripts_dir, vol_root):
    """A. 路径常量存在性"""
    pat = re.compile(r'''^(?:SRC|DST|ROOT|BASE|DB|NOWM|WM|TPL|MD|OUT|OUT_DIR|WEB|CONVERT)\s*=\s*r?["']([^"']+)["']''', re.M)
    for py in glob.glob(os.path.join(scripts_dir, "*.py")):
        src = open(py, encoding="utf-8").read()
        for m in pat.finditer(src):
            p = m.group(1)
            if "<" in p or "%" in p or p.startswith("http"):
                continue
            p2 = p.replace("\\\\", "\\")
            if not os.path.exists(p2):
                rel = os.path.relpath(py, scripts_dir)
                # 卷内相对产物（尚未生成的 out/xxx）不阻断，只提示
                if vol_root and (vol_root.replace("/", "\\") in p2 or vol_root in p2):
                    warn(f"[A] {rel}: 卷内待产物 {p2}（管线会生成，OK）")
                else:
                    fail(f"[A] {rel}: 路径不存在 {p2}（疑似上卷/Downloads 残留）")
            # 他卷目录残留（路径存在但指向别的卷——基准卷在本机存在，存在性查不出）
            m_vol = re.search(r"quota-extract-[a-z0-9]+", p)
            if m_vol and vol_root:
                my = os.path.basename(vol_root.rstrip("/\\"))
                if m_vol.group(0) != my:
                    fail(f"[A] {os.path.basename(py)}: 他卷目录残留 {m_vol.group(0)}（应为 {my}）")


def scan_regex(scripts_dir, md_path):
    """B. 编码/章码正则试命中"""
    if not md_path or not os.path.exists(md_path):
        warn("[B] 未提供 md 源（convert 前可跳过 B/C）")
        return
    md = open(md_path, encoding="utf-8").read()
    codes = set(re.findall(r"(?<!\d)(\d{1,2}-\d{1,4})(?!\d)", md))
    for py in glob.glob(os.path.join(scripts_dir, "*.py")):
        src = open(py, encoding="utf-8").read()
        # 抓 CODE_RE 类单反斜杠正则字面量
        for m in re.finditer(r'CODE_RE\s*=\s*re\.compile\(r"([^"]+)"\)', src):
            pat = m.group(1)
            body = pat.strip("^$").replace("\\d", "\\d")
            hit = sum(1 for c in codes if re.fullmatch(pat, c))
            if hit == 0:
                fail(f"[B] {os.path.basename(py)}: CODE_RE {pat!r} 对 md 源 0 命中（正则漏换/形态错——检查单反斜杠）")
        for m in re.finditer(r'CH_RE\s*=\s*re\.compile\(r"([^"]+)"\)', src):
            pat = m.group(1)
            hit = len(re.findall(pat, md, re.M))
            if hit == 0:
                fail(f"[B] {os.path.basename(py)}: CH_RE {pat!r} 对 md 源 0 命中（章码正则漏换）")


def scan_shortcodes(scripts_dir, md_path):
    """C. 章码[2:] 短码无碰撞 + smoke 路由用短码"""
    if not md_path or not os.path.exists(md_path):
        return
    md = open(md_path, encoding="utf-8").read()
    chs = sorted(set(re.findall(r"\((\d{6})\)", md)))  # 只认章标题括号码（041101 形态）
    shorts = {}
    for f in chs:
        shorts.setdefault(f[2:], []).append(f)
    clash = {s: fs for s, fs in shorts.items() if len(fs) > 1}
    if clash:
        warn(f"[C] 章码[2:] 短码碰撞（前端按章序归章可容忍）：{clash}")
    smoke = os.path.join(scripts_dir, "smoke_front.mjs")
    if os.path.exists(smoke):
        s = open(smoke, encoding="utf-8").read()
        for m in re.finditer(r'show\("layer:([^:"]+):', s):
            sc = m.group(1)
            if sc not in shorts:
                fail(f"[C] smoke 路由 {sc!r} 不是任何章码的[2:]短码（空页假绿——应为其一 {sorted(shorts)[:3]}…）")


def scan_assert_placeholders(scripts_dir):
    """D. 基准卷断言残留提示"""
    base_vals = {"487": "子目数", "1437": "blocks", "227": "tables", "77": "toc", "53": "rules(旧)"}
    for fn in ("gate.py", "finalize.py", "smoke_front.mjs", "build_front.py"):
        p = os.path.join(scripts_dir, fn)
        if not os.path.exists(p):
            continue
        src = open(p, encoding="utf-8").read()
        for v, what in base_vals.items():
            if re.search(r"==\s*%s\b" % v, src) or re.search(r"!==?\s*%s\b" % v, src):
                warn(f"[D] {fn}: 断言 {v}（{what}）疑似基准卷值——阶段 1-2 实测后回填")


def main():
    args = sys.argv[1:]
    md_path = None
    if "--md" in args:
        i = args.index("--md"); md_path = args[i + 1]; del args[i:i + 2]
    if not args:
        print(__doc__); sys.exit(2)
    vol = args[0].rstrip("\\/")
    scripts_dir = os.path.join(vol, "scripts")
    if not os.path.isdir(scripts_dir):
        scripts_dir = args[0]  # 直接传 scripts 目录
        vol = os.path.dirname(scripts_dir)
    scan_paths(scripts_dir, vol)
    scan_regex(scripts_dir, md_path)
    scan_shortcodes(scripts_dir, md_path)
    scan_assert_placeholders(scripts_dir)
    for w in WARNS:
        print("WARN", w)
    if FAILS:
        print("\nFAIL %d 项（阻断开工）：" % len(FAILS))
        for f in FAILS:
            print("  ", f)
        sys.exit(1)
    print("preflight PASS（%d 警告，0 阻断）——可进管线" % len(WARNS))


if __name__ == "__main__":
    main()
