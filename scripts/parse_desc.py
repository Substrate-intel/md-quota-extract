# -*- coding: utf-8 -*-
"""
parse_desc.py —— 园林绿化工程定额卷 目录层 + 条文层
toc：nowm.pdf 目录区（P10-13）双栏重组（x<280 左栏 / >=280 右栏，栏内 y±6.5 聚类；
     本卷 4 页全双栏）
desc_rules：md blocks 条文切片（总说明/章说明/计算规则/附表，每条一记录；本卷无独立册说明）
页码口径：正文印刷页 = 物理页 - 15（目录引用页码为正文印刷页；章码形态 05xxxx）
"""
import fitz
import json
import re

BASE = r"C:/Users/Administrator/WorkBuddy/sp/quota-extract-yl01/out"
NOWM = r"C:/Users/Administrator/WorkBuddy/sp/quota-extract-yl01/input/nowm.pdf"
OFFSET = 15

# ============================== 一、目录层 ==============================
doc = fitz.open(NOWM)
toc_rows = []  # (seq, raw_line, page)
for pno in range(9, 13):  # P10-13
    d = doc[pno].get_text("dict")
    lines = []
    for b in d["blocks"]:
        if b["type"] != 0:
            continue
        for l in b["lines"]:
            t = "".join(s["text"] for s in l["spans"]).strip()
            if t and not re.fullmatch(r"[·\s\d]+", t):
                lines.append((l["bbox"][1], l["bbox"][0], t))
    # 分左右栏
    left = [(y, x, t) for y, x, t in lines if x < 280]
    right = [(y, x, t) for y, x, t in lines if x >= 280]
    for col in (left, right):
        col.sort()
        rows = []
        for y, x, t in col:
            if rows and abs(y - rows[-1][0]) <= 6.5:  # 章名与编码行 y 差~5，行距 14.7 安全
                rows[-1][1].append((x, t))
            else:
                rows.append([y, [(x, t)]])
        for y, cells in rows:
            raw = "".join(t for x, t in sorted(cells)).strip()
            if raw and not raw.startswith("目") or len(raw) > 3:
                toc_rows.append((pno + 1, raw))
doc.close()

# 行解析 → sz05 契约字段
CH_RE = re.compile(r"^第([一二三四五六七八九十]+)章\s*(.*?)\(([0-9]{4,6})\)\s*$")  # 章码 4-6 位（yl01=0501~0504）
SEC_RE = re.compile(r"^([一二三四五六七八九十]+)、")
SUB_RE = re.compile(r"^(\d+)\.\s*")
PG_RE = re.compile(r"^[.…·\s]*\((\d{1,3})\)\s*$")

records = []
seq = 0
cur_ch_no = None
cur_ch_code = None
i = 0
n_rows = len(toc_rows)
while i < n_rows:
    page, raw = toc_rows[i]
    r = raw.strip()
    # yl01 形态：章标题跨行（行A 无章码 + 行B 以 (05xxxx) 结尾）→ 合并，续吞页码行
    if (not re.search(r"\((?:05\d{4}|\d{1,3})\)\s*$", r)
            and i + 1 < n_rows
            and re.search(r"\(05\d{4}\)\s*$", toc_rows[i + 1][1].strip())):
        r = r + toc_rows[i + 1][1].strip()
        i += 1
        if i + 1 < n_rows:  # 续吞紧跟的纯页码行
            m_pg2 = re.fullmatch(r"[.…·\s]+\((\d{1,3})\)\s*", toc_rows[i + 1][1].strip())
            if m_pg2:
                r = r + toc_rows[i + 1][1].strip()
                i += 1
    # 长标题拆行：标题行以省略号结尾且无页码 → 与下一行（纯页码行）合并
    # sz08 实测：单「…」字符点线也存在（TOC P12 子目行 7.），故 {1,}
    m_pg = re.match(r"^(.*?)\s*[.…·]{1,}\s*\((\d{1,3})\)\s*$", r)
    if not m_pg and i + 1 < n_rows and re.fullmatch(r"[.…·\s]+\(\d{1,3}\)\s*", toc_rows[i + 1][1]):
        nxt = toc_rows[i + 1][1]
        m2 = re.search(r"\((\d{1,3})\)", nxt)
        r2 = r + nxt
        m_pg = re.match(r"^(.*?)\s*[.…·]{2,}\s*\((\d{1,3})\)\s*$", r2)
        if m_pg:
            r = r2
            i += 1  # 吞并页码行
    # 扉页残余短行（目/录等 ≤2 字）丢弃留痕
    if len(re.sub(r"[…·\s]", "", r)) <= 2 and not re.search(r"\(\d+\)", r):
        i += 1
        continue
    title = m_pg.group(1).strip() if m_pg else r.strip()
    print_page = int(m_pg.group(2)) if m_pg else None
    raw = r
    # 章行（无页码）
    cm = CH_RE.match(raw.replace("　", " ").strip())
    if cm and print_page is None:
        cur_ch_no = "第%s章" % cm.group(1)
        cur_ch_code = cm.group(3)
        seq += 1
        records.append({"seq": seq, "id": "TOC-%04d" % seq, "level": "章行",
                        "ref_kind": "章", "chapter_code": cur_ch_code, "chapter_no": cur_ch_no,
                        "title": "%s%s(%s)" % (cur_ch_no, cm.group(2), cur_ch_code),
                        "raw_line": raw, "print_page": None,
                        "pdf_page": None, "toc_page": page})
        i += 1
        continue
    # 附录标题行（无页码）
    if print_page is None and re.fullmatch(r"附\s*录", title.replace("　", "")):
        seq += 1
        records.append({"seq": seq, "id": "TOC-%04d" % seq, "level": "附录行",
                        "ref_kind": "附录", "chapter_code": None, "chapter_no": None,
                        "title": "附录", "raw_line": raw, "print_page": None,
                        "pdf_page": None, "toc_page": page})
        i += 1
        continue
    # 无页码行且非章行 → 留痕不归类
    if print_page is None:
        seq += 1
        records.append({"seq": seq, "id": "TOC-%04d" % seq, "level": "其他行",
                        "ref_kind": "其他", "chapter_code": cur_ch_code, "chapter_no": cur_ch_no,
                        "title": title, "raw_line": raw, "print_page": None,
                        "pdf_page": None, "toc_page": page})
        i += 1
        continue
    pdf_page = print_page + OFFSET
    if "册" in title and "说" in title and len(title) <= 8:
        level, kind = "册说明行", "册说明"
    elif title.startswith("说"):
        level, kind = "说明行", "章说明"
    elif "计算规则" in title:
        level, kind = "规则行", "计算规则"
    elif title.startswith("附录") or "取定表" in title or "附表" in title:
        level, kind = "附表行", "附表"
    elif SEC_RE.match(title):
        level, kind = "节行", "节"
    elif SUB_RE.match(title):
        level, kind = "子目行", "子目"
    elif title.startswith("第") and "章" in title:
        level, kind = "章行", "章"
    else:
        level, kind = "其他行", "其他"
    seq += 1
    records.append({"seq": seq, "id": "TOC-%04d" % seq, "level": level, "ref_kind": kind,
                    "chapter_code": cur_ch_code, "chapter_no": cur_ch_no,
                    "title": title, "raw_line": raw,
                    "print_page": print_page, "pdf_page": pdf_page, "toc_page": page})
    i += 1

from collections import Counter
lv_cnt = Counter(r["level"] for r in records)
print("目录行:", len(records), dict(lv_cnt))
json.dump({"meta": {"source": "nowm.pdf 目录区 P10-13 双栏重组", "offset": OFFSET},
           "rows": records},
          open(BASE + r"\yl01_toc.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ============================== 二、条文层 ==============================
FULL = json.load(open(BASE + r"\md_extract_full.json", encoding="utf-8"))
IDX = json.load(open(BASE + r"\md_index.json", encoding="utf-8"))
blocks = FULL["blocks"]

desc_rules = []
did = 0


def print_page_of(page):
    """物理页 → 印刷页（zone 函数驱动，坑 51 根治：禁内联硬编码偏移）。
    yl01 分区实测（2026-10-17，页脚 8.8pt span 按 x 坐标排序判读）：
    P1-5 无印刷页码；总说明 P6-9 印=物理−5；目录区 P10-15（含 P14-15 空白页）印=物理−9；
    正文（含章扉页）P16-342 印=物理−OFFSET(15)。任一 zone 偏移改动只改本函数。"""
    if not page:
        return None
    if page <= 5:
        return None
    if page <= 9:
        return page - 5
    if page <= 15:
        return page - 9
    return page - OFFSET


def add_rule(block_type, kind, ch_code, text, page, src_blks):
    global did
    did += 1
    desc_rules.append({
        "section_id": ("GS-%03d" % did if block_type == "总说明" else
                       "CS-%03d" % did if block_type == "册说明" else
                       "ZS-%03d" % did if block_type == "章说明" else
                       "JR-%03d" % did if block_type == "计算规则" else "FB-%03d" % did),
        "block_type": block_type, "md_kind": kind, "chapter_code": ch_code,
        "seq": did, "page": page,
        "print_page": print_page_of(page),
        "text": text, "src_blks": str(src_blks),
    })


# 册说明：P10 h2 标题块（目录区的「册　说　明」普通段不带 kind，防误命中）
in_gs = False
cur_pre = None  # sz11：总说明（P6-9）与册说明（P14-15）双区段
buf, zs_buf = [], []
for b in blocks:
    txt = b["text"].strip() if b["type"] == "para" else ""
    if b["type"] == "para" and b.get("kind") == "h2":
        t2 = txt.replace("　", "").replace(" ", "")
        if re.fullmatch(r"总说明", t2):
            in_gs, cur_pre = True, "总说明"
            continue
        if re.fullmatch(r"册说明", t2):
            in_gs, cur_pre = True, "册说明"
            continue
        if in_gs:  # 其他 h2（目录标题等）→ 前置区结束
            in_gs, cur_pre = False, None
            continue
    if b["type"] == "para" and b.get("kind") == "h1":
        break
    if in_gs and txt:
        (zs_buf if cur_pre == "总说明" else buf).append(b)

# 册说明按条切（一、二、… 条目起始；续行直拼）
def split_rules(paras, item_re):
    """段落流 → 条目列表；条目边界=编号行（一、二、…），续行一律拼入当前条
    （多句续段不因句号断开——sz05 坑㉕ 同源：条目边界只认编号头）"""
    items = []
    cur = None
    for b in paras:
        t = b["text"].strip()
        if item_re.match(t):
            if cur:
                items.append(cur)
            cur = {"text": t, "blks": [b["no"]], "page": b["page"]}
        elif cur is not None:
            cur["text"] += t
            cur["blks"].append(b["no"])
        else:
            # 无编号头的孤立段（留痕独立条）
            cur = {"text": t, "blks": [b["no"]], "page": b["page"]}
    if cur:
        items.append(cur)
    return items


GS_RE = re.compile(r"^[一二三四五六七八九十]+、")
zs_items = split_rules(zs_buf, GS_RE)
for it in zs_items:
    add_rule("总说明", "总说明", None, it["text"], it["page"], it["blks"])
print("总说明条目:", len(zs_items))
gs_items = split_rules(buf, GS_RE)
for it in gs_items:
    add_rule("册说明", "册说明", None, it["text"], it["page"], it["blks"])
print("册说明条目:", len(gs_items))

# 章区：## 说明 / ## 工程量计算规则（md h2 块，chapter 归属）
cur_ch = None
cur_zone = None  # None / '说明' / '规则'
zone_buf = []
for b in blocks:
    if b["type"] == "para" and b.get("kind") == "h2":
        t = b["text"].replace("　", "").replace(" ", "")
        # 先结算上一个区
        if cur_zone and zone_buf:
            zone_items = split_rules(zone_buf, GS_RE)
            for it in zone_items:
                add_rule("章说明" if cur_zone == "说明" else "计算规则",
                         cur_zone, cur_ch, it["text"], it["page"], it["blks"])
        if t.startswith("说明") or t == "说明":
            cur_zone, zone_buf = "说明", []
        elif "计算规则" in t:
            cur_zone, zone_buf = "计算规则", []
        else:
            cur_zone, zone_buf = None, []
        continue
    if b["type"] == "para" and b.get("kind") == "h1":
        if cur_zone and zone_buf:
            zone_items = split_rules(zone_buf, GS_RE)
            for it in zone_items:
                add_rule("章说明" if cur_zone == "说明" else "计算规则",
                         cur_zone, cur_ch, it["text"], it["page"], it["blks"])
        cur_ch = b["chapter_code"]
        cur_zone, zone_buf = None, []
        continue
    if cur_zone and b["type"] == "para" and b["text"].strip():
        zone_buf.append(b)
    elif cur_zone and b["type"] == "table":
        # 表=子目区开始，结算说明/规则区
        zone_items = split_rules(zone_buf, GS_RE)
        for it in zone_items:
            add_rule("章说明" if cur_zone == "说明" else "计算规则",
                     cur_zone, cur_ch, it["text"], it["page"], it["blks"])
        cur_zone, zone_buf = None, []
# 尾部结算
if cur_zone and zone_buf:
    zone_items = split_rules(zone_buf, GS_RE)
    for it in zone_items:
        add_rule("章说明" if cur_zone == "说明" else "计算规则",
                 cur_zone, cur_ch, it["text"], it["page"], it["blks"])

# 附表：附录区材料预算价格取定表（13 表块拍平一条）
fb_blks = []
fb_title_page = None
for b in blocks:
    if b["type"] == "table" and b.get("ttype") == "附表":
        fb_blks.append(b)
    if b["type"] == "para" and "材料预算价格取定表" in b["text"]:
        fb_title_page = b["page"]
if fb_blks:
    cells = []
    for b in fb_blks:
        for r in b["rows"]:
            cells.append("｜".join(c for c in r if c))
    add_rule("附表", "附表", None, "材料预算价格取定表（附录）：" + " ⁃ ".join(cells),
             fb_title_page or fb_blks[0]["page"], [b["no"] for b in fb_blks])

bt_cnt = Counter(r["block_type"] for r in desc_rules)
print("条文层:", len(desc_rules), dict(bt_cnt))
json.dump({"meta": {"source": "md_extract_full.json 条文切片",
                    "n": len(desc_rules)},
           "rules": desc_rules},
          open(BASE + r"\yl01_desc_rules.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("written yl01_toc.json / yl01_desc_rules.json")
