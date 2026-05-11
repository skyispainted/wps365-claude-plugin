# WPS 365 Claude Code Plugin

WPS 365 V7 API 插件，为 Claude Code 提供企业协作能力：通讯录、日历、会议、云文档、多维表、IM。

## 安装

```bash
# 方法一：通过 marketplace 安装（推荐）
claude plugin marketplace add https://github.com/wps365/wps365-claude-plugin
claude plugin install wps365

# 方法二：一键脚本安装
curl -fsSL https://raw.githubusercontent.com/wps365/wps365-claude-plugin/main/install.sh | bash
```

## 首次使用

```bash
python -m wps_credential_manager login
```

浏览器完成登录后即可使用所有功能。

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

## 凭证自动刷新

`wps_sid` 过期后会自动无感刷新，用户无需手动操作。仅需首次登录验证一次。
