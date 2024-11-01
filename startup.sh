#!/bin/bash
python manage.py collectstatic && gunicorn --workers 2 VTAPS_v1.wsgi