#!/usr/bin/env bash
# WPS 365 Claude Code Plugin — 一键安装脚本
# Usage: curl -fsSL https://raw.githubusercontent.com/skyispainted/wps365-claude-plugin/main/install.sh | bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CC_PLUGINS_DIR="${HOME}/.claude/plugins"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[wps365]${NC} $*"; }
warn()  { echo -e "${YELLOW}[wps365]${NC} $*"; }
error() { echo -e "${RED}[wps365]${NC} $*" >&2; }

info "WPS 365 Claude Code 插件安装"
echo ""

# Check Python
command -v python &>/dev/null || { error "未找到 python"; exit 1; }
info "Python $(python --version) ✓"

# Install cryptography
python -c "from cryptography.hazmat.primitives.ciphers.aead import AESGCM" 2>/dev/null || {
    info "正在安装 cryptography ..."
    pip install cryptography 2>/dev/null || pip install cryptography 2>/dev/null || python -m pip install cryptography || { error "安装 cryptography 失败"; exit 1; }
    info "cryptography 安装完成 ✓"
}

# Copy a local checkout when available. Curl-based installation uses the managed plugin cache below.
LOCAL_PLUGIN_DIR="$SCRIPT_DIR/plugins/wps365"
if [ -d "$LOCAL_PLUGIN_DIR" ]; then
    mkdir -p "$CC_PLUGINS_DIR/wps365"
    rm -rf "$CC_PLUGINS_DIR/wps365"
    cp -a "$LOCAL_PLUGIN_DIR" "$CC_PLUGINS_DIR/wps365"
    info "插件已安装到 $CC_PLUGINS_DIR/wps365 ✓"
else
    warn "未检测到本地插件目录，将使用 Claude Code 受管插件缓存"
fi

# Register and enable the managed Claude Code plugin so its commands load in new sessions.
command -v claude &>/dev/null || { error "未找到 Claude Code CLI，无法注册插件"; exit 1; }
MARKETPLACE="skyispainted-wps365"
MARKETPLACE_SOURCE="${WPS365_MARKETPLACE_SOURCE:-skyispainted/wps365-claude-plugin}"
PLUGIN="wps365@$MARKETPLACE"
if ! claude plugin marketplace list | grep -Fq "$MARKETPLACE"; then
    claude plugin marketplace add "$MARKETPLACE_SOURCE" --scope user || { error "注册 Claude Code Marketplace 失败"; exit 1; }
else
    claude plugin marketplace update "$MARKETPLACE" || { error "更新 Claude Code Marketplace 失败"; exit 1; }
fi
if ! claude plugin list | grep -Fq "$PLUGIN"; then
    claude plugin install "$PLUGIN" --scope user || { error "安装 Claude Code 插件失败"; exit 1; }
else
    claude plugin update "$PLUGIN" --scope user || { error "更新 Claude Code 插件失败"; exit 1; }
fi
claude plugin enable "$PLUGIN" --scope user >/dev/null 2>&1 || true
claude plugin list | grep -Fq "$PLUGIN" || { error "Claude Code 插件未成功注册"; exit 1; }
info "Claude Code 插件已注册并启用 ✓"

PLUGIN_SOURCE_DIR="$LOCAL_PLUGIN_DIR"
if [ ! -d "$PLUGIN_SOURCE_DIR" ]; then
    PLUGIN_SOURCE_DIR=$(python -c 'import json, pathlib; data=json.loads((pathlib.Path.home()/".claude/plugins/installed_plugins.json").read_text(encoding="utf-8")); entries=data["plugins"]["wps365@skyispainted-wps365"]; print(next(item["installPath"] for item in entries if item.get("scope") == "user"))')
fi
[ -d "$PLUGIN_SOURCE_DIR" ] || { error "未找到已安装的插件目录"; exit 1; }

# Copy Python packages to user site-packages (so they work globally without PYTHONPATH)
info "正在安装 Python 包 ..."
USER_SITE=$(python -c "import site; print(site.getusersitepackages())")
mkdir -p "$USER_SITE"
rm -rf "$USER_SITE/wpsv7client" "$USER_SITE/wps_credential_manager" "$USER_SITE/wps365"
cp -a "$PLUGIN_SOURCE_DIR/skills/wps365/scripts/wpsv7client" "$USER_SITE/"
cp -a "$PLUGIN_SOURCE_DIR/skills/wps365/scripts/wps_credential_manager" "$USER_SITE/"
cp -a "$PLUGIN_SOURCE_DIR/skills/wps365/scripts/wps365" "$USER_SITE/"
info "Python 包已安装到 $USER_SITE ✓"

# Verify
info "验证安装 ..."
python -c "from wpsv7client import get_current_user; print('wps365 ready')" && info "wpsv7client 可用 ✓" || { error "wpsv7client 导入失败"; exit 1; }
python -m wps365 schema &>/dev/null && info "统一 wps365 CLI 可用 ✓" || { error "统一 wps365 CLI 导入失败"; exit 1; }
python -m wps365 schema im recent list &>/dev/null && info "IM 命令路由可用 ✓" || { error "已安装 CLI 缺少 IM 命令路由"; exit 1; }
python -m wps_credential_manager status &>/dev/null && info "凭证管理器可用 ✓" || warn "凭证管理器需首次认证"
[ -f "$PLUGIN_SOURCE_DIR/skills/wps365/SKILL.md" ] && info "SKILL.md 已注册 ✓" || { error "SKILL.md 缺失"; exit 1; }

echo ""
info "安装完成！重启 Claude Code 后 wps365 技能将自动加载。"
echo ""
info "首次认证: python -m wps365 auth login --flow local --app-id <你的_WPS_365_App_ID>"
info "认证诊断: python -m wps365 config doctor"
echo ""
