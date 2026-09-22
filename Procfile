web: gunicorn kclc.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --threads 2 --timeout 120 --access-logfile - --error-logfile -
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput

