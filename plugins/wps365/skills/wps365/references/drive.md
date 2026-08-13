# 云文档工作流

- 普通文件 ID 直接执行 `python -m wps365 drive +get <file_id>` 或 `+read <file_id>`；这只发起必要的云盘请求。
- 用户提供的是 WPS 分享链接 ID 时，使用 `--link-id <link_id>`；CLI 会解析一次得到文件和云盘 ID。
- 搜索结果不唯一时列出标题、ID 和链接信息让用户选择。不要取第一个结果直接修改、移动或分享。
- `drive +read` 支持 `--format plain|markdown|html|kdc`，默认 Markdown。
- `drive +write` 当前直接写入智能文档（`.otl`）。其它文件格式使用明确的 `wps365 legacy drive write`，并在执行前确认目标格式和覆盖语义。
- `+share` / `+unshare` 是高风险操作；必须 dry-run 后取得明确确认。
