# CHANGELOG — md-quota-extract

格式：`- 版本 | 日期 | 来源 | 变更摘要`；来源=贡献者标识/卷名；合并须经作者过审（iteration-protocol.md 第四节）。

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
