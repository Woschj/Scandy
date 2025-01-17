FROM python:3.9-slim

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    python3-dev \
    cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Repository klonen und Branch wechseln
RUN git clone https://github.com/woschj/Scandy.git . && \
    git checkout electron

# Python-Abhängigkeiten installieren
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn && \
    pip install --no-cache-dir Flask-Session==0.5.0 && \
    pip install --no-cache-dir Flask-Compress

# Umgebungsvariablen setzen
ENV FLASK_APP=server.py
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1

# Verzeichnisse erstellen und Berechtigungen setzen
RUN mkdir -p /app/flask_session && \
    mkdir -p /app/logs && \
    mkdir -p /app/backups && \
    chmod -R 777 /app/flask_session && \
    chmod -R 755 /app

# Backup-Skript und Crontab kopieren
COPY backup_daily.sh /app/backup_daily.sh
COPY crontab /etc/cron.d/backup-cron

# Berechtigungen für Backup-System setzen
RUN chmod +x /app/backup_daily.sh && \
    chmod 0644 /etc/cron.d/backup-cron && \
    crontab /etc/cron.d/backup-cron

EXPOSE 5000

# Server und Cron starten
CMD service cron start && python server.py