# reports/latest.json スキーマ

週次調査の**状態を持つ唯一のファイル**。調査エージェントが書き、Discord通知スクリプトが読む。
両者の契約なので、**項目名を変える時はこのドキュメントと `scripts/notify_discord.py` を必ず一緒に直す。**

## トップレベル

| キー | 型 | 説明 |
|---|---|---|
| `survey_date` | string (`YYYY-MM-DD`) | この調査を実施した日 |
| `company` | string | 想定する申請主体の属性 |
| `subsidies` | array | 掲載中の案件。**終了した案件は配列から削除**（記録は調査レポートに残す） |
| `notes` | array of string | 翌日以降に持ち越す宿題・Watch事項 |

## subsidies[] の各案件

| キー | 型 | 必須 | 説明 |
|---|---|:--:|---|
| `id` | string | ○ | 案件の一意キー。日をまたいで**変えない**（差分検知の軸） |
| `name` | string | ○ | 補助金・助成金の正式名称 |
| `authority` | string | ○ | 管轄（省庁・自治体・実施団体） |
| `region` | string | ○ | 会津 / 会津若松市 / 福島県 / 東北 など |
| `summary` | string | ○ | 1〜2文の概要 |
| `amount` | string | ○ | **補助額**。例: `上限500万円`（通知の主役その1） |
| `subsidy_rate` | string | ○ | **補助率**。例: `2/3`, `1/2（小規模事業者は2/3）`（通知の主役その2） |
| `deadline` | string \| null | ○ | 締切。ISO日付。未確定なら `null` |
| `deadline_note` | string | ○ | 締切の補足。未確定の理由や次回公募の見込み |
| `url` | string | ○ | 公式ページのURL |
| `url_verified` | boolean | ○ | 死活確認で200だったか。`true` の時だけ通知に「公式サイト」ボタンが付く |
| `relevance` | `"高"` \| `"中"` \| `"低"` | ○ | 関連度。`高` は通知で常に詳細表示される |
| `relevance_reason` | string | ○ | なぜその関連度なのか |
| `status` | string | ○ | `公募中` / `公募開始待ち` / `結果発表待ち` など |
| `category` | string | ○ | 会津地域 / 福島県 / 広域 など（調査の重点3カテゴリに対応）|
| `new_this_survey` | boolean | – | **今回新規に見つけた案件だけ** `true`。前回分は毎回必ず外す |

## 通知側が使う項目

`scripts/notify_discord.py` は以下を参照する。ここを壊すと通知が崩れる。

- 振り分け: `new_this_survey`（🆕新規）、`relevance == "高"`（⭐）、`deadline` から算出した残日数 0〜14日（⚠️締切間近）
- 表示: `name` / `amount` / `subsidy_rate` / `deadline` / `deadline_note` / `authority` / `region` / `status`
- ボタン: `url` + `url_verified`

## 最小例

```json
{
  "survey_date": "2026-08-26",
  "company": "会津大学発ベンチャー（会津若松市の中小企業）",
  "subsidies": [
    {
      "id": "aizu-stepup-r8-2",
      "name": "会津若松市 ステップアップ応援補助金（令和8年度 第2回公募）",
      "authority": "会津若松市 商工課",
      "region": "会津",
      "summary": "市内での新規出店・事業拡大に要する経費を支援する市の独自制度。",
      "amount": "新規出店事業：中心市街地 創業者200万円／既存事業者250万円",
      "subsidy_rate": "1/2以内",
      "deadline": "2026-08-31",
      "deadline_note": "第2回公募の締切。第3回の有無は未公表。",
      "url": "https://www.city.aizuwakamatsu.fukushima.jp/",
      "url_verified": true,
      "relevance": "高",
      "relevance_reason": "会津若松市に拠点を置く中小企業が申請主体になれる。",
      "status": "公募中",
      "category": "会津地域",
      "new_this_survey": true
    }
  ],
  "notes": ["ふくしま産業応援ファンドの上限額が公式ページ本文に未記載。翌週に再確認。"]
}
```
