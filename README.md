# DiscordClaudeCode

AI アシスタントが Discord を通じて人間と対話できる Model Context Protocol (MCP) サーバーの Python 実装です。AI システムと人間ユーザーの間の橋渡しを行い、協調的なタスク、意思決定、情報収集を可能にします。

## 機能

- **MCP 統合**: Claude Code などの AI アシスタント向けの完全な Model Context Protocol サポート
- **Discord フォーラム統合**: Discord フォーラムチャンネルでの整理された会話
- **AI 搭載タイトル生成**: Google Gemini AI を使用した自動スレッドタイトル
- **リアルタイム通信**: AI と人間の双方向通信
- **会話管理**: スレッドの永続化と履歴追跡
- **フォールバック システム**: AI サービスが利用できない場合の適切な縮退

## インストール

### 前提条件

- Python 3.8 以上
- Discord アカウントと bot
- Google AI API キー（オプション、タイトル生成強化のため）
- MCP 対応 AI クライアント（Claude Code など）

### セットアップ

1. **リポジトリをクローン**
   ```bash
   git clone https://github.com/0rnot/DiscordClaudeCode.git
   cd DiscordClaudeCode
   ```

2. **依存関係をインストール**
   ```bash
   pip install -r requirements.txt
   ```
   
   または、パッケージとしてインストール：
   ```bash
   pip install .
   ```

3. **Discord Bot をセットアップ**
   
   [Discord Developer Portal](https://discord.com/developers/applications) にアクセスして新しいアプリケーションを作成します：
   
   a. **アプリケーション作成**
      - 「New Application」をクリック
      - アプリの名前を入力
      - 「Create」をクリック
   
   b. **Application ID と Public Key を取得**
      - 「General Information」ページで **Application ID** をコピー
      - **Public Key** をコピー（リクエスト検証用）
   
   c. **Bot を設定**
      - 左サイドバーの「Bot」ページに移動
      - 「Reset Token」をクリックして新しい bot トークンを生成
      - **Bot Token** をコピー（機密情報 - 絶対に共有しないでください！）
      - 「Privileged Gateway Intents」で以下を有効化：
        - **Message Content Intent**（メッセージ処理に必要）
   
   d. **インストール設定**
      - 「Installation」ページに移動
      - 「Installation Contexts」で以下の両方を選択：
        - **Guild Install**（サーバーインストール用）
        - **User Install**（ユーザーインストール用）
      - 「Install Link」で「Discord Provided Link」を選択
      - 「Default Install Settings」で：
        - **Guild Install**: `applications.commands` と `bot` スコープを追加
        - **User Install**: `applications.commands` スコープを追加
        - bot 権限では、最低限以下を選択：
          - **Send Messages**
          - **Create Public Threads**
          - **Read Message History**

4. **Discord フォーラムチャンネルを作成**
   
   Discord サーバーでフォーラムチャンネルを作成します：
   - サーバー名を右クリック → 「チャンネルを作成」
   - チャンネルタイプで「フォーラム」を選択
   - 名前を付ける（例：「AI Questions」）
   - チャンネルを作成
   
   **必要な ID を取得：**
   - **チャンネル ID**: フォーラムチャンネルを右クリック → 「ID をコピー」
   - **ユーザー ID**: プロフィールを右クリック → 「ID をコピー」
   
   > **注意**: 「ID をコピー」オプションを表示するには、Discord 設定 → 詳細設定 → 開発者モードを有効にする必要があります

5. **Bot をインストール**
   
   テスト用に bot を両方のコンテキストにインストールします：
   
   a. **サーバーにインストール**
      - Developer Portal の Installation ページから Install Link をコピー
      - ブラウザに貼り付け
      - 「Add to Server」を選択してテストサーバーを選択
   
   b. **ユーザーアカウントにインストール**
      - 同じ Install Link を使用
      - 「Add to my apps」を選択してユーザーアカウントにインストール

## 設定

### 環境変数

上記で収集した値を使用して、以下の環境変数を設定します：

```bash
export DISCORD_BOT_TOKEN="your_discord_bot_token"        # Bot ページから
export GOOGLE_AI_API_KEY="your_google_ai_api_key"        # オプション、AI タイトル用
export HUMAN_CHANNEL_ID="your_discord_forum_channel_id"  # フォーラムチャンネル ID
export HUMAN_USER_ID="your_discord_user_id"              # ユーザー ID
```

**Google AI API キーの取得（オプション）：**
- [Google AI Studio](https://aistudio.google.com/) にアクセス
- 「Get API Key」→「Create API Key」をクリック
- 生成されたキーをコピー

Google AI API キーがない場合、タイトルはシンプルなフォールバック方式を使用します。

### Claude Code 統合

`~/.claude.json` ファイルに以下を追加：

```json
{
  "mcpServers": {
    "human-in-the-loop": {
      "command": "python3",
      "args": ["/path/to/DiscordClaudeCode/final_working_version.py"],
      "env": {
        "DISCORD_BOT_TOKEN": "your_discord_bot_token",
        "GOOGLE_AI_API_KEY": "your_google_ai_api_key",
        "HUMAN_CHANNEL_ID": "your_discord_forum_channel_id",
        "HUMAN_USER_ID": "your_discord_user_id"
      }
    }
  }
}
```

## 使用方法

### Claude Code での使用

設定後、Claude Code が自動的に MCP サーバーを使用します。以下のツールを使用できます：

```python
# 質問して人間の応答を待つ
response = ask_human("この設定で進めても良いですか？")

# 応答を待たずにステータス更新を送信
report_to_human("デプロイプロセスを開始しています...")
```

### 手動テスト

テスト用にサーバーを直接実行することもできます：

```bash
python3 final_working_version.py
```

その後、stdin/stdout 経由で MCP プロトコルを使用して対話できます。

## 動作原理

1. **AI リクエスト**: AI アシスタントが MCP プロトコル経由で質問を送信
2. **Discord スレッド**: Bot が Discord フォーラムチャンネルでスレッドを作成または再利用
3. **人間の応答**: 人間が Discord スレッドで応答
4. **AI 継続**: 応答が AI アシスタントに返される
5. **タイトル生成**: 会話に基づいてスレッドタイトルが自動更新

## 主要コンポーネント

### MCP サーバー (`final_working_version.py`)

- MCP プロトコル通信の処理
- Discord bot 統合の管理
- `ask_human` と `report_to_human` ツールの提供
- 会話履歴追跡の実装

### Discord 統合

- 整理された会話のためのフォーラムチャンネルサポート
- 永続的なスレッド管理
- メッセージ履歴追跡
- AI による自動タイトル生成

### AI タイトル生成

- Google Gemini AI を使用した会話コンテキスト分析
- 100 文字以内の説明的タイトル生成
- AI が利用できない場合のキーワード抽出へのフォールバック
- 会話の進行に応じたタイトルの動的更新

## プロジェクト構造

```
DiscordClaudeCode/
├── final_working_version.py    # メイン MCP サーバー実装
├── requirements.txt           # Python 依存関係
├── README.md                 # このファイル
├── setup.py                  # パッケージセットアップ
├── LICENSE                   # MIT ライセンス
└── .gitignore               # Git 除外ルール
```

## 依存関係

- `discord.py` (≥2.3.0) - Discord API 統合
- `mcp` (≥0.4.0) - Model Context Protocol サポート
- `PyNaCl` (≥1.4.0) - Discord 音声サポート
- `google-generativeai` (≥0.8.0) - AI タイトル生成（オプション）

## コントリビュート

1. リポジトリをフォーク
2. 機能ブランチを作成
3. 変更を実装
4. 十分にテスト
5. プルリクエストを送信

## ライセンス

このプロジェクトはオープンソースです。詳細は LICENSE ファイルを参照してください。

## トラブルシューティング

### よくある問題

1. **Bot が応答しない**: Bot の権限とトークンを確認
2. **スレッド作成に失敗**: チャンネルがフォーラムチャンネルであることを確認
3. **AI タイトルが機能しない**: Google AI API キーを確認
4. **MCP 接続に失敗**: 環境変数を確認

### デバッグモード

デバッグログを有効にするには：
```bash
export PYTHONPATH=/path/to/project
python3 -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

## 使用ガイドライン

この MCP サーバーは AI と人間の対話のために2つの主要なツールを提供します：

### ツール使用ガイドライン

対話の要件に基づいて、適切なツールを使用してください：

- **ask_human**: 人間の応答や確認が必要な場合に使用
  - 決定を要する質問
  - 確認リクエスト
  - 意見やフィードバックを求める
  - 例: "この設定で進めても良いですか？"

- **report_to_human**: 応答を要求しないステータス更新に使用
  - 進捗レポート
  - ステータス更新
  - 完了通知
  - 例: "デプロイプロセスを開始しています..."

### 判断基準

- **作業レポート・進捗更新** → `report_to_human` を使用
- **質問・確認・意見を求める** → `ask_human` を使用
- **「○○します」宣言** → `report_to_human` を使用
- **「どうしますか？」「どちらが良いですか？」質問** → `ask_human` を使用

応答は Discord に送信され、記録されます。人間に進捗を知らせるために適切な間隔で `report_to_human` を使用しますが、人間の入力が必要な場合は `ask_human` で会話を終了してください。

## サポート

問題、質問、貢献については、[GitHub リポジトリ](https://github.com/0rnot/DiscordClaudeCode) をご覧ください。

## 謝辞

このプロジェクトは [https://github.com/KOBA789/human-in-the-loop](https://github.com/KOBA789/human-in-the-loop) を参考にして作成されました。

---

*このプロジェクトは AI アシスタントと人間の専門知識の間の橋渡しを行い、Discord 統合を通じて協調的な問題解決と意思決定を可能にします。*