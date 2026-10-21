# CHANGELOG — md-quota-extract

格式：`- 版本 | 日期 | 来源 | 变更摘要`；来源=贡献者标识/卷名；合并须经作者过审（iteration-protocol.md 第四节）。

## v1.10.2 · 2026-10-22 · 爪哥（作者）· check_backflow B 层键名反查 + git 同步判定恢复 API 实查（坑102 同轮补齐）

- **B 层**：VOLUME_META 以目录名为键、值是 `(key, kind, label)`——底座卷目录 `quota-extract` 与键名 `fj` 不同名，原「拼 `quota-extract-<key>` 再正则」误报未注册；改按**值首元反查**，detail 打「目录→key/kind/label」。
- **git 同步判定**：`git_state` 在 ls-remote 失败时曾回退本地 `origin/main` 引用——API 通道推送后该引用不前移，网络抖动即假红（xj17 实证 `synced=False`，API 查远端树 a3027b6c/26290846 与本地逐字一致）。恢复三级链 **ls-remote → `_remote_main` API 实查（+tree 等价降级）→ 本地引用末位兜底**，补 `_slug`/`_auth_headers(repo)`（credential fill 带 cwd）。
- **A 层口径声明**：`A 本卷已入 CHANGELOG` 对辽宁早期卷（fj/az*/sz*/jxtb/phb）恒红属历史账不覆盖（结项早于本 skill 建账），不做特例豁免；按期交付卷（xj*）必须为绿。
- 验证：xj03/xj15/xj16/xj17 四卷 **12/12**；fj/az10 **11/12**（唯一红项=上述历史账，D 层全绿）。

## v1.10.1 · 2026-10-22 · 爪哥（作者）· check_backflow D 层判据升级（坑102）+ skill 仓脚本回收对齐

- **坑102（核验脚本自身硬假设）**：xj16 回流误红「book_name 全称」——线上值「新疆维吾尔自治区高海拔地区施工增加费用标准」是 DB `fee_book_meta.title` 逐字全称，但 `_bn_ok` 关键词白名单只有「计价依据/定额」；xj17 首跑 `no such table: items`（fee 九表无 items 表）致 D 层中断。判据改三层：**权威源逐字对账**（`_db_title` 取 meta `key='title'`，`_norm` 折叠空白）> 结构实测（计数源分型 `items→fee_items→quota_items`，detail 标 `src=`）> 关键词白名单（仅无 title 键的卷兜底，白名单补「费用标准」）。
- 新增断言 `D 线上 kind 与 schema 一致`：本地 schema 反推 kind（fee_items|fee_sections→fee / items|quota_items→quota / 其余→table）↔ 线上 kind，把坑100 判定前置到核验层（每卷断言数 10→12）。
- **skill 仓副本回收**：`scripts/check_backflow.py` 曾落后三项历史修复（SKILL 路径锚定用户级仓 / `_bn_ok` 卷种分流 / ls-remote rc 判定），长期只在卷目录维护——本次以卷内最新版为准回灌 skill 仓，并记入坑102 教训：单点脚本跨卷复用须定期 diff 回收。
- 验证：xj16/xj17/xj03 三 fee 卷 12/12；xj03 items 66(src=fee_items)、xj16 47、xj17 46，kind 三卷均 fee 且与 schema 实测一致。

## v1.10.0 · 2026-10-22 · 爪哥（作者）· xj16/xj17 两新卷交付 + fee 卷型根治（坑100/101）+ 站点 fee 路由补全

- **xj17 计价依据问题解释（一）～（四）合集**（fee schema 问答型）：四份官方解释纯问答部分结构化——17 节（4 章+13 节）/46 问/4 表/3 注/17 toc；解释三钢筋调整系数表+2014 版垂直运输系数表、解释四 B10-114~117 两表入 fee_tables（扩展 `item_id` 问答-表关联列）；**勘误部分整区剔除不入卷**（j3 五/六部分、j4 四/五/六部分，evidence 留痕 j3 物7/j4 物4），报告给勘误去向互见表+卷内互见注 N001；六门（含门2 `XJ15_S01` 跨卷硬编码基线：T003/T004 与 xj15 S01 逐值一致）+ smoke 10/10，两次全链字节级复现。
- **xj16 高海拔地区施工增加费用标准**（官方附件 PDF+解读 docx）：5 节/47 条目/2 表/1 注/勘误 1 条 applied；gate 6/6+smoke OK。
- **坑100（站点级总闸缺陷）**：`sync_remote.py db_profile` 二值判 kind 把 fee schema（无 items 表）误判 table → xj03 线上 /items、/chapters 恒 400、/volumes 计数 0、/search 排除、前端落入 mix 分支。根治三型判定（fee/quota/table）+ 站点 fee 路由补全（chapterRulesOf/CountOf 增 fee_notes 第三源：节注+祖先章注 parent 实测链+卷级注；fee 子目详情 chapter_code 别名+计数实算+item 关联表条件列；前端 onVol/search/render/itemDetail 全 fee 分支）+ /provinces 纳入 fee_items。本地 stub harness 28 断言；线上 xj03 items 66/chapters 17/chapter-rules 8 注全恢复。
- **坑101（问答型 fee 卷提取专项）**：span 行构建容差 3.5（上标/波浪号 y 漂移）+ 页码先行判定防「1」→「¹」；表格 span bbox 剔除防正文 scrambling（Q021 实证）；问签状态机（无答标题短行规则/节后无编号自动起问）；印页数据驱动（j1 物−1，j2-j4 物）；图片层区域渲染取证（j4 文头标题）；SQLite 页布局指纹坑（--check-only 跳重建后跑 apply 失配→全链必含 build_db）。
- **xj15 口径演变固化**：318 子目/3086 消耗量=基线 3065−勘误删除 3（B10-97~99 水行）+补充新增 4 子目/24 行（B10-114~117，即解释四两表同源）；portal/volumes.json 已刷新（旧档 314 留痕于 v1.9.9）。
- **发布链**：双仓（私有 6 db+volumes.json，公开 17 文件含 xj16/xj17 前端与报告）经 git_api_push API 通道推送（git CONNECT 502 WAF 间歇）；服务器 webhook 协同自动落盘+手动拉取站点代码+taskkill node 看门狗拉起；线上逐端点终验（volumes/search/chapters/items/详情/chapter-rules/provinces 全绿，新疆 11 卷 10617 items）。
- **REGION_EXCLUDE 纪律再实证**：xj16/xj17 须显式加入 liaoning-2024 排除集（宽 glob `quota-extract*` 劫持，坑95 同款），本次接入时同步追加。

## v1.9.9 · 2026-10-22 · 爪哥（作者）· 四卷官方勘误 overlay 接入（xj01/xj02/xj03/xj15）+ check_backflow fee 卷种分流

- **勘误接入纪律定版**（对标辽宁 apply_errata.py）：忠实层（parse JSON/md/源 PDF）只读；勘误后值入 DB 工作层；`erratas` 表 wrong_text 双值留痕按 errata_id 溯源；三态核对（A 错版一致→applied / B 已更正→不动 / C 疑点→issues 禁静默修正）+ 扩展态 A_bare（抽取值='见表' 占位符而勘误指定列级单位→落正并留 issue）。
- **四卷战果**：xj03 费用卷 3/3（T010 利润费率安装 10.5~15.9→11~16、管道场站 20~25→21~26；I046 总承包服务费首句「总承包单位依法…」→「招标人依法…」）；xj01 上册 8/8（JR-094/SM-099/SM-124 三条 desc 条文、5-36 水 2.69→0.69、10-1/10-3 名称厚度 100→180、官方补充定额附件 5 子目 B4-1~3+B10-1~2 全人材机入库）；xj02 下册 4/4（11-10 干混地面砂浆 0.2→0.51、16-174 回旋钻机/泥浆泵 0.88→0.088、JR-143 真石漆延长米→油漆面积）；xj15 安装补充 37 条=applied 10+applied_bare 1+not_in_db 26（B4-10 单位 't'→'t（平均每吨）' 为 A_bare 案例；B10-97~99 水行删除致消耗量 3065→3062；26 条附录/组织机构类无对应数据留档禁造）。
- **门控**：四卷新增门10 勘误 overlay；xj01 门3 补充子目形态断言（src_page NULL/print_page∈(1,2)/B 码连续）+ 门7 双轨（JSON==md 原文轨 + DB==JSON⊕勘误勘误轨）；xj15 门2 期望 cons=N_CONS−勘误删除数（数据驱动）；xj01 全链复跑门8 字节级一致。
- **前端**：四卷 payload.erratas + 子目级 errata_status='hit' 徽标；xj01 SUP 补充定额节点（第四/十册下「补充定额附件」，page=null）；xj15「勘误表」面板 + 头部计数。
- **smoke 勘误断言**：xj01/xj02 28→33、xj03 +3、xj15 +4（含删除行核销），四卷全绿。
- **check_backflow 修复（v1.5.3）**：D 层 items 计数查询 fee 卷种分流——xj03 fee schema 无 items 表（线上表格型路由 counts 亦无 items 口径），原 `select count(*) from items` 抛异常致整层 FAIL；改为 fee 卷置 None 跳过该判据，保留 available+book_name 全称终验（xj03 复跑 10/11→余项即本仓提交自身）。
- **xj02 CHANGELOG 补录**：xj02 此前缺条目致 A 层核销 FAIL（2026-10-22 实证），本次一并补。
- **双仓发布+回流**：私有仓 4 db + 公开仓前端/报告/portal 同步；xj01 11/11（线上 items=1760=1755+5 补充）、xj15 11/11（314）、xj02 线上 items=1296 与勘误后指纹一致、xj03 available+book_name 全称；portal 补注册 xj01/xj02（kind=docx_quota，sub=out 覆盖）。

## v1.9.8 · 2026-10-20 · 爪哥（作者）· 站点 chapter-rules 多源适配，新坑 95（xj10-15 六卷系统性缺口）

- **坑 95（站点级系统性缺口）**：站点 `routes/quota.js` 章级条文单源假设只认 `desc_rules`（OCR 卷 schema）——xj10-15 九表卷章/册说明存 `quota_explain`，`hasTable('desc_rules')` 判假短路致子目详情 `chapter_rules_count=0`、端点 400/空。**影响 6 卷，非 xj15 独有**；线上「展开本章说明」按钮恒 0 条即用户「册说明没交付」的真实来源。
- **根治**：路由多源适配（统一契约 block_type/md_kind/seq/print_page/text）——desc_rules → quota_explain 依次探测；九表卷 `chapter_code='vol-ch_no'` 拆分量查询；无 chapter 参数回全卷；no-match 回 200 空列表。前端按钮文案通用化「本章/册说明…章/册级通用」。
- **验证**：本地隔离冒烟 10/10（xj15 17/74、az09 零回归 13/71）；线上终验 xj15 B4-1 0→17、xj14 8-1-1 0→36、az09 9-1=13 不变。
- **验收纪律固化**：新卷上线必须逐端点实测（items 详情 / chapter-rules / 人材机 / toc / machines），禁只看 `volumes` 列表 available=true。

## v1.9.7 · 2026-10-20 · 爪哥（作者）· xj15 册说明交付口径纠偏，新坑 94

- **坑 94（呈现层术语分流）**：爪哥质疑「册说明没按条交付」→ 实证 DB `quota_explain` 册说明全部按条落库（74 条=说明29+规则45，七册全覆盖，粒度细于市政卷：市政卷册说明仅在 parse `volume_notes` 整段留存未落库），parse/DB/前端三处恒等。真正缺陷在前端：虚拟章树节点与「第N册 册名」行二次重复册名、主标题「第4册 · 第四册…」重复、说明区块硬编码「章说明」（本卷无章层，实为册说明，术语错误致无法对账）。根治=chLabel/showCh 主标题按「虚拟章标题==vol title」判据去重 + `explainLabel()` 按结构分流（no=0/1→册说明，章层卷→章说明）；数据层零动。
- **对账事实固化**：原书 P13 印「说明」、P14 印「工程量计算规则」→ 两桶（explain 5 + rules 12）分立是书印事实，忠实层不动，禁「修复」成合并。
- **smoke 加严**：xj15 前端断言 7→10（册说明呈现/章说明禁现/树节点册名去重/册说明全量原文在窗）；gate 9/9 复跑零回归。
- **交付报告新增「册说明交付口径对账」节**：三层形态表 + 两条书印事实 + 与市政卷粒度对照。

## v1.9.6 · 2026-10-20 · 爪哥（作者）· xj15（新疆安装工程补充消耗量定额）回流核销，新坑 88-93

- **新坑 6 条入 pitfalls**：88 twin 三层文字层混排须单层择定（SimSun，85/85 覆盖实证；不择层则标题/编码/数值翻倍 items=0——**根本坑**）；89 册→大节结构无章层（虚拟章 no=None + DB 合成 ch_no + 前端禁渲染第0章）；90 页眉奇偶双形态（偶页页码在行首，尾优先头兜底）；91 TOC 行噪声尾+标题前缀垃圾（禁 $ 锚定+起点标记切割）；92 标题变异 fuzzy 三层（多重集全同/difflib≥0.85/唯一前缀≤40，cell 扫描只 exact）；93 行内粘连三类（同行单位/续行单位/三行合一类别 KIND_CELL_RE+表头行判据加码）。
- **xj15 实测**：安装工程补充消耗量定额（独立于市政 12 册体系）100 页 = front 3 + toc 4 + divider 8 + explain 16 + quota_table 54 + empty 15；**7 册/8 虚拟章/74 节/314 子目/3065 消耗量**（编码形制 `B册号-序` B4-1…B12-x，与市政三段式不同）；TOC 恒等式 74/74；印页=物−10（门7 68/68 全票）；疑点 63 条（ocr_noise 31/unit见表 27/title_variant 3/remnant 2）；gate 9/9 + smoke 7/7。
- **迁移审计新增**：新 twin 接入先做字体分层普查（坑88）；新卷先判「册-章-节」vs「册-节」结构（坑89）；页眉页码提取必须奇偶双形态都验证（坑90）。

## v1.9.5 · 2026-10-20 · 爪哥（作者）· xj14（市政五）回流核销新坑（坑 86-87）

- **坑 78**：TOC 折行 buf 页级作用域——跨页折行标题被截成两个条目；buf 提升函数级跨页持久；
- **坑 79**：TOC 层级归属双通道——坑71 页码排序（2×2 分块恢复）与 OCR 错页码前置（9→5 致 vol/ch=None）两害相交：主通道=排序阅读序，兜底=原 parse 序前驱册/章行（仅 None 时回退，无 None 卷零回归）；
- **坑 80**：toc_match/toc_check 需标点盲比（sp 归一）——OCR 丢顿号致双向 startswith 全败；
- **坑 81**：title_truncated 补全约束 2≤长度差≤12 + 每 TOC 条目只补一次——防短节标题被跨节长标题吞并；
- **坑 82**：classify toc 判据加「点导行以页码结尾」形态约束——表格规格行「1.10×1.1⋯·」欺骗致整页表格丢失（6 子目+15 误留痕），坑57 同族；
- **坑 83**：跨卷复制残留第三类=静态字面量（book.title/册章常数/make_manifest flag 覆盖）——复制后必查字面量，禁只换标识符；
- xj12 回流核销：2 册/12 章/144 节/1683 子目/16986 消耗量，sections==TOC 144 恒等式，gate 9/9，双仓 sha256=32c06c6e796e，D 层线上 API 终验（book_name≠label、items=1683、子目 5-1-1 可读）。

## v1.9.2 · 2026-10-20 · 爪哥（作者）· xj11（市政二）回流核销新坑（坑 74-77）

- **坑 74**：parse 前置区跳过边界硬编码迁移——xj10 `pno<=23` 到 xj11 静默吞 P22/P23（第一章丢 3 节 18 子目）；根治=正文起点数据驱动（首个 HDR_CH_RE 页）+册说明按册扉页分段+公告/总说明全文内容驱动；
- **坑 75**：partial 分支 title 未按注释补全为 TOC 全标题（xj10 休眠 bug，xj11 触发）——partial 命中时 title 取 TOC 全标题；
- **坑 76**：ITEM_END_RE 的 `)` 误伤 OCR 多括号节标题——去 `)` 只留句号类；
- **坑 77**：【定额查询】OCR twin 带用户密码且站点 DRM 不一致——接入先验 needs_pass；本地 rapidocr twin 管线 + 小 VM 并行度实测（2 进程 11.3s/页最优）；
- xj11 回流核销目标 11/11（2 册/15 章/145 节/1281 子目/10632 消耗量，sections==TOC 145 恒等式，gate 9/9）。

## v1.9.1 · 2026-10-20 · 爪哥（作者）· xj10 回流核销收官新坑（坑 72-73）

- **坑 72**：双仓注册表宽 glob 吞卷——REGION_EXCLUDE 必须随新卷同步追加（xj02/03/10 路径劫持 liaoning-2024/+私有仓 xinjiang-2020 db 误删；API 通道恢复+pull --rebase 对齐判据）；
- **坑 73**：quota 卷书名键名分裂（quota_book_meta.title vs 路由 book_name）+ quota-db.js pool 进程级缓存——换 db 必重启 node，路由已三处 bm.title 兜底；
- xj10 回流核销 check_backflow 四层 11/11 PASS 定版。

## v1.9.0 · 2026-10-20 · 爪哥（作者）· xj03/xj10 新坑入库（坑 62-71）+ 经验迁移审计纪律

- **坑 62-63（xj03 补录）**：表题 lookahead 延迟归属（注续行 vs 跨页表题同形）；门 7 印页口径必须独立实测、禁 convert_meta 自证循环（xj10 复审坐实自证缺陷后双卷实证入清单）；
- **坑 64-68（xj10 补录）**：OCR 双源全网格列占位 / KIND_WORDS 竖合并单字+合排形态 / 跨页续表 dict 索引合并 / TOC 补全限同册同章 / SQLite os.remove 全新建档；
- **坑 69（流程性总坑）**：换卷必须做「经验迁移审计」——开工先读坑清单+同族 walkthrough+前卷 scripts 产出迁移审计表，禁从零重写；xj10 实证未调 skill 的代价=重踩坑51-63 同族三处 + sections 污染 775→真值 351；
- **坑 70**：竖合并 cell 残余行夹断表格（171 处 remnant，**消耗量 10317→真值 11312，995 条曾静默丢失**）+ 工作内容多行展开；确立恒等式 sections==TOC 节级集合（351==351）可作门控断言；
- **坑 71**：目录页 2×2 分块异常版式 → 按回填页码稳定排序恢复阅读序（页码非降=目录定义，对任何版式免疫）。

## v1.8.2 · 2026-10-17 · 爪哥（作者）· 悬赏自动发分加「交付记录硬门槛」

- 用户裁定：**必须有 QuotaSubmission 交付记录才自动发分**。contribution.md 第 8 条补「交付记录硬门槛」口径与五个原因码；
- 站点实现（backend/quota-volumes-sync.js）：新增 `deliveryGate(subs, claimBy)` 四判据（bountyId 归属 / account==claimBy / 非 rejected / 有实体凭据），有效者优先取「已过门」；发分三前提（认领人在场 + AUTO_SETTLE 未关 + 交付记录有效），不满足只转 `verified`，原因码进 `verifyNote` 与报告 `settleBlocked`（禁止静默吞掉）；
- 堵人工口子：`POST /api/quota-bounty/:id/settle` 同口径拦截（自动转 verified 后本可绕过），admin 例外须 `force=true` + `reason` 留痕；
- 验证：本地桩件端到端单测 31/31（判据表 8 + 匹配回归 6 + 决策表 15）→ 推送 GitHub → 服务器定向拉取（字节级 sha256 一致）→ 重启 → 线上探针：唯一在途悬赏 QB-20261017-001（claimed/0 提交）判定 `BLOCK:no-submission`。

## v1.8.1 · 2026-10-17 · 爪哥（作者）· 悬赏回流自动核销（xj01 实证）

- references/contribution.md 第 8 条口径更新：协同从「claimed/submitted→verified 待人工发分」升级为 **verified→settled 自动发分**（points.earn pool='bounty'，refId=quota-bounty:<id> 幂等，QUOTA_AUTO_SETTLE=off 留人工闸）；
- 匹配三通道根治（站点 backend/quota-volumes-sync.js）：① targetVol 精确绑卷（最高优先）② 文本双向包含/≥3 字窗口 ③ 关键词实体匹配（专业词≥1 且泛词≥1）；价格册词（价目表/单价册）与消耗量定额卷互斥——根治「建筑专业定额最新版」↔「房屋建筑与装饰消耗量定额」近义书名匹配失效（3 字窗口原口径对近义表述全失效）；
- xj01 实证：QB-20261013-001 悬赏回流后自动 settled，bounty 池 +2000（ledger refId=quota-bounty:6ace355b…，幂等）；QB-20261017-001（价目表）正确未命中。

## v1.8.0 · 2026-10-17 · 爪哥（作者）· sz08 缺陷修复回流 + yl01 园林绿化卷实战回写

- **坑 58/59（sz08 修复，yl01 门 6/门 7 双覆盖验证）**：parse_desc print_page 内联硬编码偏移与 OFFSET 脱钩（整体偏 2 页静默上线）→ 根治为 zone 函数 `print_page_of(page)` 收口 + 门 7 印刷页页脚实测双条件；页脚多位数 E-BZ span 序混乱（"172"读成"2 7 1"）→ 按 span x 坐标排序拼接 + 版面过滤；cost_check 只读化（坑 50 延伸）随卷生效；
- **坑 60/61（yl01 园林绿化卷新增）**：书印 TOC 节行页码整体偏差（ch3/ch4 +2）→ 前端节点树首节下界改章正文起始页（冒烟 12 孤儿实证根治）；门 6b 页脚实测无页码页口径三分（footer=None skip 留痕 / ≠print 真失配 / ⊆ no_page_print 交叉互证，4 条 skip 零泄漏实证）；
- **scripts/ 基准升级 az09→yl01**：gate.py（页脚实测+门 6b 三分口径）、parse_desc.py（zone 函数）、cost_check.py（纯只读+园林单位集）；
- **yl01 收官数字**：四章 0501-0504，889 子目逐章连续（407/136/298/48），toc 160，desc_rules 41，冒烟 27/27，九门全绿+端到端二跑门 8 一致，P1 官方取证 889/889（wm 7071387e8709 / nowm 77350d6d3a2d）；第 15 卷。

## v1.7.2 · 2026-10-17 · 爪哥（作者）· xj01 回流核销二轮：API 双轨判定根治

- check_backflow.py v1.5.3：git_state 回退路径根治——ls-remote 502 时不再拿本地 origin/main 陈旧引用比（API 通道推送后本地无该 commit 对象，update-ref 必失败、引用永停推送前 sha，xj01 实证三仓全误报未同步），改经 GitHub API 直查远端真实 refs/heads/main 再走 tree 等价判定；_slug/_auth_headers 重构去重复 token 逻辑（原 _remote_tree 内联 credential fill×3）；
- xj01 核销实证：7/9 PASS（B/C/A-tag/A-changelog + 双仓 tree 等价全过），残留 2 缺口=D 层线上 kill node（用户侧服务器动作）；
- 连带的 sp/git_api_push.py 根治（同轮）：blob 上传改 `git cat-file blob` git 归一化内容（Windows autocrlf 下工作区 CRLF≠仓库 LF blob，直接读工作区上传导致远端 tree 与本地链分叉——skill 仓 81 行全 CRLF 实证），上传后断言 bsha==oid 否则熔断；commit 带本地 author/committer/date（ISO 原样）消息 %B；新增 --force 重设远端链到本地权威。

## v1.7.1 · 2026-10-16 · 爪哥（作者）· xj01 回流核销暴露守卫缺陷根治

- check_backflow.py v1.5.2：D 层 book_name 检查不再硬编码辽宁特有词「计价依据」（xj01 书名无此词→假 fail），改通用判据 `("定额" in bn or "计价依据" in bn) and len(bn)>10 and bn!=label`（正则表达式含全称特征 + 与 label 区分，防把短 label 当全称）；
- xj01 核销实证：传参口径=卷 key（`xj01`）非全目录名；A 层 CHANGELOG 条目匹配 `^## .*{key}` 同步口径；
- 连带根因：xj01 finalize 补 book_name 纯文本 insert（坑 46 同款缺口复发——新卷 finalize 必须显式插 book_name，不能只依赖 md 元数据透传）。

## v1.7.0 · 2026-10-16 · 爪哥（作者）· xj01 OCR 双源形态卷实战回写

- **新坑 7 条入 pitfalls（坑 51-57）**：51 OCR 双源架构定版（OCR 版=文本源/矢量原版=网格几何源+P1 双源取证口径，官方层仅子目本页有文本时查 code）；52 OCR 伪影四连（竖线剥离/END_UT 粘连双正则/BARE_UT 裸令牌/守卫防误杀真单位）；53 链漏跑事故（忠实层两出口，convert 改后断点续跑必须从 extract_md 起）；54 纯消耗量口径（H1/H2 全 skip+门2 分章编码连续+list_code 空书印事实）；55 中文章码前端契约（itemPrefix 查 meta.code_prefix 表/AMP_SEC 恒等/冒烟路由换码）；56 门7 带表规则拍平重建公式（`；`/`｜` 拍平 vs src_join==text 假 fail）；57 目录 2 字「附录」豁免+编号点保号（clean_leaders ≥2）；
- **新增 references/walkthrough-xj01.md**：OCR 双源形态端到端实录（选型判据表+M0-M8 九里程碑+验收数字），参考实现 sp/quota-extract-xj01/scripts/；
- SKILL.md 版本号修正 1.4.0→1.7.0（v1.5.x/v1.6.x 前几轮漏升 frontmatter）；
- xj01 实测：1755 子目（1-1~10-351 十章连续）/11073 消耗行/目录 483/条文 190，九门全绿+冒烟 27/27+全链二跑字节级复现。

## v1.6.0 · 2026-10-16 · 爪哥（作者）· sz08 市政第八册路灯工程实战回写

- **新坑 2 条入 pitfalls（坑 49/50）**：49 表头规格档位续行吸收 + 复合单位内嵌空格归一（归一优于白名单硬塞）；50 读库 rwc connect 触碰 SQLite header counter → 门 8 字节漂移（根治=全链只读 URI，Windows 路径转正斜杠）；
- sz08 实测：516 子目 8-1~516 连续、九门全绿、P1 516/516、冒烟 23/23、全链二跑字节级复现；
- 复制源升级为 **sz02 基准版**（坑 42-45 修复随卷携带生效：nowm /ID 钉死一次到位、11.8pt H2 带、目录点线 {1,}、计量单位粘连段）；
- 分卷冒烟硬编码残留 3 处（章数/item 码/层路由短码）——坑 19 分卷冒烟铁律再次实证，换卷 smoke_front.mjs 必查三个硬编码点。

## v1.5.2 · 2026-10-16 · 爪哥（作者）· 坑 48 机械化根治（check_backflow.py 守卫）

- **新增 scripts/check_backflow.py**：回流两连核销守卫——四层 11 项逐项核销（skill 仓/VOLUME_META 注册/双仓 sha256 门禁/线上终验），任一缺口给出修复动作，退出码 1=禁止宣称收官；
- **坑 48 入 pitfalls**：收官回写 ≠ 回流到位，"忘了跑"型缺口文档防不了，只能守卫脚本防（sz02 四层静默缺口实证）；
- **iteration-protocol.md 升级**：强制回写清单 +第 7 项（每卷收官必跑守卫）+ 第六节（核销规程）；
- **坑 47 ③ 落地**：sync_remote.py site_db() 加 0 字节空壳守卫（此前"留待下卷"，按根治不拖延原则立即实施）。

## v1.5.1 · 2026-10-16 · 爪哥（作者）· 回流核实补漏（用户质询驱动）

- **坑 46 入 pitfalls**：book_meta.book_name 必须纯文本（md 管线 json.dumps 带引号+缺键 → 线上 5 卷书名降级 label）；五卷 finalize 显式 insert 根治，线上 13/13 全称。
- **坑 47 入 pitfalls**：诊断 sqlite3.connect() 默认创建 0 字节空 db → 污染 site_db() out/ 优先链 → 私有仓垃圾条目；诊断必须 ro URI，site_db 0 字节守卫留待下卷。
- **回流核实结论**：skill 仓 v1.4.0/v1.5.0 此前未 commit/push（本次补 commit a591695+tag）；sz02 未注册 VOLUME_META/双仓未同步（本次补齐全链：双仓推送+服务器协同+kill node，线上 13 卷 650 子目）。
- 教训：收官回写 ≠ 回流到位；「回流两连」（skill 仓 commit/tag/push + 成果双仓同步+服务器协同+线上终验）必须逐项核销。

## v1.5.0 · 2026-10-16 · 爪哥（作者）· sz02 市政第二册道路工程实战回写

- **新坑 4 条入 pitfalls（坑 42-45）**：42 mupdf save 随机写 trailer /ID → nowm.pdf 字节漂移（首次实证"全链二跑门8 失配但文本零差异"，根治=/ID 第二段钉死为第一段复制）；43 H2 字号带下界 12.0 漏 11.8pt 节标题（换卷必做字体直方图）；44 目录点线单「…」字符页码正则漏命中（{2,}→{1,}，其他行必须清零）；45 工作内容+计量单位粘连段（坑 38 对偶形态，趟2 先查内嵌计量单位）；
- **本卷形态新增**：页码字符逆序存储（按 x 序重排取真值）；章扉页 19.7pt 三行合并 H1；正文无「第X章」行仅扉页承载章结构；H2 兼容 13.7/11.8 双字号；
- sz02 实测：650 子目 1-650 连续、九门全绿、P1 650/650、冒烟 23/23、全链二跑字节级复现；
- 复制源仍以 sz11 版为基准（坑 42-45 修复位于卷级 remove_watermark/convert/parse_items/parse_desc，未上提 skill scripts，待下卷复制时随卷携带）。

格式：`- 版本 | 日期 | 来源 | 变更摘要`；来源=贡献者标识/卷名；合并须经作者过审（iteration-protocol.md 第四节）。

## v1.4.0 · 2026-10-15 · 爪哥（作者）· az09 第三卷实战回写（通用安装·消防工程）

- **新坑 6 条入 pitfalls（坑 36-41）**：36 窄表编码在 r[1]（措施项目类子目整表漏抓）；37 视觉行左右分块 y 差 ~1.1pt 致纯 y 排序颠倒（work 截断+单位丢失，convert 聚簇根治）；38 计量单位挂续行尾部（包含即取）；39 目录缺章标题行（书印疵）→ 合成章行+按印刷页区间重归属；40 附录标记误触（目录页「附 录」条目无 # 前缀）→ # 前缀+末章扉页后双条件；41 章无「一、」式节行 → build_front 回退其他行构造节节点+门6 参照集扩展；
- **流程纪律 2 条**：双源 sha12 锚定先实测后写死（az09 换参 MAP 凭记忆填错污染 6 处锚点；official_wm 应与原始下载件字节级闭合）；换参后全链 grep 卷名/前缀/短码三类残留（token 回填只覆盖数字，路由/标题/断言类残留需单独扫）；
- **scripts/ 参考实现升级为 az09 版**（结构沿革 lvse→sz11→az09）：convert（视觉行聚簇）/ parse_items（窄表回退+单位包含即取+CJK 空格剔除）/ parse_desc（缺章行合成+附表按节分组挂末章+附录双条件）/ build_front（节节点回退）/ gate（门6 参照集）/ smoke_front / cost_check；卷名与路径保留 az09 基准值，换参见 volume_params.md；
- **基准数字**：az09 = 286 子目（9-1~9-286 连续）/ 目录 101 行（含 1 合成章行）/ 条文 71 条（总说明10+册说明5+章说明19+计算规则33+附表4）/ 冒烟 24/24 / 九门全绿+字节级复现 / P1 官方原版取证 281/281（skip 5=系数计取项书印无费用行）。

## v1.1.0 · 2026-10-15 · 爪哥（作者）· 补成果回流与 metal 悬赏协同协议（用户质询补缺）

- **缺口**：v1.0.0 只设计了 skill 自身迭代回流，未覆盖「提取成果回流全国库 → metal 站悬赏自动核销」的接单者闭环；
- **新增 `references/contribution.md`**：悬赏接单者 8 步闭环（领悬赏→官方源→提取→自验→fork→PR→审核→自动核销）；PR 内容纪律（db 不入公开仓 PR、官方源永不回流）；维护者侧双仓入库操作（私有仓先推保 webhook 时序、quota-db.js 随进程重启生效、API 应急通道）；
- **悬赏自动核销口径**（metal 站 quota-bounty.js 已实证）：open→closed（按地区+卷 key 匹配）/ claimed|submitted→verified 待管理员发分；
- SKILL.md 增「成果回流与悬赏协同」节引用。

## v1.0.0 · 2026-10-15 · 爪哥（作者）· 初始版本（lvse 基准卷全链验证）

- **来源**：从 docx-quota-extract v1.4.0 的 md_source 变体独立成 skill（用户裁定：把「PDF→Markdown→结构化定额库」链路提炼为独立可分发 skill，覆盖只有官方 PDF、无 Word 源的定额/规范类文档）；
- **基准卷**：辽宁2024《绿色建筑工程定额》（269 页官方 PDF）——487 子目（20-1~20-487 连续零缺失）/ 目录 77 行（双栏重组）/ 条文 53 条 / 九门全绿 + 端到端重跑字节级复现 + P1 官方带水印原版取证 487/487 + 渲染级冒烟 22/22；
- **初始管线**：SKILL.md（11 阶段总纲 + 双源架构）+ references/（pipeline 11 阶段详解 / pitfalls 坑 1-11 / volume_params 61 处替换点地图 / iteration-protocol 迭代协议）+ scripts/（9 脚本参考实现：convert_pdf_to_md → extract_md → parse_items → parse_desc → finalize → cost_check → build_front → smoke_front → gate，保留 lvse 基准值）+ check_volume_params.py（六类混用守卫）；
- **双源架构**：提取用 nowm 干净源、P1 校验用官方 wm 原版，manifest 同锚两者 sha12 + convert 脚本 sha12；
- **姊妹关系**：有 Word 源优先 `docx-quota-extract`（token 更低、无转换层误差）；本 skill 用于「只有 PDF」场景。

## v1.3.0 · 2026-10-15 · 爪哥（作者）· sz11 第二卷实战回写（用户积分复盘驱动）

- **新坑 6 条入 pitfalls（坑 12-17）**：12 水印 Form XObject 指令删除（零误伤根治）；13 章码≠章序+重复+目录/正文不一致（节行按目录章序归章）；14 书印无工作内容行→门3 断言语义（**含误诊澄清**：SEC_RE 截断为假因，抽查字段名混淆乌龙）；15 换参三类系统性漏网（反斜杠/路径/短码假绿——积分消耗大头）；16 页码带与单位白名单先实测再定参；17 finalize 嵌核验数字→顺序依赖；
- **新增 `scripts/preflight_check.py`**：开工自检（路径存在+他卷残留/正则试命中/短码核对/断言占位四类）——把 sz11 实证的 10+ 轮调试往返压到 1 轮；双测验证：skill 原版检出 8 处他卷残留，sz11 全过，**且当场抓到 smoke 一处真残留（layer:041101:js）**；
- volume_params 补换参高危表+参考实现两代说明（sz11 版为最新结构改进复制源）；pipeline 补 M0 预检清单六项；
- 动机：用户复盘「本次提取消耗积分太多」——三类换参漏网+两轮页码试参+三轮白名单补齐+乌龙排查均可在 preflight/预检清单一轮内消除。

## v1.2.0 · 2026-10-15 · 爪哥（作者）· 基准卷全过程实录（用户裁定：按 lvse 全过程提炼）

- **新增 `references/walkthrough-lvse.md`**：绿色建筑卷 12 里程碑端到端实录（M0 双源定版→M1 转换层三坑→M2 保真层→M3 子目层行判别→M4 目录双栏重组→M5 落库→M6 核验 H1/P1 坑→**M7 前端假死事故（九门全绿但页面「加载中」，两级根因：契约错配+冒烟只验文件）**→M8 契约映射重写→M9 渲染级冒烟→M10 门控闭环→M11 收官分发），每步带实测验收数字；
- SKILL.md 增「能加载成功的首页」完成态四条定义（缺一不可；只过门控不冒烟=可复现的坏文件）+ 实战范本入口；
- 动机：用户指令「按照绿色建筑定额库的结构化全过程到生成结构化定额库提取首页（能加载成功的文件）的全过程去提炼总结」——把真实迭代时序（含事故）作为 skill 主线教学，而非理想化十阶段。
