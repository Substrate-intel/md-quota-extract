---
name: md-quota-extract
description: 官方定额 PDF → Markdown → 结构化定额库（SQLite + 前端成果库 + 九门门控）的确定性提取管线。适用于只有官方 PDF（含水印扫描版）、拿不到 Word/docx 源的定额、消耗量标准、计价规范类文档。基准卷：辽宁2024《绿色建筑工程定额》269 页全链验证（487 子目/九门全绿/字节级复现/P1 官方原版取证 487/487）。触发词：PDF 转 markdown、md 定额提取、PDF→md→定额库、无 docx 源定额结构化、绿色建筑式提取、md 源管线。
version: 1.0.0
---

# md-quota-extract：定额 PDF → md → 结构化库 确定性提取管线

> 姊妹 skill：`docx-quota-extract`（有 Word 源时**优先走 docx 链**——token 更低、无转换层误差）。
> 本 skill 解决「只有 PDF」的场景：PDF 先确定性转为 Markdown 权威提取源，再对标 docx 版
> 输出契约完成结构化（db schema 同构 + 前端 + 门控）。

## 核心架构：双源

| 源 | 用途 | 说明 |
|---|---|---|
| **nowm.pdf**（无水印干净版） | 提取 | convert → md（字节级可复现，锚定 sha12） |
| **官方原版 PDF**（含水印） | 校验 | P1 取证：编码+基价在官方原版页文本命中 N/N |

用户拿不到 nowm 版时，先用官方原版转换（水印行首 token 剔除，见坑 2），双源退化为单源+水印清洗留痕。

## 核心原则（违反即返工）

1. **md 是权威提取源**：convert 产物锚定 sha12，禁运行时时间戳；下游只读。
2. **保真层只读**：`md_extract_full.json` 是唯一事实源；语义修正一律 overlay/留痕（`*_raw` 后缀），不回改。
3. **确定性复现**：全链产物禁 `generated_at` 类运行时时间；有意变更后门控全绿 → `gate.py --make-manifest` 刷指纹 → 复跑。
4. **疑点留痕不静默**：差异/残余/跳过全部进 log/DB 留痕表过门控对账，禁静默丢弃。
5. **前端完成态=渲染级冒烟全绿**：文件产出不算完成（坑 11 血泪）。
6. **复制改造，禁直接运行**：skill 目录脚本保留基准卷（lvse）参数约 30 处硬编码。新卷开工 = 复制 scripts/ → 按 `references/volume_params.md` 换参 → `check_volume_params.py` 零残留（退出码 0）才开工。

## 管线总纲（11 阶段，顺序执行）

```
nowm.pdf ──(0) convert_pdf_to_md ──> source.md [页锚 Pn]
      ├─(1) extract_md      → md_extract_full.json + md_index.json   [保真层]
      ├─(2) parse_items     → lvse_items.json（子目层，名沿用基准卷产物名）
      ├─(7) parse_desc      → lvse_toc.json + lvse_desc_rules.json   [目录/条文]
      ├─(5) finalize        → lvse_quota.db（SQLite 七表）
      ├─(6) cost_check      → cost_check_report.json（H1-H6 + P1 官方原版取证）
      ├─(9) build_front     → web/index.html（PDF 长键契约 DATA 注入）
      ├─(9b) smoke_front    → 渲染级冒烟（node DOM stub，22 项）
      └─(10) gate           → baseline_manifest.json（九门 + 双源锚定）
```

| # | 脚本 | 职责 | 关键验收 |
|---|---|---|---|
| 0 | convert_pdf_to_md.py | 裸 fitz：字号分级 + find_tables→md 表 + 水印行首剔除 + 页码标定 | md 字节级可复现；页锚覆盖无页码区段排除正确 |
| 1 | extract_md.py | md→块结构（kind: h1/h2/para/table），零语义过滤 | blocks 稳定、parse_issues=0 |
| 2 | parse_items.py | 子目解析：行判别三法 + 消耗行 kind 链 + 双遍扫描 | 编码连续零缺失；unit/work/name 零空 |
| 7 | parse_desc.py | 目录（nowm.pdf dict 双栏重组）+ 条文按「条」切分 | 节集合与目录全等；条文字节级回读 |
| 5 | finalize.py | SQLite：items/labors/materials/machines/toc/desc_rules/desc_md_extra | 行数=json 计数 |
| 6 | cost_check.py | H1 恒等式（项数按卷校准）/H2-H6/P1 | H1/H6/P1 fail=0 |
| 9 | build_front.py | PDF 长键契约 DATA（stats/sections/toc/items/details/nodes/REVIEW）+ 卷适配替换 | 契约断言全过 |
| 9b | smoke_front.mjs | node + DOM stub 执行启动链 + 13 视图路由 | 22/22 全绿 |
| 10 | gate.py | 九门 + manifest 基线 | 九门全绿 + 端到端字节级复现 |

## 详细工作流

1. **预检**：两源 sha12、册结构（章/节/附表）、页码口径分区标定、水印形态侦察；
2. **换卷参数**（volume_params.md 逐项）→ `check_volume_params.py` 零残留；
3. 11 阶段顺序跑，疑点逐条取证（禁静默）；
4. 九门全绿 → 刷指纹 → 端到端重跑字节级一致 → 渲染级冒烟全绿 → 交付报告（覆盖清单+人工复核项）。

## 新卷标准动作（基准卷实测 1 个工作日内收官）

预检 → 换参+守卫 → 转换层标定（字号/水印/页码三件）→ 阶段 1-2 自测（单章先验证再放大）→
阶段 5-10 → 门控闭环 → 交付报告 → 按 `references/iteration-protocol.md` 强制回写本 skill。
