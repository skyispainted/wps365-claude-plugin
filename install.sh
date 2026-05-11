#!/usr/bin/env bash
# WPS 365 Claude Code Plugin — 一键安装脚本
# Usage: curl -fsSL https://raw.githubusercontent.com/wps365/wps365-claude-plugin/main/install.sh | bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CC_PLUGINS_DIR="${HOME}/.claude/plugins"
CC_SETTINGS="${HOME}/.claude/settings.json"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[wps365]${NC} $*"; }
warn()  { echo -e "${YELLOW}[wps365]${NC} $*"; }
error() { echo -e "${RED}[wps365]${NC} $*" >&2; }

info "WPS 365 Claude Code 插件安装"
echo ""

# Check Python
command -v python3 &>/dev/null || { error "未找到 python3"; exit 1; }
info "Python $(python3 --version) ✓"

# Install cryptography if needed
python3 -c "from cryptography.hazmat.primitives.ciphers.aead import AESGCM" 2>/dev/null || {
    info "正在安装 cryptography ..."
    pip3 install cryptography 2>/dev/null || pip install cryptography 2>/dev/null || python3 -m pip install cryptography
    info "cryptography 安装完成 ✓"
}

# Copy plugin
info "正在安装插件 ..."
mkdir -p "$CC_PLUGINS_DIR/wps365"

# If running from local repo, copy from source
if [ -d "$SCRIPT_DIR/plugins/wps365" ]; then
    rm -rf "$CC_PLUGINS_DIR/wps365"
    cp -a "$SCRIPT_DIR/plugins/wps365" "$CC_PLUGINS_DIR/wps365"
fi

info "插件已安装到 $CC_PLUGINS_DIR/wps365 ✓"

# Configure PYTHONPATH
scripts_dir="${HOME}/.claude/plugins/wps365/skills/wps365/scripts"

python3 -c "
import json, sys
p='${CC_SETTINGS}'
try:
    with open(p) as f: cfg=json.load(f)
except FileNotFoundError:
    cfg={'env':{}}
env=cfg.setdefault('env',{})
pp=env.get('PYTHONPATH','')
if '${scripts_dir}' not in pp.split(':'):
    env['PYTHONPATH']='${scripts_dir}' if not pp else pp+':${scripts_dir}'
    with open(p,'w') as f: json.dump(cfg,f,ensure_ascii=False,indent=2)
    print('PYTHONPATH_CONFIGURED')
else:
    print('PYTHONPATH_EXISTS')
"

info "PYTHONPATH 已配置 ✓"

# Verify
info "验证安装 ..."
export PYTHONPATH="$scripts_dir"
python3 -c "from wpsv7client import get_current_user" 2>/dev/null && info "wpsv7client 可用 ✓" || { error "wpsv7client 导入失败"; exit 1; }
python3 -m wps_credential_manager status &>/dev/null && info "凭证管理器可用 ✓" || warn "凭证管理器需首次认证"
[ -f "${HOME}/.claude/plugins/wps365/skills/wps365/SKILL.md" ] && info "SKILL.md 已注册 ✓" || error "SKILL.md 缺失"

echo ""
info "安装完成！重启 Claude Code 后 wps365 技能将自动加载。"
echo ""
info "首次认证: python -m wps_credential_manager login"
echo ""
