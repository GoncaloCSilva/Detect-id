#!/bin/bash

# Aplica migrações
python my_detect_id/manage.py migrate

# Coleta ficheiros estáticos
python my_detect_id/manage.py collectstatic --noinput

# Inicia o servidor Django
python my_detect_id/manage.py runserver 0.0.0.0:8000