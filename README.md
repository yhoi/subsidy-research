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

**1日1通だけ**投稿します。補助額と補助率を最上段に置き、公式サイトはボタンで開けます。

```
📋 補助金・助成金 日次調査
2026-08-26  会津大学発ベンチャー / 会津・福島・東北・DeepTech・全国中小企業
🆕 新規 2  📌 掲載中 16  ⚠️ 締切2週間以内 4  ⭐ 関連度「高」 7
────────────────────────────
⚠️ 締切間近（2週間以内）
  締切         残    補助率     補助金
  2026-08-31   5日   1/2以内    会津若松市 ステップアップ応…
  2026-09-08   13日  2/3以内    NEDO ディープテック・スター…
────────────────────────────
⭐ 優先して見るべき案件
  NEDO DTSU 第10回公募
  💰 STS 3〜5億円、PCA 5〜10億円
  📊 補助率 2/3以内
  ⏳ 締切 2026-09-08（残13日）
  🏛 NEDO / 全国 / 公募中          [ 公式サイト ]
```

- 詳細（ボタン付き）は優先度上位5件。残りは「その他の注目案件」に1行でまとめます
- 締切間近は等幅テーブルで一覧化します

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
scripts/
  ├── run-daily-research.sh        # launchdから呼ばれる実行スクリプト
  └── notify_discord.py            # latest.json → Discord通知の組み立て
reports/
  ├── latest.json                  # 最新の調査結果（差分検知の基準）
  └── YYYY-MM-DD.md                # 日次レポート
docs/latest-json.md                # latest.json のスキーマ定義
.github/workflows/discord-notify.yml  # push検知で notify_discord.py を実行
logs/                              # 実行ログ（git管理外）
```

`reports/latest.json` は **調査エージェントと通知スクリプトの間の契約**です。
項目を変更する時は [`docs/latest-json.md`](docs/latest-json.md) と `scripts/notify_discord.py` を必ず一緒に直してください。

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

- 通知は **1日1通**。連投すると読まれなくなるため、件数が多い日は表示を圧縮します
- GitHubのレポートリンクは貼りません（Discord上で完結して読める形式）
- 各案件の「公式サイト」ボタンは、URLの死活確認に成功した案件にのみ付きます
- 同日中に再実行しても、その日のレポートが既にあれば何もしません（冪等）
- 関連リポジトリと実行時刻: `pignet-subsidy-research` 6:00 / **本リポジトリ 6:30** / `pignet-competitor-research` 7:00
