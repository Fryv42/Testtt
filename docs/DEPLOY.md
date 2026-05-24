# Деплой на сервер 188.127.254.20

Каталог приложения: `/home/site1/app/sapere-aude`

## 1. Первичная настройка сервера (один раз)

### 1.1 SSH-ключ для GitLab (на сервере, пользователь `site1`)

```bash
ssh root@188.127.254.20
sudo -u site1 mkdir -p /home/site1/.ssh
sudo -u site1 ssh-keygen -t ed25519 -f /home/site1/.ssh/id_ed25519_gitlab -N ""
sudo cat /home/site1/.ssh/id_ed25519_gitlab.pub
```



### 1.2 SSH-ключ для GitLab CI (на вашем ПК)

```bash
ssh-keygen -t ed25519 -C "gitlab-ci-deploy" -f ~/.ssh/gitlab_ci_sapere_aude -N ""
```

Публичный ключ на сервер:

```bash
ssh root@188.127.254.20
mkdir -p /root/.ssh
# вставить содержимое gitlab_ci_sapere_aude.pub в /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
```

### 1.3 Клонирование и bootstrap

```bash
ssh root@188.127.254.20
cd /home/site1/app/sapere-aude
# если репозитория ещё нет — clone от site1 с deploy key
bash deploy/server-bootstrap.sh
nano /home/site1/app/sapere-aude/.env   # SECRET_KEY, при необходимости PostgreSQL/Redis
systemctl restart sapere-aude
```

## 2. Переменные GitLab CI/CD

**Settings -> CI/CD -> Variables:**

| Variable | Value | Flags |
|----------|--------|--------|
| `SSH_PRIVATE_KEY` | приватный ключ `gitlab_ci_sapere_aude` | Masked, File |
| `DEPLOY_HOST` | `188.127.254.20` | — |
| `DEPLOY_USER` | `root` | — |
| `DEPLOY_PATH` | `/home/site1/app/sapere-aude` | — |
| `DEPLOY_BRANCH` | `main` или `feature/devops` | — |

## 3. Автоматический деплой

При push в `main` (и при необходимости в `feature/devops`) после успешных `lint` и `test` job `deploy:production` выполняет:

```bash
ssh $DEPLOY_USER@$DEPLOY_HOST "$DEPLOY_PATH/deploy/deploy.sh"
```

Ручной деплой на сервере:

```bash
ssh root@188.127.254.20
bash /home/site1/app/sapere-aude/deploy/deploy.sh
```

## 4. Проверка

```bash
curl http://188.127.254.20/health/
curl http://188.127.254.20/api/docs/
systemctl status sapere-aude
journalctl -u sapere-aude -n 50 --no-pager
```

## 5. Файлы в `deploy/`

| Файл | Назначение |
|------|------------|
| `deploy.sh` | Обновление кода, migrate, collectstatic, restart |
| `server-bootstrap.sh` | Первая установка (nginx, systemd, venv) |
| `sapere-aude.service` | Unit systemd |
| `nginx-sapere-aude.conf` | Прокси HTTP + WebSocket |
