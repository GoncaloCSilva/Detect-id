# Usa uma imagem base do Python
FROM python:3.11-slim

RUN apt-get update && apt-get install -y libpq-dev gcc

# Define diretório de trabalho
WORKDIR /app

# Copia o projeto
COPY . /app

# Instala as dependências
RUN pip install --upgrade pip && \
    pip install -r requirements.txt || echo "Ignoring Windows-only packages"

# Expõe a porta 8000
EXPOSE 8000

# Comando para iniciar o servidor
CMD ["python", "my_detect_id/manage.py", "runserver", "0.0.0.0:8000"]
