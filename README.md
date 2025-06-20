# CosplayRadar

Micro-SaaS platform per creator di cosplay con suggerimenti di personaggi trending e dashboard analytics.

## 🚀 Funzionalità

- **Dashboard Creator**: Suggerimenti di personaggi popolari da anime, manga, videogiochi e film
- **Trend Analysis**: Analisi real-time delle tendenze cosplay sui social media
- **Ispirazioni Visive**: Galleria di riferimenti e link ad altri cosplayer
- **Filtri Avanzati**: Per categoria, fandom, difficoltà e popolarità
- **Sistema Premium**: Accesso a funzionalità avanzate tramite abbonamento

## 🏗️ Architettura

```
cosplayradar/
├── apps/
│   ├── web/          # Frontend Next.js + Dashboard
│   └── scraper/      # Worker Python per scraping
├── packages/
│   ├── db/           # Schema Prisma condiviso
│   └── config/       # Configurazioni lint/prettier
└── docker-compose.yml
```

## 🛠️ Stack Tecnologico

- **Frontend**: Next.js 14, Tailwind CSS, TypeScript
- **Backend**: Next.js API Routes, NextAuth.js
- **Database**: PostgreSQL (Neon in prod, Docker in dev)
- **Scraping**: Python con Reddit API, Twitter API
- **Auth**: NextAuth con Google/GitHub OAuth
- **Pagamenti**: Stripe (mock in dev)
- **Deploy**: Vercel (frontend), Railway/Fly.io (scraper)
- **CI/CD**: GitHub Actions
- **Monorepo**: Turbo + npm workspaces

## 🚀 Quick Start

### Prerequisiti

- Node.js 18+
- Docker & Docker Compose
- Python 3.11+

### Installazione

```bash
# Clone del repository
git clone https://github.com/yourusername/cosplayradar
cd cosplayradar

# Installa dipendenze
npm install

# Setup del database locale
docker-compose up -d postgres

# Setup del database
cd packages/db
npx prisma migrate dev
cd ../..

# Setup env files
cp apps/web/.env.example apps/web/.env.local
cp apps/scraper/.env.example apps/scraper/.env

# Avvia in development
npm run dev
```

### Script Disponibili

- `npm run dev` - Avvia tutti i servizi in development
- `npm run build` - Build di produzione
- `npm run lint` - Linting di tutto il monorepo
- `npm run test` - Esegue tutti i test

## 🔧 Development

### Frontend (Next.js)
```bash
cd apps/web
npm run dev  # http://localhost:3000
```

### Scraper (Python)
```bash
cd apps/scraper
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
python src/main.py
```

### Database
```bash
cd packages/db
npx prisma studio  # http://localhost:5555
```

## 🌍 Environment Variables

Vedi i file `.env.example` in ogni app per le variabili richieste:
- `apps/web/.env.example` - Configurazione frontend
- `apps/scraper/.env.example` - Configurazione scraper

## 🚢 Deploy

### Frontend (Vercel)
Il frontend si deploya automaticamente su Vercel connesso al branch `main`.

### Scraper (Railway/Fly.io)
Il worker Python può essere deployato su Railway o Fly.io con deploy automatico.

### Database (Neon)
PostgreSQL in produzione su Neon con connection pooling.

## 🤝 Contribuire

Vedi [CONTRIBUTING.md](./CONTRIBUTING.md) per le linee guida di contribuzione.

## 📄 Licenza

MIT License - vedi [LICENSE](./LICENSE) per dettagli.

## 🔗 Links

- [Documentazione](https://docs.cosplayradar.com)
- [Demo Live](https://cosplayradar.vercel.app)
- [Status Page](https://status.cosplayradar.com)
