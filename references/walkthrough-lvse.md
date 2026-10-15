# 基准卷端到端实录：绿色建筑工程定额（PDF → 能加载成功的首页）

> 本文档是 lvse 卷（辽宁2024《绿色建筑工程定额》，269 页官方 PDF，无 Word 源）的**真实全过程记录**，
> 按实际时序提炼——包括 M7 前端假死事故的发生-定位-修复。新卷照此主线走，每个里程碑的验收数字
> 换成本卷实测值。坑编号对应 pitfalls.md。

## 全过程时间线（12 个里程碑）

### M0 预检与双源定版
- 官方带水印原版 wm.pdf（sha12=6d347c2b6efc，269 页）+ 无水印干净源 nowm.pdf（ac0de6d04eba）；
- **双源架构定版：提取用 nowm、P1 校验用官方 wm**——干净源免水印清洗误差，官方原版做最终取证（版权口径上校验以官方原版为准）；
- 预检产出：两源 sha12、页码口径分区（正文 +9/目录区 +5/扉页对无页码）、册结构（4 章 012001-004）。

### M1 转换层：PDF→md（三坑连环）
- **坑 1**：`import pymupdf4llm` 即段错误 → 弃用，裸 fitz 自研（字号分级 19.7→H1/13.7→H2/10.3→正文/8.8→定额表 + `find_tables()`→md 表）；
- **坑 2**：旋转水印 bbox redact = 整页抹除 → 改单元格级行首孤立 token 剔除（行首锚定防「基价」双面字误伤）；
- **坑 3**：E-BZ 页码散字（每字符一行、外侧边位置）→ y 带+外侧边 x 收集、按 x 左→右重组、分区 offset。
- **验收**：md 285KB，页锚 258/269（扉页对正确排除），重跑字节级一致。

### M2 保真层：md→块结构
- `md_extract_full.json`：1437 块（1210 段落 + 227 表格）+ `md_index.json`（4 章、子目表 214/附表 13/续前 28）；
- **坑 4**：章标题块的 `# ` 前缀被剥离后，所有 `startswith("#")` 边界**静默失效**（册说明 buf 吞掉 848 段）→ 块显式 `kind:"h1"/"h2"`，全部边界检查改 kind 判定。
- **验收**：blocks=1437 稳定、parse_issues=0。

### M3 子目层：487 子目解析（行判别是主战场）
- **坑 5**：md 合并单元格 = 首行有值后续空（≠ docx 纵向合并的每行重复值）→ 消耗行分类链断裂、430 子目 unit 空、254 子目名称空；
- **根治三法**：消耗行=c0 空+前 kind 链式；名称行=r[1] 无值+r[3:] 非数字文本（ci_label_check）+hfill 跨列标签填充；费用行 `"(元)" in joined`；规格/档位行 SPEC_VAL_RE 放行；
- **坑 6**：工作内容/计量单位拆成两行 → 单遍状态机被截断 → **双遍扫描**；分号结尾的「N.」子行是工作内容延续不 break。
- **验收**：487 子目（20-1~20-487）连续零缺失；unit/work/name 全零空；parse_issues=0。

### M4 目录/条文层：不经 md
- **坑 7**：目录双栏排版，md 表格化破坏坐标 → 从 nowm.pdf 目录页 dict 直接重建（x<280/≥280 分栏 + 栏内 y±6.5 聚类）→ 77 行；
- **坑 8**：说明区折行条目命中节标题正则（32 vs 权威 14）→ **跟表验证**（其后 6 块内须有表格；窗口 4 块漏过表距 5 块的案例）→ 14 节全等；
- 条文 53 条：册说明 9 + 章说明 23 + 计算规则 20 + 附表 1。
- **验收**：节集合与目录节行全等、章内页码单调、条文字节级回读 53/53。

### M5 落库
- `lvse_quota.db` 七表：items 487（含 src_page 物理页）/ item_labors 487 / item_materials 2919 / item_machines 652 / toc 77 / desc_rules 53 / desc_md_extra 3（纯人工留痕）+ book_meta。
- **验收**：每表行数 = json 计数（门7 对账）。

### M6 核验：H1 项数坑 + P1 正则坑
- **坑 9**：H1 用三项式（基价=人+材+机）→ 487/487 全红。根因：本卷为**四项制**（人工+材料+机械+综合费，sz05 5-1 样例验证 3277.47=1767.05+17.27+995.83+497.32）→ 四项式 487/487（299 条「—」费项按 0 计并留痕 none_fee）；H2 带宽按本卷实测 15.2%→0-0.16；
- **坑 10**：P1 灵活正则作用于去空白文本 → 44/487 fail（相邻编码粘连 '20-920-10' 误杀 lookbehind）→ **作用于未去空白原文**（编码 `(?<!\d)20-\s*N(?!\d)`、基价 `120[\s.]*78`）→ **对官方 wm 原版取证 487/487**。
- **验收**：H1-H6/P1 全部 fail=0。

### M7 ⚠️ 前端假死事故（本 skill 最有价值的一课）
- **表面状态**：build_front v1 产出了 760KB 的 index.html，**九门全绿 + 端到端字节级复现**——一切指标正常；
- **用户实测**：首页永远「加载中…」；
- **根因两级**：
  1. v1 产出 **docx 短键契约** DATA（items: c/ch/n/u…、无 stats/sections/toc），而模板渲染链吃 **PDF 长键契约**——脚本头部 `DATA.stats.h` 与 `DATA.sections.some` 相继 TypeError，**整个 JS 崩溃**，`#main` 永不替换；
  2. 冒烟只验了「文件存在/大小/DATA 可解析」，**没有执行渲染**——门控基线锚定的就是错配版，所以九门全绿是「可复现的坏文件」；
- **教训**：门控锚「可复现」，不锚「可渲染」。文件产出 ≠ 交付。

### M8 前端 v2：按成熟契约映射重写
- 参照 sz05 docx 版 `build_docx_front_pdf_style.py` 的**契约映射**（已在两卷验证）；
- DATA 全套：meta（book_name/source/generated_at=卷日期/extract_order/offset/toc_pages/code_prefix）、stats.h{H1-H4}、chapters（chapter_code/six_layer_status/toc_ref_sm/rule）、nodes（节→表→item 归属，页区间法）、sections（block_type/chapter_code 短码=slice(2)）、toc、items 长键（item_code/node_id/h1-h4/errata_status/work_content）、details（labors/materials/machines/validate）、issues（人工核对素材）；
- **卷适配替换**（模板硬编码点）：itemPrefix 章码推导→读 `DATA.meta.code_prefix`；节印页 `-27`→`-DATA.meta.offset`；搜索示例/卡片副标题/标题；
- 细节修正：纯人工 3 条（20-11/260/327）从 desc_md_extra 留痕表取（有工日行无材机行），不是「零消耗行」查询。

### M9 渲染级冒烟（完成态的机械定义）
- `smoke_front.mjs`：node + 最小 DOM stub **真执行**内联脚本——
  1. 启动链零异常（buildTree→bindTree→show("gs")→refreshCounts）；
  2. main 非「加载中」；
  3. 契约断言（stats/sections/GS_TYPE/4 章进树/487 子目 node_id 全归属）；
  4. **13 个视图路由逐一真跑**（gs/toc/ch/layer×sm/js/fb/items/review/issues/errata/price/derive/item 详情弹窗）；
- **验收：22/22 全绿。**

### M10 门控闭环（有意变更的正确处理）
- 端到端重跑 build_front → **字节级一致**（sha 前后相同）；
- gate 跑 → 门 8 失配**仅 index.html**（=有意变更，逐个确认归属）→ `--make-manifest` 刷指纹 → 复跑**九门 9/9**。

### M11 收官分发
- portal 注册（VOLUMES 制，现查渲染）+ hosting_map 定性（仅机械/配比拆分卷需条目，本卷无）+ 交付报告（覆盖清单+人工复核项：16「见表」/3 纯人工/299「—」）；
- 成果回流双仓（公开仓四件套+私有仓 db，见 contribution.md）→ webhook 自动协同 → 线上 API 收录（注意 quota-db.js 注册表**随进程重启生效**）。

## 「能加载成功的首页」完成态定义（缺一不可）

1. ✅ `smoke_front.mjs` 22/22 全绿（机械验收）；
2. ✅ 浏览器打开 index.html：首页即渲染（无「加载中」停留）、章节树全章可见、点开任一子目详情弹窗有四项费用+人材机消耗表；
3. ✅ 九门全绿 + 端到端重跑字节级一致 + 刷指纹闭环；
4. ✅ 交付报告 + 人工复核清单落盘。

只满足 3 不满足 1/2 = M7 事故重演（可复现的坏文件）。
