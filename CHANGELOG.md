# CHANGELOG — md-quota-extract

格式：`- 版本 | 日期 | 来源 | 变更摘要`；来源=贡献者标识/卷名；合并须经作者过审（iteration-protocol.md 第四节）。

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
