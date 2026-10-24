#!/bin/zsh
# レシピ帳.md を再変換して GitHub Pages に反映する。使い方: ./deploy.sh
set -e
cd "$(dirname "$0")"
python3 build.py
git add -A
if git diff --cached --quiet; then echo "変更なし(レシピ帳.mdが前回と同じ)"; exit 0; fi
git commit -q -m "レシピ帳を更新 $(date +%F)"
git push -q origin main
echo "反映済み: https://carf-coder.github.io/jisui-recipes/ (1〜2分で更新)"
