#!/bin/zsh
# launchd から毎週月曜 6:30 JST に呼ばれる、週次補助金調査実行スクリプト
# 詳細プロンプト: ../prompts/research-prompt.md

set -uo pipefail

# 配置場所に依存しないよう、リポジトリ位置はスクリプト自身から解決する
SR_DIR="${SR_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
LOG_DIR="${SR_DIR}/logs"
PROMPT_FILE="${SR_DIR}/prompts/research-prompt.md"
RUN_LOG="${LOG_DIR}/run-$(date +%Y-%m-%d).log"

mkdir -p "${LOG_DIR}"

# パス確保: launchdは最小PATHで起動するため node/npm が見えない
export PATH="/opt/homebrew/bin:/usr/local/bin:${HOME}/.local/bin:${PATH}"

CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude || echo "${HOME}/.local/bin/claude")}"

{
  echo "===== $(date '+%Y-%m-%d %H:%M:%S %Z') run start ====="
  if [[ ! -x "${CLAUDE_BIN}" ]]; then
    echo "ERROR: claude not found at ${CLAUDE_BIN}"
    exit 1
  fi

  if [[ ! -f "${PROMPT_FILE}" ]]; then
    echo "ERROR: prompt file not found: ${PROMPT_FILE}"
    exit 1
  fi

  # ネットワーク疎通待ち
  # 早朝の起動時はスリープ復帰直後でWiFiが未接続のことがあり、そのまま実行すると
  # ENOTFOUND で即死する（2026-08-27〜29に3日連続で発生）。
  # 最大30分（30秒×60回）待ち、それでも繋がらなければ調査せず終了する。
  ONLINE=0
  for i in $(seq 1 60); do
    if curl -sS -o /dev/null --max-time 10 https://api.anthropic.com/ 2>/dev/null; then
      ONLINE=1
      [[ $i -gt 1 ]] && echo "network ready after $(( (i - 1) * 30 ))s"
      break
    fi
    sleep 30
  done
  if [[ ${ONLINE} -ne 1 ]]; then
    echo "ERROR: 30分待ってもネットワークに到達できませんでした。調査をスキップします。"
    exit 1
  fi

  PROMPT="$(cat "${PROMPT_FILE}")"
  cd "${SR_DIR}"

  # 調査前に締切切れを落としておく。プロンプトにも削除ルールはあるが、
  # Pignet向けbotでLLMが「受付終了」のまま残す事故が続いたので、入力の時点で機械的に消す。
  python3 scripts/prune_expired.py reports/latest.json

  echo "$PROMPT" | "${CLAUDE_BIN}" -p --output-format text
  RC=$?
  echo "===== claude exit=${RC} at $(date '+%Y-%m-%d %H:%M:%S %Z') ====="

  # 調査後にも同じ掃除をかけ、残っていればコミットして押す。ここが最後の砦。
  python3 scripts/prune_expired.py reports/latest.json
  if ! git diff --quiet -- reports/latest.json; then
    git add reports/latest.json
    git commit -m "chore: 締切切れ・終了済み案件を latest.json から削除" \
      && git push \
      || echo "WARN: prune後のcommit/pushに失敗（次回の実行で再試行される）"
  fi
  exit $RC
} >> "${RUN_LOG}" 2>&1
