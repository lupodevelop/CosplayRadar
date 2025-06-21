# Deployment Guide - Lifecycle Service

## Guida Completa al Deployment

### Prerequisiti

- **Python 3.11+**
- **PostgreSQL 12+** 
- **Docker** (opzionale, per deployment containerizzato)
- **Git** per clonare il repository

### 1. Setup Base

```bash
# Clona il repository (se non già fatto)
cd /path/to/CosplayRadar/services/lifecycle-service

# Installa le dipendenze
pip install -r requirements.txt

# Crea i file __init__.py se mancanti
touch src/__init__.py
touch src/core/__init__.py  
touch src/database/__init__.py
touch src/api/__init__.py
```

### 2. Configurazione Database

#### Opzione A: PostgreSQL Locale

```bash
# Installa PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Crea database e utente
psql postgres
CREATE DATABASE cosplayradar_dev;
CREATE USER cosplayradar WITH PASSWORD 'dev_password_123';
GRANT ALL PRIVILEGES ON DATABASE cosplayradar_dev TO cosplayradar;
\q
```

#### Opzione B: Docker PostgreSQL

```bash
# Avvia PostgreSQL via Docker
docker run --name cosplayradar-postgres \
  -e POSTGRES_DB=cosplayradar_dev \
  -e POSTGRES_USER=cosplayradar \
  -e POSTGRES_PASSWORD=dev_password_123 \
  -p 5432:5432 -d postgres:13
```

### 3. Configurazione Ambiente

Crea file `.env` nella root del progetto:

```bash
# Database
DATABASE_URL=postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev

# Server
PORT=8001
HOST=0.0.0.0

# Configurazione
LIFECYCLE_CONFIG_PATH=./config/lifecycle_rules.json

# Logging
LOG_LEVEL=INFO
```

### 4. Test del Servizio

```bash
# Test completo dei componenti
python test_service.py

# Test delle statistiche
python main.py stats

# Test del server (in background)
python main.py server &

# Test delle API
curl http://localhost:8001/health
curl http://localhost:8001/stats

# Ferma il server
pkill -f "python main.py server"
```

### 5. Deployment Produzione

#### Opzione A: Docker Compose (Raccomandato)

```bash
# Build e avvio completo
docker-compose up --build -d

# Verifica i servizi
docker-compose ps
docker-compose logs lifecycle-service

# Test delle API
curl http://localhost:8001/health
```

#### Opzione B: Systemd Service

Crea file `/etc/systemd/system/lifecycle-service.service`:

```ini
[Unit]
Description=CosplayRadar Lifecycle Service
After=network.target postgresql.service

[Service]
Type=simple
User=cosplayradar
WorkingDirectory=/opt/cosplayradar/services/lifecycle-service
Environment=PATH=/opt/cosplayradar/venv/bin
ExecStart=/opt/cosplayradar/venv/bin/python main.py server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Attiva e avvia il servizio
sudo systemctl enable lifecycle-service
sudo systemctl start lifecycle-service
sudo systemctl status lifecycle-service
```

#### Opzione C: Supervisor

Installa supervisor e crea config:

```bash
pip install supervisor

# Config: /etc/supervisor/conf.d/lifecycle-service.conf
[program:lifecycle-service]
command=/path/to/python main.py server
directory=/path/to/lifecycle-service
user=cosplayradar
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/lifecycle-service.log
```

### 6. Scheduler Automatico

Per eseguire valutazioni automatiche:

#### Cron Job
```bash
# Aggiungi al crontab (crontab -e)
# Esegui valutazione ogni giorno alle 2:00
0 2 * * * cd /opt/cosplayradar/services/lifecycle-service && python main.py evaluate >> /var/log/lifecycle-cron.log 2>&1
```

#### Docker Scheduler
```bash
# Il docker-compose.yml include già un scheduler
docker-compose up scheduler -d
```

### 7. Monitoraggio

#### Health Check Script
```bash
#!/bin/bash
# healthcheck.sh

HEALTH_URL="http://localhost:8001/health"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $STATUS -eq 200 ]; then
    echo "✅ Lifecycle Service is healthy"
    exit 0
else
    echo "❌ Lifecycle Service is unhealthy (HTTP $STATUS)"
    exit 1
fi
```

#### Prometheus Metrics (Futuro)
Il servizio è pronto per l'integrazione con Prometheus:

```python
# Aggiungi al requirements.txt
prometheus-client==0.17.1

# Metrics endpoint già pianificato
# GET /metrics
```

### 8. Backup e Recovery

#### Backup Database
```bash
# Script di backup
#!/bin/bash
pg_dump -h localhost -U cosplayradar cosplayradar_dev > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup automatico (cron)
0 3 * * * /opt/scripts/backup_lifecycle_db.sh
```

#### Backup Configurazione
```bash
# Backup della configurazione
cp config/lifecycle_rules.json config/lifecycle_rules.json.backup.$(date +%Y%m%d)
```

### 9. Troubleshooting

#### Problemi Comuni

**Server non si avvia:**
```bash
# Controlla i log
python main.py server 2>&1 | tee server.log

# Verifica porta
netstat -tulpn | grep :8001

# Verifica database
python -c "import asyncpg; print('PostgreSQL driver OK')"
```

**Database connection failed:**
```bash
# Test connessione diretta
psql -h localhost -U cosplayradar -d cosplayradar_dev -c "SELECT 1;"

# Verifica URL
echo $DATABASE_URL
```

**Schema errors:**
```bash
# Ricrea schema
python -c "
import asyncio
from src.database.lifecycle_repository import LifecycleRepository
repo = LifecycleRepository('$DATABASE_URL')
asyncio.run(repo.ensure_schema())
"
```

### 10. Performance Tuning

#### Database
```sql
-- Indici per performance
CREATE INDEX IF NOT EXISTS idx_lifecycle_status ON lifecycle_series(lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_anilist_status ON lifecycle_series(anilist_status);
CREATE INDEX IF NOT EXISTS idx_evaluation_date ON lifecycle_series(last_evaluation);
```

#### Python
```bash
# Usa uvloop per performance async migliori
pip install uvloop

# Nel main.py
import uvloop
uvloop.install()
```

### 11. Sicurezza

#### API Authentication (Produzione)
```python
# Aggiungi al requirements.txt
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Implementa JWT authentication negli endpoints
```

#### Database Security
```bash
# Usa connessioni SSL in produzione
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

#### Firewall
```bash
# Apri solo le porte necessarie
ufw allow 8001/tcp  # API
ufw allow 5432/tcp  # PostgreSQL (solo se necessario)
```

### 12. Integrazione con CosplayRadar

Il lifecycle-service è progettato per integrarsi con:

1. **Database principale CosplayRadar**
2. **AniList Service** per dati delle serie
3. **Temperature Service** per trending data
4. **Sistema di notifiche** per alert

#### Schema Integration
Il servizio usa tabelle dedicate (`lifecycle_series`) che referenziano le tabelle principali di CosplayRadar.

### 13. Maintenance

#### Updates
```bash
# Update del servizio
git pull origin main
pip install -r requirements.txt --upgrade
docker-compose restart lifecycle-service
```

#### Log Rotation
```bash
# Logrotate config: /etc/logrotate.d/lifecycle-service
/var/log/lifecycle-service.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 cosplayradar cosplayradar
}
```

Questo servizio è ora completamente pronto per il deployment in produzione! 🚀
