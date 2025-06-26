# Usa uma imagem base do Python
FROM python:3.11-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Copia TODO o projeto (incluindo my_detect_id/)
COPY . .

# Instala as dependências
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expõe a porta 8000 (usada por default pelo Django)
EXPOSE 8000

# Comando para aplicar migrações e arrancar o servidor
CMD ["sh", "-c", "python my_detectID/manage.py migrate && python my_detectID/manage.py runserver 0.0.0.0:8000"]
