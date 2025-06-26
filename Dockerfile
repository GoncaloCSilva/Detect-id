# Usa uma imagem base do Python
FROM python:3.11-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Copia TODO o projeto (incluindo my_detect_id/)
COPY . .

# Instala as dependências
RUN pip install --upgrade pip && \
    pip install -r my_detectID/requirements.txt

# Dá permissão de execução ao script
RUN chmod +x entrypoint.sh

# Expõe a porta 8000 (usada por default pelo Django)
EXPOSE 8000

# Usa o script de entrada
CMD ["./entrypoint.sh"]