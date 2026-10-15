# CHANGELOG — md-quota-extract

格式：`- 版本 | 日期 | 来源 | 变更摘要`；来源=贡献者标识/卷名；合并须经作者过审（iteration-protocol.md 第四节）。

## v1.0.0 · 2026-10-15 · 爪哥（作者）· 初始版本（lvse 基准卷全链验证）

- **来源**：从 docx-quota-extract v1.4.0 的 md_source 变体独立成 skill（用户裁定：把「PDF→Markdown→结构化定额库」链路提炼为独立可分发 skill，覆盖只有官方 PDF、无 Word 源的定额/规范类文档）；
- **基准卷**：辽宁2024《绿色建筑工程定额》（269 页官方 PDF）——487 子目（20-1~20-487 连续零缺失）/ 目录 77 行（双栏重组）/ 条文 53 条 / 九门全绿 + 端到端重跑字节级复现 + P1 官方带水印原版取证 487/487 + 渲染级冒烟 22/22；
- **初始管线**：SKILL.md（11 阶段总纲 + 双源架构）+ references/（pipeline 11 阶段详解 / pitfalls 坑 1-11 / volume_params 61 处替换点地图 / iteration-protocol 迭代协议）+ scripts/（9 脚本参考实现：convert_pdf_to_md → extract_md → parse_items → parse_desc → finalize → cost_check → build_front → smoke_front → gate，保留 lvse 基准值）+ check_volume_params.py（六类混用守卫）；
- **双源架构**：提取用 nowm 干净源、P1 校验用官方 wm 原版，manifest 同锚两者 sha12 + convert 脚本 sha12；
- **姊妹关系**：有 Word 源优先 `docx-quota-extract`（token 更低、无转换层误差）；本 skill 用于「只有 PDF」场景。
