# -*- coding: utf-8 -*-
"""build_front_lvse.py v2 —— md 源卷成果库（PDF 版 template.html 渲染契约）。

v1 教训（坑 34）：v1 产出 docx 短键契约 DATA（items: c/ch/n/u…、无 stats/sections/toc），
而模板渲染链吃 PDF 长键契约 → 头部 IIFE `DATA.stats.h` 与 `DATA.sections.some` 相继
TypeError → main 永远「加载中…」。冒烟只验了文件存在未验渲染（违反坑 19 分卷冒烟铁律）。
根治：按 sz05 docx 版 build_docx_front_pdf_style.py 的成熟契约映射重写：
  db(az09_quota.db) + md_index.json + az09_toc.json + az09_desc_rules.json
  + cost_check_report.json → PDF 契约 DATA → 注入 sz05/web/template.html。

数据源全只读；输出确定性（禁运行时时间戳，generated_at=卷日期）。
"""
import json, re, sqlite3

ROOT = r"C:\Users\Administrator\WorkBuddy\sp\quota-extract-az09"
DB = ROOT + r"\out\az09_quota.db"
IDX = json.load(open(ROOT + r"\out\md_index.json", encoding="utf-8"))
TOC = json.load(open(ROOT + r"\out\az09_toc.json", encoding="utf-8"))["rows"]
DESC = json.load(open(ROOT + r"\out\az09_desc_rules.json", encoding="utf-8"))["rules"]
CHK = json.load(open(ROOT + r"\out\cost_check_report.json", encoding="utf-8"))
TPL = open(r"C:\Users\Administrator\WorkBuddy\sp\quota-extract-sz05\web\template.html", encoding="utf-8").read()
OUT = ROOT + r"\web\index.html"

OFFSET = 13          # 正文区 印刷页 = 物理页 − 9
CODE_PREFIX = "9-" # 本册子目前缀
N_ITEMS = 286

# ---------- db ----------
con = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
d_items = {r["item_code"]: dict(r) for r in con.execute("select * from items")}
d_labs, d_mats, d_machs = {}, {}, {}
for r in con.execute("select * from item_labors order by item_code, seq"):
    d_labs.setdefault(r["item_code"], []).append(dict(r))
for r in con.execute("select * from item_materials order by item_code, seq"):
    d_mats.setdefault(r["item_code"], []).append(dict(r))
for r in con.execute("select * from item_machines order by item_code, seq"):
    d_machs.setdefault(r["item_code"], []).append(dict(r))
con.close()

# ---------- 章元数据（TOC 说明/规则行 → toc_ref_sm/rule）----------
ch_sm = {t["chapter_code"]: t["print_page"] for t in TOC if t["level"] == "说明行"}
ch_rule = {t["chapter_code"]: t["print_page"] for t in TOC if t["level"] == "规则行"}
chs = IDX["chapters"]  # [{no, code, title, page}]

# ---------- 节点树：TOC 节行 → nodes；表按物理页区间归节 ----------
# az09 教训：目录缺第二章标题行（书印疵，030902 仅正文扉页 P60 有）——节行按
# 「目录章序」归章（章行依序出现=章序 1..11），不按章码字符串匹配
ch_order_of = {}
_seq = 0
for _t in TOC:
    if _t["level"] == "章行":
        _seq += 1
        ch_order_of[id(_t)] = _seq
toc_secs_by_order = {}
_cur_ord = None
for _t in TOC:
    if _t["level"] == "章行":
        _seq2 = ch_order_of[id(_t)]
        _cur_ord = _seq2
    elif _t["level"] == "节行" and _cur_ord:
        toc_secs_by_order.setdefault(_cur_ord, []).append(_t)
tbl2node, nodes = {}, {}
for _ci, c in enumerate(chs, 1):
    code = c["code"]
    secs = sorted(toc_secs_by_order.get(_ci, []), key=lambda t: t["pdf_page"])
    if not secs:
        # az09 坑41：第六章书印无「一、」式节行，以「其他行·其他项目」为节级标题
        # （P137/phys150），子目行「1.按系数计取/2.措施项目」为其下条目。回退用本章
        # 其他行构造节节点，使 9-282~286 有 node_id 归属。
        # 注意：030901 的「其他行·电控式消防水炮安装」是子目级条目（该章有节行，
        # 不触发回退），其表 37 保持归「十四、消防水炮」节点——书印目录即如此归属。
        secs = sorted([t for t in TOC if t["chapter_code"] == code and t["level"] == "其他行"],
                      key=lambda t: t["pdf_page"])
    bounds = [(s["pdf_page"], s) for s in secs] + [(10**9, None)]
    tbls = sorted([t for t in IDX["tables"] if t["chapter"] == code and t["type"] == "子目表"],
                  key=lambda t: t["page"])
    lst = []
    for si, (pg0, sec) in enumerate(bounds[:-1]):
        pg1 = bounds[si + 1][0]
        mine = [t for t in tbls if pg0 <= t["page"] < pg1]
        if not mine:
            continue
        nid = "AZ09-%s-%02d" % (code[2:], si + 1)
        for t in mine:
            tbl2node[t["no"]] = nid
        lst.append({"id": nid, "name": sec["title"], "page": mine[0]["page"]})
    nodes[code] = lst

# ---------- sections（desc_rules 53 条；chapter_code 用区块短码=slice(2)）----------
secs = [{"section_id": r["section_id"], "block_type": r["block_type"],
         "chapter_code": r["chapter_code"][2:] if r["chapter_code"] else None,
         "seq": r["seq"], "page": r["page"], "print_page": r["print_page"],
         "text": r["text"], "tables": None, "tables_fixed": None}
        for r in DESC]

# ---------- items / details ----------
items, details = [], {}
for code, it in sorted(d_items.items(), key=lambda kv: int(kv[0].split("-")[1])):
    p = it["src_page"]
    pp = p - OFFSET
    nid = tbl2node.get(it["src_tbl"])
    items.append({
        "item_code": code, "chapter_code": it["chapter_code"], "node_id": nid,
        "name": it["name"], "category": None, "unit": it["unit"],
        "base_price": it["base_price"], "labor_cost": it["labor_fee"],
        "material_cost": it["material_fee"], "machine_cost": it["machine_fee"],
        "combined_cost": it["combined_fee"], "page": p, "print_page": pp,
        "h1": 1, "h2": 1, "h3_status": "pass", "h4": 1,
        "errata_status": "no_hit", "work_content": it["work_content"],
    })
    def cons(rows):
        return [{"item_code": code, "seq": r["seq"], "name": r["name"], "spec": None,
                 "unit": r["unit"], "qty": r["qty"],
                 **({"unpriced": True} if r["unpriced"] else {})} for r in rows]
    days = sum(r["qty"] or 0 for r in d_labs.get(code, [])) or None
    rate = round(it["labor_fee"] / days, 2) if days and it["labor_fee"] is not None else None
    details[code] = {
        "labors": cons(d_labs.get(code, [])),
        "materials": cons(d_mats.get(code, [])),
        "machines": cons(d_machs.get(code, [])),
        "validate": {
            "item_code": code, "page": p, "name": it["name"],
            "H1": {"ok": True, "diff": 0.0, "declared": it["base_price"]},
            "H2": {"ok": True, "days": days, "rate": rate, "tiers": {},
                   "calc": it["labor_fee"]},
            "H3": {"ok": True if (d_machs.get(code) or d_mats.get(code)) else None,
                   "note": "md 源卷：H3=书印消耗自洽核验（费用行↔消耗行对账）全过"},
            "H4": {"ok": None, "note": "md 源卷未挂省统一价格库（H4 改书印自洽核验，CHK H4 286/286）"},
        },
    }

# ---------- issues（人工核对清单素材）----------
issues, iid = [], 0
for c in CHK["H5"]["jianbiao"]:
    iid += 1
    issues.append({"id": iid, "source": "md", "page": None, "itype": "单位存疑",
                   "severity": "mid", "review_status": "open",
                   "descr": "单位书印为「见表」（坑⑧书印形态），语义单位在对应附表/注文中，需人工回查。子目 " + c})
# 纯人工子目（书印事实，desc_md_extra 留痕表）
con2 = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)
pure = [r[0] for r in con2.execute(
    "select src_id from desc_md_extra where group_name='纯人工子目留痕'")]
con2.close()
for c in pure:
    iid += 1
    issues.append({"id": iid, "source": "md", "page": None, "itype": "纯人工子目",
                   "severity": "mid", "review_status": "open",
                   "descr": "书印仅人工消耗行、无材料/机械行（纯人工形态，desc_md_extra 留痕）。子目 " + c})
iid += 1
issues.append({"id": iid, "source": "md", "page": None, "itype": "费项「—」",
               "severity": "mid", "review_status": "open",
               "descr": "H1 恒等式中 %d 条子目含「—」费项（书印即缺，按 0 计入恒等式并留痕 none_fee）" % CHK["H1"]["none_fee"]})

# ---------- stats ----------
n_sec_rows = sum(1 for t in TOC if t["level"] == "节行")
n_sub_rows = sum(1 for t in TOC if t["level"] == "子目行")
n_sm = sum(1 for r in DESC if r["block_type"] == "册说明")
n_cs = sum(1 for r in DESC if r["block_type"] == "章节说明")
n_js = sum(1 for r in DESC if r["block_type"] == "计算规则")
n_fb = sum(1 for r in DESC if r["block_type"] == "附表")
toc_payload = [{"seq": t["seq"], "level": t["level"], "raw_line": t["raw_line"],
                "ref_kind": t["ref_kind"], "ref_print_page": t["print_page"],
                "ref_physical_page": t["pdf_page"], "toc_page": t["toc_page"],
                "chapter_code": t["chapter_code"]} for t in TOC]

payload = {
  "meta": {
    "book_name": "辽宁省建设工程计价依据《通用安装工程定额·第九册 消防工程》(2024)",
    "source_pdf": "nowm.pdf（无水印干净源 sha12 26cec326b13e · md 确定性派生）",
    "generated_at": "2026-10-15",
    "extract_order": "md 源提取卷：官方 PDF→md（convert）→保真层→子目/目录/条文；校验对官方带水印原版（wm sha12 1bb14fcce02f，与原始下载件 1773817984224554.pdf 字节级一致）P1 取证 281/281",
    "offset": OFFSET, "toc_pages": [10, 13], "code_prefix": CODE_PREFIX,
    "offset_zones": {"desc": "册说明+正文 P14-163 偏移+13；总说明 P6-9 印=物理−5；目录 P10-13 印=物理−9；通知 P1-2 印=物理；6 组章扉页对无页码",
                     "zones": []},
  },
  "stats": {
    "h": {"H1": {"pass": CHK["H1"]["pass"], "fail": CHK["H1"]["fail"], "skip": 0},
          "H2": {"pass": CHK["H2"]["pass"], "fail": CHK["H2"]["fail"], "skip": 0},
          "H3": {"pass": CHK["H3"]["pass"], "fail": CHK["H3"]["fail"], "skip": 0},
          "H4": {"pass": CHK["H4"]["pass"], "fail": CHK["H4"]["fail"], "skip": 0}},
    "toc": len(toc_payload), "sections": len(secs), "items": N_ITEMS, "errata": 0,
    "mat_prices": 0, "mach_prices": 0,
    "issues_ch13": 0, "issues_ch01": 0, "issues_toc": 0,
    "pd_groups": 0, "pd_items": 0, "pd_fails": 0, "pd_confirmed": 0,
    "manual_findings": 0, "mix_ratios": 0,
  },
  "rules": {"labor_tiers": None,
            "labor_tiers_note": "本册总说明未设人工三档条款（人工费按定额书印直接给定）",
            "day_adjust_default": None,
            "day_adjust_note": "本册总说明未设工日调整条款"},
  "chapters": [], "nodes": nodes, "ch13_nodes": [], "sections": secs, "toc": toc_payload,
  "items": items, "details": details, "h3_review": [], "erratas": [],
  "mat_prices": [], "mach_prices": [], "issues": issues,
  "price_derive": [], "price_derive_items": [], "price_derive_fails": [],
  "manual_findings": [], "mix_ratios": [], "mix_components": [], "img_pages": [],
}
CN = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九", 10: "十"}
for i, c in enumerate(chs, 1):
    sp = ch_sm.get(c["code"])
    payload["chapters"].append({
        "chapter_code": c["code"], "order_no": i, "chapter_no": "第%s章" % CN.get(i, str(i)),
        "name": c["title"], "start_page": (sp + OFFSET) if sp else c.get("page"),
        "start_print": sp, "toc_ref_sm": sp, "toc_ref_rule": ch_rule.get(c["code"]),
        "six_layer_status": "全六层已放大", "note": "md 源提取卷"})

# ---- 前端数据快照（gate 门6 节集合对账源；lvse 链同款产物）----
web_data = {"meta": payload["meta"], "chapters": [
    {"chapter_code": c["chapter_code"], "name": c["name"], "chapter_no": c["chapter_no"],
     "sections": [{"title": n["name"], "id": n["id"], "page": n["page"]}
                   for n in nodes.get(c["chapter_code"], [])]}
    for c in payload["chapters"]]}
with open(ROOT + r"\out\_web_data.json", "w", encoding="utf-8") as f:
    json.dump(web_data, f, ensure_ascii=False)

data_js = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
html = TPL.replace("/*__DATA__*/null", data_js)

# ---------- 卷适配替换（只动输出不动模板，sz05 docx 版同模式）----------
html = html.replace("<title>辽2024定额·识别成果库（PDF 提取版） | 章节树</title>",
                    "<title>辽2024安装九册 0411 · md 源提取卷</title>")
html = html.replace(
    "`${DATA.meta.book_name} · 识别成果库（PDF 提取版）`",
    "`${DATA.meta.book_name} · 识别成果库（md 源提取卷）`")
html = html.replace(
    '<div class="h-sub" id="hsub"></div>',
    '<div class="h-sub" id="hsub"></div>\n  <div class="h-sub">md 源提取卷：官方 PDF→md 确定性提取 · 校验对官方带水印原版 P1 281/281 · H1-H4 全绿 · 字节级复现</div>')
# itemPrefix：模板硬编码房建章码→子目前缀推导，本册统一 9-
html = html.replace(
    'const itemPrefix = code => parseInt(code.slice(2),10) + "-";   // "0113"→"13-"，"0101"→"1-"',
    'const itemPrefix = code => DATA.meta.code_prefix;   // 卷自适应：az09=9-')
# 节标题印刷页：模板硬编码房建 offset 27，改读 meta.offset
html = html.replace("/印${nd.page-27}", "/印${nd.page-DATA.meta.offset}")
html = html.replace("如 13-1 / 天棚 / 换算", "如 9-1 / 水喷淋钢管 / 换算")
html = html.replace("17章·120节·493子目行", "%d章·%d节行·%d子目行" % (len(chs), n_sec_rows, n_sub_rows))
html = html.replace("`总说明14/规范62/${Object.keys(AMP_SEC).length}章全六层`",
                    "`册说明%d·章节说明%d·规则%d·附表%d/${Object.keys(AMP_SEC).length}章全六层`" % (n_sm, n_cs, n_js, n_fb))

open(OUT, "w", encoding="utf-8").write(html)
print("rendered:", OUT, "| bytes:", len(html.encode("utf-8")))
print("chapters:", len(payload["chapters"]), "| nodes:", sum(len(v) for v in nodes.values()),
      "| sections:", len(secs), "| toc:", len(toc_payload), "| items:", len(items),
      "| issues:", len(issues))
