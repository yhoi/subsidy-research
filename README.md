# subsidy-research

会津大学発ベンチャー／会津・福島県内の中小企業向けに、申請可能な補助金・助成金を **AIエージェントが毎週自動で調査** し、差分を Discord に通知するリポジトリです。

---

## 何をするもの？

- **毎日 6:30 JST**: 既存案件の締切・公募状況だけを追従（`latest.json` のみ更新・通知なし）
- **毎週月曜 6:30 JST**: 新規案件を探索して棚卸しし、レポートを作成して Discord に通知
- 掲載URLの死活確認（リンク切れは正しいURLを探し直し、見つからなければ「URL不明」と明記して残す）
- 前回結果との差分（新規 / 更新 / 終了 / スコープ外）をレポート化
- **Discordに自動通知**（締切間近・関連度「高」・新規発見）

## 調査対象

| カテゴリ | 主な調査先 |
|---|---|
| 会津地域 | 会津若松市、会津大学、AiCT、大学発ベンチャー支援 |
| 福島県 | 福島イノベーション・コースト構想、産業振興センター、ハイテクプラザ |
| 広域（県内中小企業が対象のもの） | 東北経済産業局など。**福島県に所在する中小企業が申請主体になれるものに限る** |

掲載基準は「**上記属性の法人が申請主体になれること**」。大学研究者個人のみが対象の制度や個人向け給付は除外します。

**対象外**（2026-08-26に方針変更）:

- 全国区の一般的な中小企業向け補助金（ものづくり / 持続化 / デジタル化・AI導入 / 事業再構築・新事業進出 など）… 広く知られており、この調査で発見する価値が薄いため
- DeepTech・研究開発系の大型支援（NEDO / JST START・SBIR など）… 申請規模と体制が現状に合わないため

ただし**福島県版・東北版として県内事業者向けの上乗せ枠がある場合は対象**です。

## 通知イメージ

**1回の調査につき1通だけ**投稿します。補助額と補助率を最上段に置き、公式サイトはボタンで開けます。

```
## 補助金・助成金 週次調査
2026-08-26  会津大学発ベンチャー / 会津・福島県の中小企業
新規 2 / 掲載中 10 / 締切2週間以内 2 / 関連度「高」 4
────────────────────────────
締切間近（2週間以内）
2026-08-31 / 残5日 / 補助率 1/2以内
  会津若松市 ステップアップ応援補助金（令和8年度 第2回公募）

2026-09-04 / 残9日 / 補助率 1/2以内
  ふくしま産業応援ファンド事業（助成金）2026年度後期公募
────────────────────────────
優先して見るべき案件
会津若松市 ステップアップ応援補助金（令和8年度 第2回公募）
補助額  新規出店事業：中心市街地 創業者200万円／既存事業者250万円
補助率  1/2以内
締切    2026-08-31（残5日）
管轄    会津若松市 商工課 / 会津 / 公募中     [ 公式サイト ]
```

- 詳細（ボタン付き）は優先度上位5件。残りは「その他の案件」に1行でまとめます
- 案件ごとに区切り線を入れます。**コードブロックは使いません**（Discordが折り返さず、ウィンドウ幅によって右端が切れるため）
- 左端のアクセントバーは状態で色が変わります（締切間近=バイオレット / 関連度「高」=スカイブルー / 新規のみ=エメラルド）

## 仕組み

```
GitHub Actions（毎日 21:30 UTC = 6:30 JST）
   └─ .github/workflows/research.yml
        ├─ 月曜以外 … claude -p ← prompts/daily-refresh-prompt.md
        │              既存案件の状態だけ更新 → latest.json を push（通知なし）
        └─ 月曜     … claude -p ← prompts/weekly-research-prompt.md
                       新規探索・URL死活確認・差分検知
                       → reports/ を push → 同ジョブ内で Discord 通知
```

ローカル実行（`scripts/run-weekly-research.sh`）は手動フォールバックとして残してあります。

## ディレクトリ構成

```
prompts/
  ├── weekly-research-prompt.md    # 週次の本調査（新規探索＋レポート）
  └── daily-refresh-prompt.md      # 日次のリフレッシュ（latest.json のみ）
scripts/
  ├── run-weekly-research.sh       # 手動実行用（ローカル）
  └── notify_discord.py            # latest.json → Discord通知の組み立て
reports/
  ├── latest.json                  # 最新の調査結果（差分検知の基準）
  └── YYYY-MM-DD.md                # 調査レポート
docs/latest-json.md                # latest.json のスキーマ定義
.github/workflows/
  ├── research.yml                 # 定期実行の本体（日次／週次）
  └── discord-notify.yml           # ローカルからpushした時の通知（フォールバック）
logs/                              # 実行ログ（git管理外）
```

`reports/latest.json` は **調査エージェントと通知スクリプトの間の契約**です。
項目を変更する時は [`docs/latest-json.md`](docs/latest-json.md) と `scripts/notify_discord.py` を必ず一緒に直してください。

## セットアップ

前提: [Claude Code](https://claude.com/claude-code) の `claude` コマンドと `gh` CLI が使えること。

```sh
# 1. Claude Code の CI用トークンを発行（Max/Proサブスクを使うのでAPI従量課金は発生しない）
claude setup-token
gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo <owner>/<repo>

# 2. Discord Webhook を登録
gh secret set DISCORD_WEBHOOK_URL --repo <owner>/<repo>

# 3. 手動で1回まわして動作確認
gh workflow run 補助金調査 -f mode=daily     # 日次リフレッシュだけ試す
gh workflow run 補助金調査 -f mode=weekly    # 本調査＋通知まで試す
gh run watch
```

定期実行は `.github/workflows/research.yml` の `schedule` で動くため、**ローカルPCの起動やWiFiに依存しません**。

<details>
<summary>ローカルで定期実行したい場合（launchd・任意）</summary>

```sh
sed "s|__REPO_DIR__|$(pwd)|g" launchd/com.yhoi.subsidy-research.plist.sample \
  > ~/Library/LaunchAgents/com.yhoi.subsidy-research.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.yhoi.subsidy-research.plist
launchctl list | grep subsidy-research
```

GitHub Actions と併用すると二重に走るので、**どちらか一方にしてください**。

</details>

## メモ

- 通知は **1回の調査につき1通**。連投すると読まれなくなるため、件数が多い日は表示を圧縮します
- GitHubのレポートリンクは貼りません（Discord上で完結して読める形式）
- 各案件の「公式サイト」ボタンは、URLの死活確認に成功した案件にのみ付きます
- 同日中に再実行しても、その日のレポートが既にあれば何もしません（冪等）
- 同じ日のレポートを作り直したい場合は、**作業ツリーから消すだけでは足りません**。コミット済みだとエージェントが事故と判断して `git checkout` で復元するため、`git rm reports/YYYY-MM-DD.md` してコミットしてから実行してください
- GitHub Actions 内から `GITHUB_TOKEN` で push しても他のワークフローは起動しません（ループ防止のGitHub仕様）。このため週次の通知は `research.yml` の中で直接送っています
- scheduled workflow は**リポジトリに60日間活動がないと自動停止**します。日次実行でコミットが入るため通常は問題ありません
