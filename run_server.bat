@echo off
echo Creating Python virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing requirements...
pip install -r requirements.txt

echo Running migrations...
python manage.py migrate
python manage.py migrate core

echo Creating superuser...
set DJANGO_SUPERUSER_USERNAME=admin
set DJANGO_SUPERUSER_PASSWORD=admin
set DJANGO_SUPERUSER_EMAIL=admin@example.com
python manage.py createsuperuser --noinput

echo Starting Django server...
python manage.py runserver

pause