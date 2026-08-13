# 即时消息工作流

- 用户只给联系人或群名称时，先 `contact +search` 或 `im +search`，确认唯一用户/会话 ID 后再发送。
- 查看上下文使用 `im +history <chat_id>`；不要为了确认收件人盲发测试消息。
- 发送：`im +send <chat_id> <text>`。用户明确给出收件人和消息内容即构成写入授权。
- 撤回：`im +recall <chat_id> <message_id>` 是高风险写入，先 dry-run 后取得具体确认。
- 消息发送报权限或参数错误时，不要重新登录；转述统一错误并检查会话、消息类型或资源权限。
