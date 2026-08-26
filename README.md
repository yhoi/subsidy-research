# 補助金・助成金 日次調査（会津大学発ベンチャー向け）

会津大学発ベンチャー／会津・福島拠点のテック系スタートアップが申請可能な補助金・助成金を、AIエージェントが毎日自動調査するリポジトリ。

`pignet-org/pignet-subsidy-research` の派生。調査ターゲット属性と通知先（Slack → Discord）を変更している。

## 仕組み

```
毎朝6:30 JST（launchd: com.yhoi.subsidy-research）
  ↓
scripts/run-daily-research.sh が claude -p を起動
  ↓
prompts/daily-research-prompt.md に従いWeb検索で調査
  ↓
各URLの死活確認（リンク切れは除外）
  ↓
前回結果（reports/latest.json）と差分検知
  ↓
reports/ にcommit & push
  ↓
GitHub Actions が検知 → Discord自動通知
```

## 調査対象

- 会津地域（会津若松市・会津大学・AiCT）／大学発ベンチャー支援
- 福島県（イノベーション・コースト構想、産業振興センター、ハイテクプラザ等）
- DeepTech・研究開発（NEDO / JST / ディープテック系スタートアップ支援）
- 東北（東北経済産業局ほか）
- 全国の中小企業向け（経産省・中小企業庁・IPA・IT導入／ものづくり／持続化 等）

## Discord通知

- push検知で `.github/workflows/discord-notify.yml` が Discord Webhook に投稿
- **チャット本文のみ**。GitHubのレポートリンクは貼らない
- Webhook URLは Secrets（`DISCORD_WEBHOOK_URL`）に保存
- 2000文字制限に合わせて自動分割送信

## セットアップ

```sh
# launchd登録
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.yhoi.subsidy-research.plist

# 手動実行
./scripts/run-daily-research.sh
```

競合調査（7:00 JST）・Pignet補助金調査（6:00 JST）と時間をずらして6:30 JSTに実行。
