#!/usr/bin/env bash
# Скрипт обновления приложения на сервере (вызывается из GitLab CI по SSH).
set -euo pipefail

APP_DIR="${APP_DIR:-/home/site1/app/sapere-aude}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-master}"
PYTHON="${PYTHON:-python3}"

cd "$APP_DIR"

if [[ ! -d .git ]]; then
  echo "ERROR: $APP_DIR is not a git repository. Run deploy/server-bootstrap.sh first."
  exit 1
fi

git fetch origin
git checkout "$DEPLOY_BRANCH"
git reset --hard "origin/$DEPLOY_BRANCH"

if [[ ! -d venv ]]; then
  "$PYTHON" -m venv venv
fi

# shellcheck source=/dev/null
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

if [[ ! -f .env ]]; then
  echo "ERROR: missing .env in $APP_DIR (copy from .env.production.example)"
  exit 1
fi

mkdir -p logs
python manage.py migrate --noinput
python manage.py collectstatic --noinput

if systemctl is-active --quiet sapere-aude 2>/dev/null; then
  systemctl restart sapere-aude
  echo "Service sapere-aude restarted."
else
  echo "WARN: systemd unit sapere-aude not found or inactive. Start manually."
fi

echo "Deploy finished: $(git rev-parse --short HEAD) on branch $DEPLOY_BRANCH"
