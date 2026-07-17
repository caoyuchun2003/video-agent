#!/usr/bin/env bash
# 注入网关环境变量后 bsam package + deploy。绝不放千帆 Key。
set -euo pipefail

export PATH="${HOME}/Library/Python/3.9/bin:${HOME}/.local/bin:${PATH}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v bsam >/dev/null 2>&1; then
  echo "未找到 bsam。先: pip3 install --user bce-sam-cli"
  exit 1
fi

: "${BACKEND_URL:?请 export BACKEND_URL=http://IP/video}"
: "${GATEWAY_TOKEN:?请 export GATEWAY_TOKEN=...}"
ALLOW_ORIGIN="${ALLOW_ORIGIN:-https://video.yuchuntest.com}"

BASE_TEMPLATE="${ROOT}/template.yaml"
DEPLOY_TEMPLATE="${ROOT}/template.deploy.yaml"
trap 'rm -f "$DEPLOY_TEMPLATE"' EXIT

python3 - "$BASE_TEMPLATE" "$DEPLOY_TEMPLATE" <<'PY'
import os, re, sys
src, dst = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()

def esc(v: str) -> str:
    return v.replace("'", "''")

vars_block = (
    "        Variables:\n"
    f"          BACKEND_URL: '{esc(os.environ['BACKEND_URL'])}'\n"
    f"          GATEWAY_TOKEN: '{esc(os.environ['GATEWAY_TOKEN'])}'\n"
    f"          ALLOW_ORIGIN: '{esc(os.environ['ALLOW_ORIGIN'])}'\n"
)

text2, n = re.subn(
    r"        Variables:\n(?:(?:          .*\n))+",
    vars_block,
    text,
    count=1,
)
if n != 1:
    raise SystemExit(f"failed to inject Variables block (matches={n})")
open(dst, "w", encoding="utf-8").write(text2)
print("已生成 template.deploy.yaml（仅网关变量，无千帆 Key）")
PY

if grep -E 'QIANFAN|bce-v3/ALTAK' "$DEPLOY_TEMPLATE" >/dev/null; then
  echo "❌ 拒绝部署：deploy 模板疑似含千帆/BCE Key"
  exit 1
fi

echo "注入的变量名："
grep -E '^\s+[A-Z0-9_]+:' "$DEPLOY_TEMPLATE" | sed 's/:.*//'

echo ">>> bsam package"
bsam package -t "$DEPLOY_TEMPLATE"
echo ">>> bsam deploy"
bsam deploy -t "$DEPLOY_TEMPLATE"
rm -f "$ROOT"/*.zip "$ROOT"/src/*.zip
echo "部署完成。"
