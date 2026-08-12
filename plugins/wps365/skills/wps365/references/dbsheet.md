# 多维表工作流

1. 先执行 `python -m wps365 base +schema <file_id>`，找到正确的 `sheet_id`、字段名/字段 ID 和视图。
2. 读取记录：`base +list <file_id> <sheet_id>`；读取单条：`base +get <file_id> <sheet_id> <record_id>`。
3. 创建或更新使用 `--json` 传记录数组。创建数组元素可以是字段对象；更新元素必须含记录 `id` 和字段内容。
4. 一次写入前先确认用户给出的字段名与 schema 一致。不要猜测列名、sheet ID 或记录 ID。
5. 删除记录是高风险写入；先 dry-run 展示文件、sheet 和全部记录 ID，再获得明确确认。
