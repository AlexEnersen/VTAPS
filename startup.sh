#!/bin/bash
python3 manage.py collectstatic && gunicorn --workers 2 VTAPS_v1.wsgi