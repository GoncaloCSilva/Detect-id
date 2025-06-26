# Usa uma imagem base do Python
FROM python:3.11-slim

RUN apt-get update && apt-get install -y libpq-dev gcc

# Copia TODO o projeto (incluindo my_detect_id/)
COPY . /app

# Instala as dependências
RUN pip install --upgrade pip && \
    pip install -r requirements.txt || echo "Ignoring Windows-only packages"

# Expõe a porta 8000 (usada por default pelo Django)
EXPOSE 8000

# Comando para iniciar o servidor Django
CMD ["python", "my_detect_id/manage.py", "runserver", "0.0.0.0:8000"]
