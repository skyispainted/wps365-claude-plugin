# WPS 365 Claude Code Plugin

WPS 365 V7 API 插件，为 Claude Code 提供企业协作能力：通讯录、日历、会议、云文档、多维表、IM。

## 安装

**最佳实践：把仓库地址发给 AI，让它帮你安装。**

在 Claude Code 中发送：

> 帮我安装这个 Claude 插件：https://github.com/skyispainted/wps365-claude-plugin

AI 会自动执行 marketplace 安装、环境初始化和凭证认证全流程。

### 手动安装

如果命令行安装，可通过 Claude Code 插件系统：

```bash
claude plugin marketplace add https://github.com/skyispainted/wps365-claude-plugin
claude plugin install wps365
```

或通过一键脚本：

```bash
curl -fsSL https://raw.githubusercontent.com/skyispainted/wps365-claude-plugin/main/install.sh | bash
```

## 首次使用

首次使用时 AI 会引导你完成认证：提供数字员工 app_id → 打开浏览器登录 WPS → 完成。
`wps_sid` 会自动存储并在过期时无感刷新。

## 功能

| 模块 | 功能 |
|------|------|
| `wpsv7client.users` | 查询当前用户 |
| `wpsv7client.contacts` | 通讯录搜索 |
| `wpsv7client.calendar` | 日历日程管理 |
| `wpsv7client.meeting` | 会议管理 |
| `wpsv7client.drive` | 云文档操作 |
| `wpsv7client.dbsheet` | 多维表操作 |
| `wpsv7client.im` | 即时消息 |
