#!/bin/zsh
# launchd から 6:30 JST に呼ばれる、日次補助金調査実行スクリプト
# 詳細プロンプト: ../prompts/daily-research-prompt.md

set -uo pipefail

SR_DIR="/Users/yamashitayuuya/product/subsidy-research"
LOG_DIR="${SR_DIR}/logs"
PROMPT_FILE="${SR_DIR}/prompts/daily-research-prompt.md"
CLAUDE_BIN="/Users/yamashitayuuya/.local/bin/claude"
RUN_LOG="${LOG_DIR}/run-$(date +%Y-%m-%d).log"

mkdir -p "${LOG_DIR}"

# パス確保: launchdは最小PATHで起動するため node/npm が見えない
export PATH="/opt/homebrew/bin:/usr/local/bin:/Users/yamashitayuuya/.local/bin:${PATH}"

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
