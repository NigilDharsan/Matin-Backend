#!/usr/bin/env bash
# deploy_ec2.sh
# Run on an Ubuntu EC2 instance as a sudo-capable user (ubuntu/ec2-user/etc).
# This script will:
#  - install system packages
#  - clone the repo (optional)
#  - create a Python venv and install requirements
#  - run migrations and collectstatic
#  - create a superuser (non-interactive via env vars)
#  - install and enable a systemd service for gunicorn
#  - configure nginx and start it

set -euo pipefail
IFS=$'\n\t'

# === CONFIG ===
# Edit these values as needed or export them before running the script
GIT_REPO=${GIT_REPO:-""}                # e.g. https://github.com/you/repo.git (optional)
APP_DIR=${APP_DIR:-/home/ubuntu/Matin-Backend}
DEPLOY_USER=${DEPLOY_USER:-ubuntu}
PYTHON=${PYTHON:-python3}
VENV_DIR="$APP_DIR/venv"
PROJECT_DIR=${PROJECT_DIR:-$APP_DIR}
PROJECT_MODULE=${PROJECT_MODULE:-dealer_project}  # Django project module that contains wsgi.py
SOCKET_FILE=${SOCKET_FILE:-/run/gunicorn.sock}
DOMAIN=${DOMAIN:-_}   # server_name for nginx; use your domain if available
NUM_WORKERS=${NUM_WORKERS:-3}

echo "Starting deployment script"
echo "APP_DIR=$APP_DIR"

# Ensure script is run with sudo privileges when needed
if [ "$(id -u)" -ne 0 ]; then
  SUDO='sudo'
else
  SUDO=''
fi

# Update & install system packages
echo "Updating apt and installing packages..."
$SUDO apt-get update -y
$SUDO apt-get install -y build-essential git nginx curl $PYTHON-venv $PYTHON-dev python3-pip

# Optional: clone repo if GIT_REPO provided and APP_DIR doesn't exist
if [ -n "$GIT_REPO" ]; then
  if [ -d "$APP_DIR/.git" ]; then
    echo "Repo already cloned in $APP_DIR — pulling latest"
    cd "$APP_DIR"
    git pull
  else
    echo "Cloning repo $GIT_REPO into $APP_DIR"
    $SUDO mkdir -p "$APP_DIR"
    $SUDO chown $DEPLOY_USER:$DEPLOY_USER $(dirname "$APP_DIR") || true
    sudo -u $DEPLOY_USER git clone "$GIT_REPO" "$APP_DIR"
  fi
fi

# Ensure app dir exists
$SUDO mkdir -p "$APP_DIR"
$SUDO chown -R $DEPLOY_USER:$DEPLOY_USER "$APP_DIR"

# Create and activate virtualenv, install requirements
echo "Creating virtualenv at $VENV_DIR"
if [ ! -d "$VENV_DIR" ]; then
  sudo -u $DEPLOY_USER $PYTHON -m venv "$VENV_DIR"
fi

echo "Activating venv and installing requirements"
ACTIVATE_CMD="source \"$VENV_DIR/bin/activate\""
# Install requirements as deploy user
sudo -H -u $DEPLOY_USER bash -lc "${ACTIVATE_CMD} && pip install --upgrade pip setuptools wheel && if [ -f \"$APP_DIR/requirements.txt\" ]; then pip install -r \"$APP_DIR/requirements.txt\"; fi"

# Collect static, migrate, create superuser
echo "Applying migrations and collecting static files"
# Allow optional environment overrides for superuser creation
DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-admin}
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@example.com}

sudo -H -u $DEPLOY_USER bash -lc "${ACTIVATE_CMD} && cd \"$APP_DIR\" && echo 'Running migrate' && python manage.py migrate --noinput"
sudo -H -u $DEPLOY_USER bash -lc "${ACTIVATE_CMD} && cd \"$APP_DIR\" && python manage.py collectstatic --noinput"

# Create superuser non-interactive if it does not exist
sudo -H -u $DEPLOY_USER bash -lc "${ACTIVATE_CMD} && cd \"$APP_DIR\" && python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); username='${DJANGO_SUPERUSER_USERNAME}'; email='${DJANGO_SUPERUSER_EMAIL}'; password='${DJANGO_SUPERUSER_PASSWORD}';
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print('Superuser already exists')\""

# Create systemd unit file for gunicorn
GUNICORN_SERVICE_PATH=/etc/systemd/system/gunicorn.service
echo "Creating systemd service file at $GUNICORN_SERVICE_PATH"
$SUDO tee "$GUNICORN_SERVICE_PATH" > /dev/null <<EOF
[Unit]
Description=gunicorn daemon for $PROJECT_MODULE
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
$SUDO systemctl enable gunicorn
$SUDO systemctl restart gunicorn || { echo "gunicorn failed to start — check logs"; journalctl -u gunicorn --no-pager --no-hostname -n 50; exit 1; }

# Nginx configuration
NGINX_CONF_PATH=/etc/nginx/sites-available/django_project
echo "Creating nginx config at $NGINX_CONF_PATH"
$SUDO tee "$NGINX_CONF_PATH" > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        alias $APP_DIR/static/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$SOCKET_FILE;
    }
}
EOF

$SUDO ln -sf "$NGINX_CONF_PATH" /etc/nginx/sites-enabled/django_project
$SUDO nginx -t
$SUDO systemctl restart nginx

# Firewall (optional)
if command -v ufw >/dev/null 2>&1; then
  echo "Configuring UFW to allow 'Nginx Full'"
  $SUDO ufw allow 'Nginx Full' || true
fi

echo "Deployment complete."
echo "Visit http://$DOMAIN (or the EC2 public IP)"

exit 0
