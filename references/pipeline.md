# 11 阶段管线详解（输入/输出/验收/复用要点）

> 脚本均为基准卷（lvse·绿色建筑定额，487 子目）验证版；新卷须逐项替换卷参数
> （见 volume_params.md），替换后先全自测再放大。

## 数据流总图

```
nowm.pdf ──(0)convert──> source.md [<!-- Pn --> 页锚]
      │
      ├─(1)extract_md──> md_extract_full.json [保真层·只读] + md_index.json
      ├─(2)parse_items─> lvse_items.json
      ├─(7)parse_desc──> lvse_toc.json + lvse_desc_rules.json
      ├─(5)finalize────> lvse_quota.db（items/item_labors/item_materials/item_machines/
      │                  toc/desc_rules/desc_md_extra/book_meta + src_page 列）
      ├─(6)cost_check──> cost_check_report.json
      ├─(9)build_front─> web/index.html（template 注入 PDF 长键契约 DATA）
      ├─(9b)smoke_front> 渲染级冒烟（node DOM stub）
      └─(10)gate───────> baseline_manifest.json（10 产物 sha256 + 双源锚定）
```

## 阶段 0｜convert_pdf_to_md.py —— PDF→md 转换层（本链特有）

- **输入**：nowm.pdf（先算 sha12 作全链锚）。
- **输出**：md 文档（字号分级：主标题→H1 章、次级→H2、正文、定额表；`find_tables()`→markdown 表；`<!-- Pn -->` 物理页锚）。
- **要点**：
  - **禁 pymupdf4llm**（坑 1：本机 import 即段错误）；裸 fitz 自研；
  - 水印**不 redact**（坑 2：旋转水印 bbox 轴对齐化=整页抹除），改单元格级行首孤立 token 剔除——行首锚定防「基价」双面字误伤；
  - E-BZ 小数空格归一 `(\d)\.\s+(\d)→\1.\2`；
  - 页码标定（坑 3）：E-BZ 页码为散字单字符行、位于**外侧边**（偶页左/奇页右），按 x 左→右重组；分区 offset（正文/目录分开标定，无页码扉页对排除）。
- **验收**：md 重跑字节级一致；页锚数=总页数−无页码页；抽查 3 处表行与 PDF 目视一致。

## 阶段 1｜extract_md.py —— 保真层

- **输出**：`md_extract_full.json`：`{meta:{sha12…}, blocks:[{kind:h1|h2|para|table, text, table_no, rows}]}` + `md_index.json`（章码/表类型清单）。
- **要点**：章标题块**必须带 `kind:"h1"`**（坑 4：`# ` 前缀剥离后文本判界全失效）；零语义过滤。
- **验收**：块数稳定；parse_issues=0；重跑字节级一致。

## 阶段 2｜parse_items.py —— 子目解析（最核心）

- **输出**：`lvse_items.json`：子目全集（编码/名称/单位/工作内容/四项费用/人材机消耗）。
- **结构认知**：定额表 = **列=子目、行=费用/消耗**；md 合并单元格 = 首行有值后续空（≠ docx 纵向合并的重复值形态，坑 5）。
- **行判别三法**（坑 5）：①消耗行=c0 空 + 前 kind 链式承接；②名称行=r[1] 无值 + r[3:] 非数字文本；③跨列标签 hfill 横向填充；费用行（费用名在 r[1]）用 `"(元)" in joined` 检测；规格/档位行放行（纯数字/每增减N/≤N）。
- **工作内容/单位双遍扫描**（坑 6）：md 把两者拆成独立行，单遍状态机被先出现的行截断；分号结尾的「N.」子行是工作内容延续不 break。
- **验收**：编码连续零缺失；unit/work/name 零空；H1 预跑全过。

## 阶段 7｜parse_desc.py —— 目录 + 条文

- **目录不走 md**（坑 7：双栏排版全文序交错 + md 表格化破坏坐标）——从 nowm.pdf 目录页 dict 直接重建：x 分栏 + 栏内 y 聚类 + 长标题/页码行合并。
- **节标题跟表验证**（坑 8）：其后 6 块内须有表格，防说明区折行条目污染 sections。
- **条文切分**：按「条」号锚切；续行直拼/子项换行（同 docx 链坑 11/13 形态）。
- **验收**：节集合与目录节行集合全等；章内页码单调；条文字节级回读 N/N。

## 阶段 5｜finalize.py —— SQLite 落库

- **表**：items/item_labors/item_materials/item_machines/toc/desc_rules/desc_md_extra（留痕）/book_meta；items 带 `src_page` 列（表所在物理页）。
- **验收**：门7 DB 对账（每表行数 = json 计数）。

## 阶段 6｜cost_check.py —— 造价逻辑核

| 项 | 逻辑 | 验收 |
|---|---|---|
| H1 | 基价恒等式——**项数按卷校准**（坑 9：可能三项/四项含综合费，开工前用已知好卷样例验证） | fail=0 |
| H2 | 人工费聚类/费率带宽（带宽按本卷实测） | fail=0 离群留痕 |
| H3/H4 | 消耗结构自洽（费用行↔消耗行对账；无省价格库时改书印自洽口径） | fail=0 |
| H5 | 单位白名单（卷特有单位入表；「见表」skip 留痕） | fail=0 |
| H6 | 结构完整性（编码连续/单位/工作内容/名称） | 全零 |
| P1 | **官方带水印原版**取证：编码 `(?<!\d)前缀-\s*N(?!\d)` + 基价 `120[\s.]*78`（E-BZ 空格容忍），**作用于未去空白原文**（坑 10） | N/N |

## 阶段 9｜build_front.py —— 前端（PDF 长键契约）

- **输入**：db + md_index + lvse_toc + lvse_desc_rules + cost_check_report + template.html。
- **契约**（坑 11）：`meta(book_name/source/generated_at/extract_order/offset/toc_pages/code_prefix)`、`stats.h{H1-H4}`、`chapters(chapter_code/six_layer_status/toc_ref_sm…)`、`nodes`（节→表→item 归属，页区间法）、`sections(block_type/chapter_code 短码)`、`toc(77 行字段)`、`items(item_code/node_id/h1-h4/errata_status/work_content…)`、`details(labors/materials/machines/validate)`、`issues`（人工核对素材：见表单位/纯人工/费项「—」）。
- **卷适配替换**（模板硬编码点）：itemPrefix 章码推导→`DATA.meta.code_prefix`；节印页 `-27`→`-DATA.meta.offset`；搜索示例/卡片副标题/标题。
- **验收**：DATA 契约断言全过。

## 阶段 9b｜smoke_front.mjs —— 渲染级冒烟（必跑）

- node + 最小 DOM stub 执行内联脚本：启动链零异常 + main 非「加载中」+ 13 视图路由真跑。
- **完成态=冒烟全绿**（坑 11：门控基线只锚「可复现」不锚「可渲染」）。

## 阶段 10｜gate.py —— 九门 + 基线指纹

| 门 | 内容 |
|---|---|
| 1 | 装载完备（blocks/parse_issues=0） |
| 2 | 编码连续零缺失 |
| 3 | unit/work/name 零空 |
| 4 | H1 恒等式 |
| 5 | H3/H4 消耗结构 |
| 6 | 目录对账（节全等/页码单调） |
| 7 | 条文字节级回读 |
| 8 | 基线指纹（manifest sha256；`--make-manifest` 刷） |
| 9 | P1 官方原版取证 N/N |

- **收官**：门1-7/9 绿 → 刷指纹 → 九门全绿 → **端到端全链重跑字节级一致** → 冒烟全绿 → 交付报告。

## M0 预检清单（sz11 补遗，坑 13/16——逐项实测，禁搬上卷参数）

1. 水印载体形态：查 `page.get_xobjects()`——有 Form XObject 走坑 12 指令删除（无则退坑 2）；
2. 章结构三对账：目录章行数 == 正文章数；章码唯一性（重复/错位留痕）；**目录章码 vs 正文章码逐章比对**（sz11 第六章 041105/041106 实证）；
3. 前置区段：总说明/册说明各有无（决定条文双区段收集）；扉页对清单；
4. 页码：抽样 3-5 页**打印页脚字符 y 分布**再定带（sz11 y=350.4）；三区段 offset 各自标定；
5. 单位全集：先 dump 全库 unit 分布一次性补 H5 白名单（禁跑红再逐轮补）；
6. 换参后：`preflight_check.py`（路径/正则试命中/短码/断言占位）→ `check_volume_params.py` 零残留 → 开工。
