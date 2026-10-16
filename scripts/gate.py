# -*- coding: utf-8 -*-
"""
gate.py —— 园林绿化工程定额卷（辽宁2024，md 源）九门门控 + 基线指纹
门1 装载完备 / 门2 编码连续（逐章）/ 门3 完整性 / 门4 H1 / 门5 消耗结构
门6 目录对账（+页脚实测）/ 门7 条文回读（+印刷页页脚实测）/ 门8 基线指纹 / 门9 P1 官方原版取证
--make-manifest 刷基线；全链重跑后门8 自校验字节级复现
多章册适配：定额编号四章分前缀 1-/2-/3-/4-；门2 逐章查空洞
"""
import hashlib
import json
import re
import sqlite3
import sys

import fitz

BASE = r"C:/Users/Administrator/WorkBuddy/sp/quota-extract-yl01/out"
WEB = r"C:/Users/Administrator/WorkBuddy/sp/quota-extract-yl01/web"
MANIFEST = r"C:/Users/Administrator/WorkBuddy/sp/quota-extract-yl01/baseline_manifest.json"
NOWM = r"C:/Users/Administrator/WorkBuddy/sp/quota-extract-yl01/input/nowm.pdf"
ARTIFACTS = [
    BASE + r"\md_extract_full.json", BASE + r"\md_index.json",
    BASE + r"\yl01_items.json", BASE + r"\yl01_toc.json",
    BASE + r"\yl01_desc_rules.json", BASE + r"\yl01_quota.db",
    BASE + r"\cost_check_report.json", BASE + r"\_web_data.json",
    WEB + r"\index.html",
]
ANCHORS = {
    "nowm_pdf_sha12": "77350d6d3a2d",   # remove_watermark 产 nowm.pdf 实测（342 页零残留）
    "wm_pdf_sha12": "7071387e8709",
    "md_sha12": None,  # 由产物自证
}
# 产物计数预期（首跑实测后回填；变更须重跑全链并 --make-manifest）
N_BLOCKS = 2145
N_TBL = 292
N_TOC = 160
N_RULE = 41


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ---- 页脚印刷页实测（坑 51/52 根治：页码口径的 ground truth）----
# 坑 52：页脚多位数在 get_text() 行序中非 x 序（E-BZ 字体 span 序混乱，实测 sz08 P185
# 行序 "2 7 1" 而真值 172）——必须按 span x 坐标排序拼接；版面过滤（底部 15%+页缘）
# 排除表格右下角同龄字号内容。
_fdoc = fitz.open(NOWM)
_footer_cache = {}


def page_footer(pno):
    """物理页页脚印刷页（int）；无印刷页码页返回 None。"""
    if pno in _footer_cache:
        return _footer_cache[pno]
    page = _fdoc[pno - 1]
    W, H = page.rect.width, page.rect.height
    d = page.get_text("dict")
    cands = []
    for b in d["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                t = s["text"].strip()
                if not t or t == "·" or not re.fullmatch(r"\d{1,3}", t):
                    continue
                x0, y0 = s["bbox"][0], s["bbox"][1]
                if y0 > 0.85 * H and (x0 < 0.18 * W or x0 > 0.82 * W):
                    cands.append((round(y0, 1), round(x0, 1), t))
    val = None
    if cands:
        cands.sort()
        y0 = cands[0][0]
        row = sorted([c for c in cands if abs(c[0] - y0) <= 2], key=lambda c: c[1])
        val = int("".join(t for _, _, t in row))
    _footer_cache[pno] = val
    return val


results = []


def gate(gid, name, ok, detail):
    results.append((gid, name, "PASS" if ok else "FAIL", detail))
    print("[%s] %s %s | %s" % ("PASS" if ok else "FAIL", gid, name, detail))


con = sqlite3.connect("file:" + (BASE + r"\yl01_quota.db").replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
idx = json.load(open(BASE + r"\md_index.json", encoding="utf-8"))
items_doc = json.load(open(BASE + r"\yl01_items.json", encoding="utf-8"))
toc_doc = json.load(open(BASE + r"\yl01_toc.json", encoding="utf-8"))
desc_doc = json.load(open(BASE + r"\yl01_desc_rules.json", encoding="utf-8"))
rep = json.load(open(BASE + r"\cost_check_report.json", encoding="utf-8"))
web_data = json.load(open(BASE + r"\_web_data.json", encoding="utf-8"))

# ---- 门1 装载完备性 ----
doc_full = json.load(open(BASE + r"\md_extract_full.json", encoding="utf-8"))
n_blocks = len(doc_full["blocks"])
n_tbl = len(idx["tables"])
n_issue = len(items_doc["meta"]["parse_issues"])
gate("门1", "装载完备", n_blocks == N_BLOCKS and n_tbl == N_TBL and n_issue == 0,
     "blocks=%d tables=%d parse_issues=%d" % (n_blocks, n_tbl, n_issue))

# ---- 门2 编码连续（多章册：逐章前缀独立查空洞，防跨章串号掩盖缺号） ----
codes = [r[0] for r in con.execute("select item_code from items")]
by_ch = {}
for c in codes:
    ch, nn = c.split("-")
    by_ch.setdefault(ch, []).append(int(nn))
ch_gaps = {}
for ch, v in by_ch.items():
    s = set(v)
    ch_gaps[ch] = [n for n in range(1, max(v) + 1) if n not in s]
gaps = [(ch, n) for ch, v in ch_gaps.items() for n in v]
ch_cov = {ch: len(v) for ch, v in sorted(by_ch.items())}
n_list = con.execute("select count(*) from items where list_code is null or list_code=''").fetchone()[0]
gate("门2", "编码连续（逐章）", not gaps and n_list == 0,
     "n=%d 章覆盖=%s 空洞=%d 清单编号缺=%d" % (len(codes), ch_cov, len(gaps), n_list))

# ---- 门3 完整性 ----
n_unit = con.execute("select count(*) from items where unit is null or unit=''").fetchone()[0]
n_work = con.execute("select count(*) from items where work_content is null or work_content=''").fetchone()[0]
n_name = con.execute("select count(*) from items where name is null or name=''").fetchone()[0]
gate("门3", "unit/work/name 零空（yl01：unit 复合空格归一+㎡→m2 后零空；work 零空）",
     n_unit == 0 and n_work == 0 and n_name == 0,
     "unit空=%d work空=%d name空=%d" % (n_unit, n_work, n_name))
gate("门4", "H1 恒等式", rep["H1"]["fail"] == 0,
     "pass=%d fail=%d" % (rep["H1"]["pass"], rep["H1"]["fail"]))

# ---- 门5 消耗结构 ----
unpriced = con.execute("select count(*) from item_materials where unpriced=1").fetchone()[0]
gate("门5", "H3/H4 消耗结构", rep["H3"]["fail"] == 0 and rep["H4"]["fail"] == 0,
     "H3 fail=%d H4 fail=%d unpriced留痕=%d" % (rep["H3"]["fail"], rep["H4"]["fail"], unpriced))

# ---- 门6 目录对账 ----
toc_rows = toc_doc["rows"]
toc_secs = set(r["title"] for r in toc_rows if r["level"] == "节行")
md_secs = set(s["title"] for ch in web_data["chapters"] for s in ch["sections"])
# 章内页码单调
mono_ok = True
prev = {}
for r in toc_rows:
    if r["print_page"] is None:
        continue
    ch = r["chapter_no"] or "GS"
    if r["print_page"] < prev.get(ch, 0):
        mono_ok = False
    prev[ch] = r["print_page"]
# 门6b：目录 pdf_page 页脚实测（print_page 必须与官方 PDF 页脚一致）
# 坑 55 口径定版：TOC 推导物理页（print+OFFSET）可落在无页码扉页对上（yl01 实测 4 条：
# 186=ch3 扉页、334/335=附录扉页对，书印 TOC 引用偏差 +1~+2 属书印事实）——footer=None
# 无法页脚验证 → skip 留痕非失配；footer 实测 != print 才是真失配（解析层 offset 错）。
# 交叉互证：footer=None 的页集合必须 ⊆ extract_md meta.no_page_print（防解析层漏标）。
toc_fp_bad = []
toc_fp_skip = []
for r in toc_rows:
    if not r["pdf_page"]:
        continue
    foot = page_footer(r["pdf_page"])
    if foot is None:
        toc_fp_skip.append((r["id"], r["pdf_page"], r["print_page"]))
    elif foot != r["print_page"]:
        toc_fp_bad.append((r["id"], r["pdf_page"], r["print_page"], foot))
npp = set(doc_full["meta"].get("no_page_print") or [])
npp_leak = [p for _, p, _ in toc_fp_skip if p not in npp]
gate("门6", "目录对账", len(toc_rows) == N_TOC and md_secs <= toc_secs and mono_ok
     and not toc_fp_bad and not npp_leak,
     "toc行=%d 节子集=%s 章内页码单调=%s 真失配=%d %s 无页码页skip=%d 泄漏=%s"
     % (len(toc_rows), md_secs <= toc_secs, mono_ok, len(toc_fp_bad), toc_fp_bad[:3],
        len(toc_fp_skip), npp_leak))

# ---- 门7 条文层回读 + 门7b 印刷页页脚实测 ----
full_blocks = doc_full["blocks"]
n_rule = len(desc_doc["rules"])
n_ok = n_bad = 0
bad = []
for r in desc_doc["rules"]:
    if r["block_type"] == "附表":
        n_ok += 1  # 附表为拍平记录，单独口径
        continue
    try:
        blks = json.loads(r["src_blks"])
        src_join = "".join(full_blocks[b]["text"].strip() for b in blks)
        if re.sub(r"\s+", "", src_join) == re.sub(r"\s+", "", r["text"]):
            n_ok += 1
        else:
            n_bad += 1
            bad.append(r["section_id"])
    except Exception:
        n_bad += 1
        bad.append(r["section_id"])
# 门7b：desc_rules.print_page 必须与 PDF 页脚实测一致（坑 51：内联偏移写错→整体偏页）
fp_bad = []
for r in desc_doc["rules"]:
    foot = page_footer(r["page"]) if r["page"] else None
    if foot is not None and r["print_page"] != foot:
        fp_bad.append((r["section_id"], r["page"], r["print_page"], foot))
gate("门7", "条文字节级回读+印刷页页脚实测", n_rule == N_RULE and n_bad == 0 and not fp_bad,
     "rules=%d 回读ok=%d bad=%d 页脚失配=%d %s" % (n_rule, n_ok, n_bad, len(fp_bad), fp_bad[:5]))

# ---- 门9 P1 官方原版取证（先于门8：门8 含全部产物指纹） ----
gate("门9", "P1 官方原版取证", rep["P1"]["fail"] == 0,
     "pass=%d fail=%d skip=%d" % (rep["P1"]["pass"], rep["P1"]["fail"], rep["P1"]["skip"]))

con.close()

# ---- 门8 基线指纹 ----
cur = {p.split("\\")[-1]: sha256(p) for p in ARTIFACTS}
cur["_anchors"] = {"nowm_pdf_sha12": ANCHORS["nowm_pdf_sha12"],
                   "wm_pdf_sha12": ANCHORS["wm_pdf_sha12"]}
if "--make-manifest" in sys.argv:
    json.dump(cur, open(MANIFEST, "w", encoding="utf-8"), indent=1)
    gate("门8", "基线指纹", True, "已刷新 manifest（%d 产物）" % len(cur))
else:
    try:
        base_m = json.load(open(MANIFEST, encoding="utf-8"))
        diff = [k for k in cur if base_m.get(k) != cur[k]]
        gate("门8", "基线指纹", not diff,
             "一致（%d 产物）" % len(cur) if not diff else "失配: %s" % diff)
    except FileNotFoundError:
        gate("门8", "基线指纹", False, "manifest 不存在，先 --make-manifest")

n_fail = sum(1 for r in results if r[2] == "FAIL")
print()
print("=" * 50)
print("九门结果: %d PASS / %d FAIL" % (len(results) - n_fail, n_fail))
if "--rerun" in sys.argv:
    print("（--rerun 端到端复现由外部编排执行：重跑全链后再次 gate 校验门8）")
sys.exit(1 if n_fail else 0)
