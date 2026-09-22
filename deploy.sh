#!/bin/bash
echo "Deploying updates..."
git pull origin main
source venv/bin/activate
python manage.py migrate
killall gunicorn
echo "Done! The site and logos are updated."
