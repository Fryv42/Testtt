#!/usr/bin/env bash
# Первичная настройка сервера (запускать на VPS под root, один раз).
# Пароль и секреты в скрипт не вносятся.
set -euo pipefail

APP_DIR="/home/site1/app/sapere-aude"
APP_USER="site1"
GIT_REPO="${GIT_REPO:-git@gitlab.informatics.ru:2025-2026/online/s101/s114/sapere-aude.git}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo bash deploy/server-bootstrap.sh"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3 python3-venv python3-pip git nginx redis-server \
  postgresql postgresql-contrib

if ! id "$APP_USER" &>/dev/null; then
  useradd -m -s /bin/bash "$APP_USER"
fi

mkdir -p "$(dirname "$APP_DIR")"
chown -R "$APP_USER:$APP_USER" /home/site1/app

if [[ ! -d "$APP_DIR/.git" ]]; then
  sudo -u "$APP_USER" git clone -b "$DEPLOY_BRANCH" "$GIT_REPO" "$APP_DIR"
else
  echo "Repository already exists at $APP_DIR"
fi

cd "$APP_DIR"
sudo -u "$APP_USER" python3 -m venv venv
sudo -u "$APP_USER" bash -c "source venv/bin/activate && pip install -r requirements.txt"

if [[ ! -f "$APP_DIR/.env" ]]; then
  sudo -u "$APP_USER" cp .env.production.example .env
  echo "Edit $APP_DIR/.env (SECRET_KEY, DB, Redis) before going live."
fi

sudo -u "$APP_USER" mkdir -p logs
sudo -u "$APP_USER" bash -c "cd $APP_DIR && source venv/bin/activate && python manage.py migrate --noinput"
sudo -u "$APP_USER" bash -c "cd $APP_DIR && source venv/bin/activate && python manage.py collectstatic --noinput"

chmod +x "$APP_DIR/deploy/deploy.sh"

cp "$APP_DIR/deploy/sapere-aude.service" /etc/systemd/system/sapere-aude.service
systemctl daemon-reload
systemctl enable sapere-aude
systemctl start sapere-aude

cp "$APP_DIR/deploy/nginx-sapere-aude.conf" /etc/nginx/sites-available/sapere-aude
ln -sf /etc/nginx/sites-available/sapere-aude /etc/nginx/sites-enabled/sapere-aude
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "Bootstrap complete. Check: systemctl status sapere-aude && curl -s http://127.0.0.1/health/"
