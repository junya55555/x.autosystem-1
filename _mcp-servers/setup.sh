#!/bin/bash
# MCP Setup Script - 新Codespaceでgrok-consultant / x-search MCPを自動構築
#
# 使い方:
#   1. GitHubのCodespace User Secretsに以下を設定:
#      - XAI_API_KEY
#      - X_BEARER_TOKEN
#   2. 新Codespaceでこのスクリプトを実行:
#      bash _mcp-servers/setup.sh
#   3. Claude Code を再起動（VS Code: Cmd+Shift+P → "Reload Window"）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MCP Setup for Claude Code"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ===== 環境変数チェック =====
if [ -z "$XAI_API_KEY" ]; then
    echo ""
    echo "❌ XAI_API_KEY が設定されていません"
    echo ""
    echo "設定方法:"
    echo "  1. https://github.com/settings/codespaces にアクセス"
    echo "  2. Codespaces secrets → New secret"
    echo "  3. Name: XAI_API_KEY / Value: あなたのキー"
    echo "  4. Repository access で対象リポを選択"
    echo "  5. このCodespaceを再起動 → このスクリプトを再実行"
    echo ""
    exit 1
fi

if [ -z "$X_BEARER_TOKEN" ]; then
    echo ""
    echo "⚠️  X_BEARER_TOKEN が未設定です（x-search MCPはスキップされます）"
    echo "   両方使いたい場合はCodespace Secretsに X_BEARER_TOKEN も追加してください"
    echo ""
fi

# ===== jq インストールチェック =====
if ! command -v jq &> /dev/null; then
    echo "📦 jq をインストール中..."
    sudo apt-get update -qq && sudo apt-get install -y -qq jq
fi

# ===== grok-consultant MCP セットアップ =====
echo ""
echo "📦 grok-consultant MCP を構築中..."
GROK_DIR="$HOME/.claude/mcp-servers/grok-consultant"
mkdir -p "$GROK_DIR"
cp "$SCRIPT_DIR/grok-consultant/server.py" "$GROK_DIR/"

if [ ! -d "$GROK_DIR/.venv" ]; then
    python3 -m venv "$GROK_DIR/.venv"
fi
"$GROK_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$GROK_DIR/.venv/bin/pip" install --quiet mcp openai
echo "✓ grok-consultant ready"

# ===== x-search MCP セットアップ =====
if [ -n "$X_BEARER_TOKEN" ]; then
    echo "📦 x-search MCP を構築中..."
    XSEARCH_DIR="$HOME/.claude/mcp-servers/x-search"
    mkdir -p "$XSEARCH_DIR"
    cp "$SCRIPT_DIR/x-search/server.py" "$XSEARCH_DIR/"

    if [ ! -d "$XSEARCH_DIR/.venv" ]; then
        python3 -m venv "$XSEARCH_DIR/.venv"
    fi
    "$XSEARCH_DIR/.venv/bin/pip" install --quiet --upgrade pip
    "$XSEARCH_DIR/.venv/bin/pip" install --quiet mcp httpx
    echo "✓ x-search ready"
fi

# ===== Claude Code config 更新 =====
echo ""
echo "📝 Claude Code config (~/.claude.json) を更新中..."

CLAUDE_CONFIG="$HOME/.claude.json"
TMP_CONFIG="$(mktemp)"

# 既存configがなければ初期化
if [ ! -f "$CLAUDE_CONFIG" ]; then
    echo '{"mcpServers": {}}' > "$CLAUDE_CONFIG"
fi

# mcpServersキーがなければ追加
if ! jq -e '.mcpServers' "$CLAUDE_CONFIG" > /dev/null; then
    jq '. + {"mcpServers": {}}' "$CLAUDE_CONFIG" > "$TMP_CONFIG"
    mv "$TMP_CONFIG" "$CLAUDE_CONFIG"
fi

# grok-consultant 追加
jq --arg key "$XAI_API_KEY" \
   --arg python "$GROK_DIR/.venv/bin/python" \
   --arg server "$GROK_DIR/server.py" \
   '.mcpServers["grok-consultant"] = {
       "type": "stdio",
       "command": $python,
       "args": [$server],
       "env": {
           "XAI_API_KEY": $key,
           "XAI_MODEL": "grok-4-1-fast-reasoning"
       }
   }' "$CLAUDE_CONFIG" > "$TMP_CONFIG"
mv "$TMP_CONFIG" "$CLAUDE_CONFIG"

# x-search 追加 (token設定時のみ)
if [ -n "$X_BEARER_TOKEN" ]; then
    XSEARCH_DIR="$HOME/.claude/mcp-servers/x-search"
    jq --arg token "$X_BEARER_TOKEN" \
       --arg python "$XSEARCH_DIR/.venv/bin/python" \
       --arg server "$XSEARCH_DIR/server.py" \
       '.mcpServers["x-search"] = {
           "type": "stdio",
           "command": $python,
           "args": [$server],
           "env": {
               "X_BEARER_TOKEN": $token
           }
       }' "$CLAUDE_CONFIG" > "$TMP_CONFIG"
    mv "$TMP_CONFIG" "$CLAUDE_CONFIG"
fi

echo "✓ config updated"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ セットアップ完了！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "次の手順:"
echo "  1. VS Code Desktop で Cmd+Shift+P"
echo "  2. 'Developer: Reload Window' を実行"
echo "  3. Claude Code に 'mcp使える？' と聞いて確認"
echo ""
