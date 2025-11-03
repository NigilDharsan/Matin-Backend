# Django Ninja Dealer — README

This repository contains a Django/Ninja API for a dealer/product-supply system and a set of scripts to run locally and to deploy on an Ubuntu EC2 instance using Gunicorn + systemd + Nginx.

## What I added

- `run_server.bat` — Windows convenience script to create venv, install requirements, migrate, create a superuser (`admin`/`admin`), and run the dev server.
- `run_server.sh` — Linux convenience script for the same (make executable with `chmod +x run_server.sh`).
- `deploy_ec2.sh` — Opinionated deployment script for Ubuntu EC2 that installs packages, sets up venv, installs requirements, runs migrations, collectstatic, creates superuser, configures systemd for Gunicorn, and creates an Nginx site config.
- `gunicorn.service.template` — systemd unit template for Gunicorn (placeholders can be replaced or used by `deploy_ec2.sh`).
- `nginx_django.conf.template` — Nginx site config template (proxy to unix socket and serve static files).

> Files live in the repository root (see above names).

---

## Quick local setup (Linux/macOS)

1. Create and activate venv, install requirements, run migrations and start dev server:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # or use the scripts
python manage.py runserver
```

Or use the provided script (makes non-interactive superuser `admin/admin`):

```bash
chmod +x run_server.sh
./run_server.sh
```

## Quick local setup (Windows)

Double-click `run_server.bat` or run it from cmd.exe:

```cmd
run_server.bat
```

Note: adjust `requirements.txt`, database settings and environment values if needed.

---

## How to deploy to an Ubuntu EC2 instance (overview)

The included `deploy_ec2.sh` is an opinionated script that performs these steps:

- apt-get update + install system packages (git, nginx, python3-venv, etc.)
- optional git clone (if `GIT_REPO` env var is provided)
- create a Python virtualenv under `APP_DIR/venv`
- pip install -r requirements.txt
- run `manage.py migrate --noinput`
- run `manage.py collectstatic --noinput`
- create superuser if missing (non-interactive — env vars)
- create a `gunicorn.service` file at `/etc/systemd/system/gunicorn.service`
- enable & start `gunicorn` systemd service
- create an Nginx site config and restart nginx

### Usage example on EC2 (Ubuntu)

1. Copy the repo to your EC2 instance or set `GIT_REPO` to auto-clone.
2. Make the script executable and run it as a sudo-capable user:

```bash
chmod +x deploy_ec2.sh
# optional overrides, then run
export GIT_REPO="https://github.com/you/repo.git"
export APP_DIR=/home/ubuntu/django-ninja-dealer
export DEPLOY_USER=ubuntu
export DOMAIN=YOUR_DOMAIN_OR_IP
sudo ./deploy_ec2.sh
```

The script accepts other env vars to customize behavior (defaults are shown in the script):

- `GIT_REPO` — optional repo to clone
- `APP_DIR` — where the app will live on the server (default `/home/ubuntu/django-ninja-dealer`)
- `DEPLOY_USER` — unix user that will own files and run services (default `ubuntu`)
- `PROJECT_MODULE` — Django project module with `wsgi.py` (default `dealer_project`)
- `SOCKET_FILE` — UNIX socket path for Gunicorn (default `/run/gunicorn.sock`)
- `DOMAIN` — `server_name` for Nginx config
- `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL` — superuser credentials

> After the script runs, Gunicorn should be enabled as a systemd service and Nginx configured to proxy to the UNIX socket.

---

## systemd Gunicorn service (what `deploy_ec2.sh` creates)

The script writes `/etc/systemd/system/gunicorn.service` similar to `gunicorn.service.template`:

- runs Gunicorn from your venv
- binds to a unix socket
- runs as the `DEPLOY_USER`

If you'd like to store environment variables (SECRET_KEY, DB credentials, etc.) in a file, we can update the service to use `EnvironmentFile=/etc/<your-app>/gunicorn.env` and create an example `.env` file. Ask me to add that if you'd like.

---

## Nginx config (what `deploy_ec2.sh` creates)

The site config is based on `nginx_django.conf.template`:

- serves `/static/` directly from `{APP_DIR}/static/`
- proxies `/` to the unix socket at `SOCKET_FILE`

You will likely want to add SSL via Certbot (let me know and I can append Certbot/HTTPS steps).

---

## Notes & Troubleshooting

- Database: `deploy_ec2.sh` does not create a PostgreSQL database or user. Ensure your database exists and `dealer_project/settings.py` contains correct DB credentials or environment-based configuration.
- Secrets: Do not keep production `SECRET_KEY` or DB passwords in version control. Use environment variables or `EnvironmentFile` for systemd.
- Permissions: The script sets file ownership to `DEPLOY_USER`. Ensure the specified user exists on the EC2 instance.
- Socket path: `/run/gunicorn.sock` (default) needs appropriate permissions for Nginx to connect (same user/group or accessible by `www-data`). The service runs as the `DEPLOY_USER` — if Nginx can't connect, consider placing the socket under `/run/<appname>/gunicorn.sock` and giving group access to `www-data`.
- If Gunicorn fails to start, check:

```bash
sudo journalctl -u gunicorn -n 200 --no-pager
sudo systemctl status gunicorn -l
sudo nginx -t
sudo journalctl -u nginx -n 200 --no-pager
```

- If Nginx returns `502 Bad Gateway`, confirm Gunicorn is running and the socket path in Nginx matches the Gunicorn service.

---

## Authentication toggle (dev convenience)

This repo contains a toggle in `dealer_project/settings.py` named `API_AUTHENTICATION_ENABLED`:

- `False` — no authentication enforced (useful for local development)
- `True` — enables JWT-based authentication

If you deploy to EC2 for production, set `API_AUTHENTICATION_ENABLED=True` and ensure your client supplies a valid `Authorization: Bearer <token>` header.

---

## Next improvements I can add (pick any):

- Add an `EnvironmentFile` + example `.env` file + update `gunicorn.service` to load it (recommended)
- Add Certbot/HTTPS automation for the provided domain
- Add a small `systemd` pre-start script to create runtime folders and set permissions for the socket
- Add a health-check endpoint and a simple systemd unit `Restart=always` tuning

---

If you want, I can now add `EnvironmentFile` support to the `gunicorn.service` and create an example `/etc/<app>/gunicorn.env` file with instructions for securing it. Which improvement should I implement next?