# 1. Puxa a versão exata do Python
FROM python:2.7.13

# 2. Corrige os repositórios (Essencial para Debian Jessie não ser 404)
RUN echo "deb http://archive.debian.org/debian/ jessie main" > /etc/apt/sources.list && \
    echo "deb http://archive.debian.org/debian-security/ jessie/updates main" >> /etc/apt/sources.list && \
    echo "Acquire::Check-Valid-Until \"false\";" > /etc/apt/apt.conf.d/10no-check-valid-until

# 3. Instala o asn1c (que fornece o comando 'unber') e outras dependências de sistema
RUN apt-get update && apt-get install -y --force-yes \
    asn1c \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Define a pasta de trabalho
WORKDIR /app

# 5. Copia e instala as dependências Python (o cache de camada garante velocidade)
COPY tugas_legadao/requirements.txt .
RUN pip install --no-cache-dir pip==20.3.4 && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copia todos os scripts para dentro do container
COPY tugas_legadao/ .

# 7. Mantém o container rodando
CMD ["tail", "-f", "/dev/null"]