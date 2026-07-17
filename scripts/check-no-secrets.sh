#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bad=0
if git diff --cached --name-only 2>/dev/null | grep -E '(^|/)\.env$|\.zip$|template\.deploy\.yaml|(^|/)\.secrets/|credentials$' ; then
  echo "❌ 暂存区含敏感路径"; bad=1
fi
if git ls-files | grep -E '(^|/)\.env$|\.zip$|template\.deploy\.yaml|(^|/)\.secrets/' ; then
  echo "❌ 已跟踪敏感路径"; bad=1
fi
if git grep -nE 'bce-v3/ALTAK-[A-Za-z0-9]+/[a-f0-9]{20,}' -- . ':(exclude)*.md' ':(exclude).env.example' 2>/dev/null; then
  echo "❌ 仓库内容疑似含真实 Key"; bad=1
fi
if [[ "$bad" -ne 0 ]]; then exit 1; fi
echo "✅ 未发现已跟踪/暂存的密钥"
