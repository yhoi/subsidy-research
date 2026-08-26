# reports/latest.json スキーマ

日次調査の**状態を持つ唯一のファイル**。調査エージェントが書き、Discord通知スクリプトが読む。
両者の契約なので、**項目名を変える時はこのドキュメントと `scripts/notify_discord.py` を必ず一緒に直す。**

## トップレベル

| キー | 型 | 説明 |
|---|---|---|
| `survey_date` | string (`YYYY-MM-DD`) | この調査を実施した日 |
| `company` | string | 想定する申請主体の属性 |
| `subsidies` | array | 掲載中の案件。**終了した案件は配列から削除**（記録は日次レポートに残す） |
| `notes` | array of string | 翌日以降に持ち越す宿題・Watch事項 |

## subsidies[] の各案件

| キー | 型 | 必須 | 説明 |
|---|---|:--:|---|
| `id` | string | ✅ | 案件の一意キー。日をまたいで**変えない**（差分検知の軸） |
| `name` | string | ✅ | 補助金・助成金の正式名称 |
| `authority` | string | ✅ | 管轄（省庁・自治体・実施団体） |
| `region` | string | ✅ | 会津若松市 / 福島県 / 東北 / 全国 など |
| `summary` | string | ✅ | 1〜2文の概要 |
| `amount` | string | ✅ | **補助額**。例: `上限500万円`（通知の主役その1） |
| `subsidy_rate` | string | ✅ | **補助率**。例: `2/3`, `1/2（小規模事業者は2/3）`（通知の主役その2） |
| `deadline` | string \| null | ✅ | 締切。ISO日付。未確定なら `null` |
| `deadline_note` | string | ✅ | 締切の補足。未確定の理由や次回公募の見込み |
| `url` | string | ✅ | 公式ページのURL |
| `url_verified` | boolean | ✅ | 死活確認で200だったか。`true` の時だけ通知に「公式サイト」ボタンが付く |
| `relevance` | `"高"` \| `"中"` \| `"低"` | ✅ | 関連度。`高` は通知で常に詳細表示される |
| `relevance_reason` | string | ✅ | なぜその関連度なのか |
| `status` | string | ✅ | `公募中` / `公募開始待ち` / `結果発表待ち` など |
| `category` | string | ✅ | IT導入・AI/DX、研究開発、地域活性化 など |
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
  "company": "会津大学発ベンチャー（会津若松市・AI/DeepTech系スタートアップ）",
  "subsidies": [
    {
      "id": "nedo-dtsu-10",
      "name": "NEDO ディープテック・スタートアップ支援事業（DTSU）第10回",
      "authority": "NEDO",
      "region": "全国",
      "summary": "研究開発型スタートアップの実用化開発を支援する大型公募。",
      "amount": "上限5億円（STS期）",
      "subsidy_rate": "2/3以内",
      "deadline": "2026-09-08",
      "deadline_note": "第10回公募の締切。次回は未公表。",
      "url": "https://www.nedo.go.jp/",
      "url_verified": true,
      "relevance": "高",
      "relevance_reason": "会津大学発のDeepTech系法人が主対象。",
      "status": "公募中",
      "category": "研究開発・DeepTech",
      "new_this_survey": true
    }
  ],
  "notes": ["IT導入補助金5次締切の日程は未公表。翌日以降に再確認。"]
}
```
