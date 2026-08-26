# subsidy-research

会津大学発ベンチャー／会津・福島拠点のテック系スタートアップ向けに、申請可能な補助金・助成金を **AIエージェントが毎朝自動で調査** し、差分を Discord に通知するリポジトリです。

---

## 何をするもの？

- 毎朝 **6:30 JST** に自動起動
- Web検索で新規案件を探し、既存案件の締切・公募状況を再確認
- 掲載URLの死活確認（リンク切れは除外）
- 前回結果との差分（🆕新規 / 🔄更新 / ✅終了）をレポート化
- **Discordに自動通知**（締切間近・関連度「高」・新規発見）

## 調査対象

| カテゴリ | 主な調査先 |
|---|---|
| 会津地域 | 会津若松市、会津大学、AiCT、大学発ベンチャー支援 |
| 福島県 | 福島イノベーション・コースト構想、産業振興センター、ハイテクプラザ |
| DeepTech・研究開発 | NEDO、JST（START / SBIR 等）、ディープテック系スタートアップ支援 |
| 東北 | 東北経済産業局、東北の自治体・VC連携プログラム |
| 全国（中小企業） | 経産省、中小企業庁、IPA、IT導入 / ものづくり / 持続化 / 新事業進出 |

掲載基準は「**上記属性の法人が申請主体になれること**」。大学研究者個人のみが対象の制度や個人向け給付は除外します。

## 通知イメージ

```
📋 補助金・助成金 日次調査レポート
2026-08-27 | 会津大学発ベンチャー / 会津・福島・東北・DeepTech・全国中小企業
🆕 新規 2件 | 📌 掲載中 18件 | ⚠️ 締切2週間以内 3件

⚠️ 終了間近（2週間以内）
**〇〇補助金**
締切 2026-09-05（残9日） / 補助額 上限500万円 / 状況 公募中
管轄: 福島県産業振興センター
```

## 仕組み

```
launchd（毎朝6:30 JST）
   └─ scripts/run-daily-research.sh
        └─ claude -p  ←  prompts/daily-research-prompt.md
             ├─ Web検索・URL死活確認・差分検知
             └─ reports/ を更新して git push
                  └─ GitHub Actions → Discord Webhook 通知
```

## ディレクトリ構成

```
prompts/daily-research-prompt.md   # エージェントに渡す調査手順
scripts/run-daily-research.sh      # launchdから呼ばれる実行スクリプト
reports/
  ├── latest.json                  # 最新の調査結果（差分検知の基準）
  └── YYYY-MM-DD.md                # 日次レポート
.github/workflows/discord-notify.yml  # push検知でDiscord通知
logs/                              # 実行ログ（git管理外）
```

> `reports/latest.json` のスキーマは通知スクリプトが参照します。項目名を変えると通知が壊れます。

## セットアップ

```sh
# 1. Discord Webhook を Secrets に登録
gh secret set DISCORD_WEBHOOK_URL --repo yhoi/subsidy-research

# 2. 定期実行を登録（macOS / launchd）
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.yhoi.subsidy-research.plist

# 3. 手動実行して動作確認
./scripts/run-daily-research.sh
```

## メモ

- 通知は **チャット本文のみ**。GitHubのレポートリンクは貼りません（Discord上で完結して読める形式）
- Discordの2000文字制限に合わせて自動で分割送信します
- 同日中に再実行しても、その日のレポートが既にあれば何もしません（冪等）
- 関連リポジトリと実行時刻: `pignet-subsidy-research` 6:00 / **本リポジトリ 6:30** / `pignet-competitor-research` 7:00
