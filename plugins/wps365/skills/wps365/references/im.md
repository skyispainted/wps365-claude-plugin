# 即时消息工作流

- 已知精确 `chat_id` 时直接执行 `im +send <chat_id> <text>`；不要为已知目标运行认证检查、`schema` 或会话搜索。
- 按联系人姓名发送纯文本时：先 `contact +search <name>` 确认唯一活跃联系人，再 `im +search <name>` 查找会话，最后发送 `im +send <chat_id> <text>`。
- 只能选择 `type: "p2p"` 且 `p2p_ext_attrs.peer.id` 与所选联系人 ID 相同的会话；不要仅按名称匹配，也不要猜测或发送到同名群聊。
- 多个同名联系人、多个匹配私聊或没有匹配私聊时，展示最小必要候选信息并请求用户消歧；在此之前不得发送。
- 查看上下文使用 `im +history <chat_id>`；不要为了确认收件人盲发测试消息。
- 用户明确给出收件人和消息内容即构成普通发送授权；撤回 `im +recall <chat_id> <message_id>` 是高风险写入，先 dry-run 后取得具体确认。
- 只在快捷命令未知、CLI 返回“未知快捷命令”或参数契约不明确时使用 `schema im` 或 `schema im <+shortcut>`。
- 消息发送报权限或参数错误时，不要重新登录；转述统一错误并检查会话、消息类型或资源权限。
