#!/usr/bin/env bash
set -euo pipefail

# === CONFIG ===
APP_DIR=/home/ubuntu/Matin-Backend-2
DEPLOY_USER=ubuntu
PYTHON=python3
VENV_DIR="$APP_DIR/venv"
PROJECT_MODULE=dealer_project
SOCKET_FILE="$APP_DIR/gunicorn.sock"
DOMAIN=3.80.137.153
NUM_WORKERS=3

echo "=== Deploy Matin-Backend-2 (PORT 8080) ==="

if [ "$(id -u)" -ne 0 ]; then SUDO='sudo'; else SUDO=''; fi

$SUDO apt-get update -y
$SUDO apt-get install -y build-essential nginx curl $PYTHON-venv $PYTHON-dev python3-pip

$SUDO mkdir -p "$APP_DIR"
$SUDO chown -R $DEPLOY_USER:$DEPLOY_USER "$APP_DIR"

if [ ! -d "$VENV_DIR" ]; then
  sudo -u $DEPLOY_USER $PYTHON -m venv "$VENV_DIR"
fi

ACTIVATE_CMD="source \"$VENV_DIR/bin/activate\""
sudo -H -u $DEPLOY_USER bash -lc "${ACTIVATE_CMD} && pip install --upgrade pip setuptools wheel && pip install -r \"$APP_DIR/requirements.txt\""

sudo -H -u $DEPLOY_USER bash -lc "${ACTIVATE_CMD} && cd \"$APP_DIR\" && python manage.py migrate --noinput"
$SUDO mkdir -p "$APP_DIR/staticfiles"
$SUDO chown -R $DEPLOY_USER:$DEPLOY_USER "$APP_DIR/staticfiles"
sudo -H -u $DEPLOY_USER bash -lc "${ACTIVATE_CMD} && cd \"$APP_DIR\" && python manage.py collectstatic --noinput"

# === SYSTEMD SERVICE ===
GUNICORN_SERVICE_PATH=/etc/systemd/system/gunicorn_dealers_backend.service
$SUDO tee "$GUNICORN_SERVICE_PATH" > /dev/null <<EOF
[Unit]
Description=Gunicorn service for DEALERS Django backend
After=network.target

[Service]
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn --workers $NUM_WORKERS --bind unix:$SOCKET_FILE $PROJECT_MODULE.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

$SUDO systemctl daemon-reload
$SUDO systemctl enable gunicorn_dealers_backend.service
$SUDO systemctl restart gunicorn_dealers_backend.service

# === NGINX CONFIG ===
NGINX_CONF_PATH=/etc/nginx/sites-available/django_project_dealers
$SUDO tee "$NGINX_CONF_PATH" > /dev/null <<EOF
server {
    listen 8080;
    server_name $DOMAIN;

    location /static/ {
      alias $APP_DIR/staticfiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$SOCKET_FILE;
    }
}
EOF

$SUDO ln -sf "$NGINX_CONF_PATH" /etc/nginx/sites-enabled/django_project_dealers

$SUDO nginx -t
$SUDO systemctl restart nginx

echo "=== DEALERS PROJECT RUNNING AT http://$DOMAIN:8080 ==="
