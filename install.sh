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

# Copy plugin to Claude Code plugin dir
info "正在安装插件 ..."
mkdir -p "$CC_PLUGINS_DIR/wps365"
if [ -d "$SCRIPT_DIR/plugins/wps365" ]; then
    rm -rf "$CC_PLUGINS_DIR/wps365"
    cp -a "$SCRIPT_DIR/plugins/wps365" "$CC_PLUGINS_DIR/wps365"
fi
info "插件已安装到 $CC_PLUGINS_DIR/wps365 ✓"

# Copy Python packages to user site-packages (so they work globally without PYTHONPATH)
info "正在安装 Python 包 ..."
USER_SITE=$(python -c "import site; print(site.getusersitepackages())")
mkdir -p "$USER_SITE"
cp -a "$CC_PLUGINS_DIR/wps365/skills/wps365/scripts/wpsv7client" "$USER_SITE/"
cp -a "$CC_PLUGINS_DIR/wps365/skills/wps365/scripts/wps_credential_manager" "$USER_SITE/"
info "Python 包已安装到 $USER_SITE ✓"

# Verify
info "验证安装 ..."
python -c "from wpsv7client import get_current_user; print('wps365 ready')" && info "wpsv7client 可用 ✓" || { error "wpsv7client 导入失败"; exit 1; }
python -m wps_credential_manager status &>/dev/null && info "凭证管理器可用 ✓" || warn "凭证管理器需首次认证"
[ -f "${HOME}/.claude/plugins/wps365/skills/wps365/SKILL.md" ] && info "SKILL.md 已注册 ✓" || error "SKILL.md 缺失"

echo ""
info "安装完成！重启 Claude Code 后 wps365 技能将自动加载。"
echo ""
info "首次认证: python -m wps_credential_manager login"
echo ""
