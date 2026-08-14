# 云文档工作流

- 所有 `wps365` 调用均指主 Skill 定义的插件内置启动器；不要直接依赖可能过期的 `python -m wps365`。
- 用户提供明确的 `link_id` 或 WPS 分享链接时，直接执行 `wps365 drive +get/+read --link-id <link_id>`；`--link-id` 是必须携带值的 Flag，不能单独作为开关使用。
- 用户提供明确且已验证的自有文件 ID 时，直接执行 `wps365 drive +get/+read <file_id>`。
- 用户只提供名称时，先 `wps365 drive +search <keyword>`。每个可读候选会返回 `read_args`；选定单一候选后原样透传：`wps365 drive +read <read_args...>`。当前任务链已有选定候选时复用其 `read_args`，不要再次搜索。
- 没有 `read_args` 的兼容处理：`file_src.type == "link"` 且有 `link_id` 时使用 `--link-id <link_id>`；否则仅对可验证的自有文件使用 `id`。不要将共享结果的 `id` 一律当成可读文件 ID。
- 多个候选时仅展示名称、来源和更新时间，请用户消歧；不要取第一个结果，也不要切换到其他候选读取、修改、移动或分享。
- 用文件 ID 读取失败且同一搜索结果含 `link_id` 时，只对该候选重试一次 `drive +read --link-id <link_id>`；不要先运行 `schema`、重新认证或改用另一候选的 ID。
- `drive +read` 支持 `--format plain|markdown|html|kdc`，默认 Markdown。
- `drive +write` 当前直接写入智能文档（`.otl`）。其它文件格式使用 `drive +overwrite --source <local_file>` 或 `drive +convert-overwrite --source|--content ...`；两者都是高风险写入，必须先 dry-run 后取得明确确认。
- `+share` / `+unshare` 是高风险操作；必须 dry-run 后取得明确确认。
