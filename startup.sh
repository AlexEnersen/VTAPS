#!/bin/bash
python3 manage.py collectstatic && gunicorn --workers 3 --threads 4 VTAPS.wsgi