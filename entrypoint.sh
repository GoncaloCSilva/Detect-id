#!/bin/bash

# Aplica migrações
python my_detectID/manage.py migrate

# Coleta ficheiros estáticos
python my_detectID/manage.py collectstatic --noinput

# Inicia o servidor Django
python my_detectID/manage.py runserver 0.0.0.0:8000