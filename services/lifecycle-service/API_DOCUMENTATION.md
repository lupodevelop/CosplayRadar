# API Documentation - Lifecycle Service

## Panoramica

Il **Lifecycle Service** è un microservizio dedicato alla gestione del ciclo di vita delle serie anime/manga in CosplayRadar. Gestisce le transizioni di stato, i periodi di grazia, la valutazione delle performance e l'archiviazione automatica.

## Endpoints Disponibili

### 🔍 Health Check

**GET** `/health`

Verifica lo stato del servizio e la connessione al database.

**Risposta di esempio:**
```json
{
    "status": "healthy",
    "service": "lifecycle-service",
    "version": "1.0.0",
    "timestamp": "2025-06-21T06:26:23.512690",
    "database": {
        "database_connected": true,
        "query_time_seconds": 0.01381,
        "total_series": 0,
        "timestamp": "2025-06-21T06:26:23.512621"
    }
}
```

### 📊 Statistiche

**GET** `/stats`

Recupera statistiche complete del lifecycle service.

**Risposta inclusa:**
- Distribuzione per stadi del lifecycle
- Statistiche per status AniList
- Metriche temporali
- Performance delle serie
- Configurazione delle regole

### ⚙️ Configurazione

**GET** `/config`

Recupera la configurazione attuale delle regole del lifecycle.

**PUT** `/config`

Aggiorna la configurazione delle regole.

**Body richiesta:**
```json
{
    "config": {
        "periods": {
            "grace_period_days": 42
        },
        "thresholds": {
            "keep_active": {
                "min_composite_score": 50.0
            }
        }
    }
}
```

### 🔄 Valutazione

**POST** `/evaluate`

Esegue una valutazione manuale del lifecycle per tutte le serie.

**Parametri query opzionali:**
- `dry_run=true`: Simula la valutazione senza modificare i dati
- `limit=50`: Limita il numero di serie da valutare

**Risposta di esempio:**
```json
{
    "success": true,
    "data": {
        "series_evaluated": 125,
        "decisions_made": 89,
        "archived_count": 23,
        "kept_active_count": 45,
        "extended_grace_count": 21,
        "execution_time_seconds": 2.34
    }
}
```

### 📦 Archiviazione

**POST** `/archive/{series_id}`

Archivia manualmente una serie specifica.

**Body richiesta:**
```json
{
    "reason": "Manual archive requested by admin"
}
```

### 🔄 Ripristino

**POST** `/restore/{series_id}`

Ripristina una serie archiviata al tracking attivo.

**Body richiesta:**
```json
{
    "reason": "Series gained popularity again"
}
```

### 🐛 Debug

**GET** `/debug/grace-expired`

Recupera le serie con periodo di grazia scaduto (per debugging).

## Codici di Stato

- **200**: Operazione completata con successo
- **400**: Richiesta non valida (parametri errati)
- **404**: Risorsa non trovata (serie non esistente)
- **500**: Errore interno del server

## Autenticazione

Attualmente il servizio non richiede autenticazione. Per l'ambiente di produzione, considerare l'aggiunta di:
- API Key authentication
- JWT tokens
- Rate limiting

## Esempi di Utilizzo

### Test Health Check
```bash
curl -X GET http://localhost:8001/health
```

### Visualizza Statistiche
```bash
curl -X GET http://localhost:8001/stats | jq .
```

### Esegui Valutazione Manual
```bash
curl -X POST http://localhost:8001/evaluate?dry_run=true
```

### Archivia Serie
```bash
curl -X POST http://localhost:8001/archive/12345 \
  -H "Content-Type: application/json" \
  -d '{"reason": "Low engagement for extended period"}'
```

## Configurazione Avanzata

Il servizio può essere configurato tramite:

1. **Variabili d'ambiente:**
   - `DATABASE_URL`: URL di connessione PostgreSQL
   - `LIFECYCLE_CONFIG_PATH`: Percorso file configurazione
   - `PORT`: Porta del server (default: 8001)
   - `HOST`: Host del server (default: 0.0.0.0)

2. **File di configurazione:** `config/lifecycle_rules.json`

3. **API endpoint:** `PUT /config`

## Monitoraggio

Per monitorare il servizio:

1. **Health Check regolari:** `GET /health`
2. **Statistiche periodiche:** `GET /stats`
3. **Log analysis:** Il servizio usa logging strutturato
4. **Performance metrics:** Incluse nelle statistiche

## Troubleshooting

### Servizio non si avvia
- Verificare connessione database
- Controllare il file di configurazione
- Verificare che la porta sia disponibile

### Database connection failed
- Verificare `DATABASE_URL`
- Controllare che PostgreSQL sia in esecuzione
- Verificare credenziali e permessi

### Evaluation errors
- Controllare i log per errori specifici
- Verificare la configurazione delle regole
- Testare con `dry_run=true`

## Integrazione con Altri Servizi

Il Lifecycle Service è progettato per integrarsi con:

1. **AniList Service**: Per recuperare dati delle serie
2. **Temperature Service**: Per metriche di trending
3. **Database principale**: Per aggiornamenti dello stato
4. **Sistema di notifiche**: Per alert automatici

## Prossimi Sviluppi

- [ ] Autenticazione API
- [ ] Rate limiting
- [ ] Webhook notifications
- [ ] Batch processing ottimizzato
- [ ] Machine learning per decisioni predittive
- [ ] Dashboard web per monitoraggio
