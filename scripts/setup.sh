#!/bin/bash

echo "🚀 Configurazione CosplayRadar..."

# Avvia i servizi Docker
echo "📦 Avvio servizi Docker..."
docker-compose up -d postgres redis

# Attendi che PostgreSQL sia pronto
echo "⏳ Attesa avvio PostgreSQL..."
sleep 5

# Naviga nella directory del database
cd packages/db

# Installa dipendenze Prisma
echo "📥 Installazione dipendenze Prisma..."
npm install

# Genera il client Prisma
echo "⚙️ Generazione client Prisma..."
DATABASE_URL="postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev?schema=public" npx prisma generate

# Sincronizza il database
echo "🗄️ Sincronizzazione database..."
DATABASE_URL="postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev?schema=public" npx prisma db push

# Torna al root
cd ../..

# Installa tutte le dipendenze
echo "📦 Installazione dipendenze monorepo..."
npm install

echo "✅ Setup completato!"
echo ""
echo "🌐 Per avviare l'applicazione:"
echo "cd apps/web && npm run dev"
echo ""
echo "📊 Per aprire Prisma Studio:"
echo "cd packages/db && npm run db:studio"
