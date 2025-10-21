#!/bin/bash
python3 manage.py collectstatic && gunicorn --workers 3 --threads 4 --timeout 90 VTAPS.wsgi