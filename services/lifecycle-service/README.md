# Lifecycle Service

Servizio per la gestione del ciclo di vita delle serie anime/manga nel sistema CosplayRadar.

## Funzionalità

- **Transizioni di Status**: Gestisce il passaggio delle serie da "NOT_YET_RELEASED" a "RELEASING" a "FINISHED"
- **Periodo di Grazia**: Sistema intelligente per mantenere serie attive per un periodo dopo il rilascio
- **Archiviazione Automatica**: Rimuove automaticamente serie con performance insufficienti
- **Pulizia Database**: Mantiene il database efficiente rimuovendo dati obsoleti
- **Monitoraggio Performance**: Traccia metriche e performance delle serie nel tempo

## Architettura

```
lifecycle-service/
├── src/
│   ├── core/
│   │   ├── lifecycle_engine.py      # Engine principale
│   │   ├── decision_maker.py        # Logica decisionale
│   │   └── rules_manager.py         # Gestione regole
│   ├── database/
│   │   ├── lifecycle_repository.py  # Repository database
│   │   └── models.py               # Modelli dati
│   ├── services/
│   │   ├── status_updater.py       # Aggiornamento status
│   │   ├── archiver.py             # Servizio archiviazione
│   │   └── cleanup_service.py      # Pulizia database
│   └── api/
│       └── routes.py               # API endpoints
├── config/
│   └── lifecycle_rules.json       # Configurazione regole
├── tests/
├── requirements.txt
├── main.py
└── docker-compose.yml
```

## Configurazione

Il servizio utilizza regole configurabili per decidere quando archiviare o mantenere le serie:

- **Periodo di Grazia**: 6 settimane dopo rilascio
- **Soglie Performance**: Basate su popularity, favourites, trending
- **Regole Speciali**: Per serie classiche o ad alta performance

## API Endpoints

- `GET /health` - Health check
- `GET /stats` - Statistiche lifecycle
- `POST /evaluate` - Valuta serie per lifecycle
- `POST /archive/{series_id}` - Archivia serie specifica
- `POST /cleanup` - Pulizia database

## Utilizzo

```bash
# Avvia il servizio
python main.py

# Esegui valutazione lifecycle
curl -X POST http://localhost:8083/evaluate

# Visualizza statistiche
curl http://localhost:8083/stats
```
