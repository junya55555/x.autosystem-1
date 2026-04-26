# MCP Setup for Cross-Codespace Use

このディレクトリは、新Codespaceに **grok-consultant MCP**（Grokを第三者意見で呼べる）と **x-search MCP**（X API v2で投稿検索）を引き継ぐためのものです。

## 🚀 新Codespaceでのセットアップ手順

### Step 1: GitHubにCodespace User Secretsを登録（初回のみ）

1. ブラウザで [https://github.com/settings/codespaces](https://github.com/settings/codespaces) にアクセス
2. **"Codespaces secrets"** セクション → **"New secret"**
3. 以下2つを登録：

| Name | Value | Repository access |
|---|---|---|
| `XAI_API_KEY` | xaiの APIキー | autosystem-2, autosystem-3 等を選択 |
| `X_BEARER_TOKEN` | X API Bearer Token | 同上 |

> 既存値は autosystem-1 のCodespace所有者なら `~/.claude.json` で確認可能

4. 既に作成済みのCodespaceは**一度停止＆再起動**でSecretsが反映される

### Step 2: 新Codespaceでセットアップスクリプト実行

新Codespaceのターミナルで（テンプレcloneと同じタイミングで実行可）：

```bash
git clone https://github.com/junya55555/x.autosystem-1.git /tmp/setup-source
cp -r /tmp/setup-source/_templates ./
bash /tmp/setup-source/_mcp-servers/setup.sh
rm -rf /tmp/setup-source
```

### Step 3: Claude Code をリロード

VS Code Desktop で：
- `Cmd + Shift + P`
- `Developer: Reload Window` を選択

### Step 4: 動作確認

新CodespaceのClaudeに：
```
mcp__grok-consultant__ask_grok と mcp__x-search__search_x_recent が使える？
```
と聞いて、両方使えればOK 🌷

---

## 🔧 構成内容

```
_mcp-servers/
├── grok-consultant/
│   └── server.py        # Grok APIをMCPツールとして公開
├── x-search/
│   └── server.py        # X v2 search APIをMCPツールとして公開
├── setup.sh             # セットアップ自動化スクリプト
└── README.md            # このファイル
```

## ⚠️ 注意

- **APIキーをコミットしないでください**。セットアップスクリプトは環境変数から読みます
- Codespace User Secretsは**ユーザー単位**なので、3アカウント分のリポ全てで同じキーが使われます
- `XAI_API_KEY` と `X_BEARER_TOKEN` は autosystem-1 の `~/.claude.json` に格納されています
