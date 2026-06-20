#!/usr/bin/env bash
# publish.sh — one command to refresh the public cut of the-stable and push it.
#
# Runs the curated export (scripts/export_public.sh), which assembles the public tree AND runs the
# leak sweep. The sweep is the GATE: any leak makes the export exit non-zero, which aborts this script
# before a single commit — so "publish" can never push something the sweep would have caught.
#
# Usage:   bash scripts/publish.sh [DEST]        (DEST defaults to ../the-stable-public)
#          bash scripts/publish.sh --no-push     (refresh + commit locally, do not push)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUSH=1
DEST=""
for arg in "$@"; do
  case "$arg" in
    --no-push) PUSH=0 ;;
    *) DEST="$arg" ;;
  esac
done
DEST="${DEST:-$REPO/../the-stable-public}"

# 1. curated export + leak sweep (exits 2 on any leak — that aborts publish here)
bash "$REPO/scripts/export_public.sh" "$DEST"

# 2. commit the refreshed public tree
cd "$DEST"
[[ -d .git ]] || git init -b main
git add -A
if git diff --cached --quiet; then
  echo "· public tree already current — nothing to commit or push."
  exit 0
fi
git commit -q -m "the stable — public sync ($(date +%Y-%m-%d))"
echo "· committed: $(git log --oneline -1)"

# 3. push (unless --no-push, or no origin is set)
if [[ "$PUSH" -eq 0 ]]; then
  echo "· --no-push: committed locally. Push with: cd '$DEST' && git push origin HEAD"
elif git remote get-url origin >/dev/null 2>&1; then
  git push origin HEAD
  echo "· pushed to $(git remote get-url origin)"
else
  echo "· no origin remote set — committed locally only. Add a remote, then: git push origin HEAD"
fi
