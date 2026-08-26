#!/bin/zsh
# launchd から毎週月曜 6:30 JST に呼ばれる、週次補助金調査実行スクリプト
# 詳細プロンプト: ../prompts/weekly-research-prompt.md

set -uo pipefail

# 配置場所に依存しないよう、リポジトリ位置はスクリプト自身から解決する
SR_DIR="${SR_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
LOG_DIR="${SR_DIR}/logs"
PROMPT_FILE="${SR_DIR}/prompts/weekly-research-prompt.md"
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

  PROMPT="$(cat "${PROMPT_FILE}")"
  cd "${SR_DIR}"
  echo "$PROMPT" | "${CLAUDE_BIN}" -p --output-format text
  RC=$?
  echo "===== claude exit=${RC} at $(date '+%Y-%m-%d %H:%M:%S %Z') ====="
  exit $RC
} >> "${RUN_LOG}" 2>&1
