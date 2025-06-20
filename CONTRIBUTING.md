# Contributing to CosplayRadar

Grazie per il tuo interesse nel contribuire a CosplayRadar! Questo documento fornisce le linee guida per contribuire al progetto.

## 🌊 Git Workflow

Utilizziamo una strategia Git flow semplificata con tre tipi di branch principali:

### Branch Structure

- **`main`** - Branch di produzione (sempre stabile)
- **`dev`** - Branch di sviluppo (integrazione delle feature)
- **`feature/*`** - Branch per nuove funzionalità

### Workflow

1. **Crea un branch feature dal branch `dev`:**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/nome-feature
   ```

2. **Sviluppa la tua feature:**
   ```bash
   # Fai le tue modifiche
   git add .
   git commit -m "feat: aggiungi nuova funzionalità"
   ```

3. **Push e crea una Pull Request:**
   ```bash
   git push origin feature/nome-feature
   # Crea PR su GitHub verso il branch `dev`
   ```

4. **Merge in `main`:**
   - Il merge da `dev` a `main` avviene solo dopo review e test completi
   - Solo i maintainer possono fare merge in `main`

## 📝 Conventional Commits

Utilizziamo [Conventional Commits](https://www.conventionalcommits.org/) per standardizzare i messaggi di commit:

### Formato
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types Supportati
- **`feat`** - Nuove funzionalità
- **`fix`** - Bug fix
- **`docs`** - Modifiche alla documentazione
- **`style`** - Formattazione, missing semi colons, etc
- **`refactor`** - Refactoring del codice
- **`test`** - Aggiunta o modifica di test
- **`chore`** - Manutenzione, update dipendenze
- **`ci`** - Modifiche CI/CD
- **`perf`** - Miglioramenti performance
- **`build`** - Modifiche al build system

### Esempi
```bash
feat: aggiungi dashboard analytics
fix: risolvi problema login OAuth
docs: aggiorna README con nuove istruzioni
chore: update dipendenze Next.js
test: aggiungi test per componente Character
ci: configura GitHub Actions per deploy
```

## 🔄 Pull Request Policy

### Prima di creare una PR

1. **Assicurati che il codice sia testato:**
   ```bash
   npm run test
   npm run lint
   ```

2. **Verifica che il build funzioni:**
   ```bash
   npm run build
   ```

3. **Formatta il codice:**
   ```bash
   npm run format
   ```

### Template PR

Quando crei una PR, includi:

```markdown
## 📝 Descrizione
Breve descrizione delle modifiche apportate.

## 🔗 Issue collegato
Fixes #(numero_issue)

## 🧪 Testing
- [ ] Test automatici passano
- [ ] Test manuali effettuati
- [ ] Nessuna regressione

## 📋 Checklist
- [ ] Il codice segue le linee guida del progetto
- [ ] I test sono aggiornati
- [ ] La documentazione è aggiornata
- [ ] Commit message seguono Conventional Commits
```

### Review Process

1. **Automatic Checks**: GitHub Actions esegue lint, test e build
2. **Code Review**: Almeno un maintainer deve approvare
3. **Manual Testing**: Se necessario, test manuali su staging
4. **Merge**: Squash and merge verso `dev`, merge commit verso `main`

## 🛠️ Setup Sviluppo

### Prerequisites
- Node.js 18+
- Docker & Docker Compose
- Python 3.11+

### Local Setup
```bash
# Clone e setup
git clone https://github.com/yourusername/cosplayradar
cd cosplayradar
npm install

# Setup hooks (automatico con prepare script)
npm run prepare

# Avvia ambiente di sviluppo
docker-compose up -d
npm run dev
```

### Pre-commit Hooks

Husky è configurato per eseguire automaticamente:

- **`pre-commit`**: Lint e format del codice
- **`commit-msg`**: Validazione con Commitlint

## 🏗️ Struttura del Progetto

```
cosplayradar/
├── apps/
│   ├── web/              # Frontend Next.js
│   └── scraper/          # Worker Python
├── packages/
│   ├── db/               # Schema Prisma
│   └── config/           # Configurazioni condivise
├── .github/
│   └── workflows/        # GitHub Actions
└── docs/                 # Documentazione
```

## 📚 Coding Standards

### TypeScript/JavaScript
- Usa TypeScript strict mode
- Preferisci funzioni arrow per i componenti
- Usa Prettier per la formattazione
- Segui le regole ESLint configurate

### Python
- Segui PEP 8
- Usa Black per la formattazione
- Type hints obbligatori
- Docstring per funzioni pubbliche

### CSS/Styling
- Usa Tailwind CSS classes
- Evita CSS custom quando possibile
- Mobile-first responsive design

## 🚀 Release Process

1. **Merge `dev` → `main`** dopo testing completo
2. **Tagging**: I maintainer creano tag semantici (v1.0.0)
3. **Deploy automatico** su push a `main`
4. **Release notes** generate da commit conventionali

## 🐛 Issue Reporting

Quando apri un issue, includi:

- **Descrizione chiara** del problema
- **Steps to reproduce**
- **Comportamento atteso vs attuale**
- **Screenshots** se applicabile
- **Ambiente** (OS, browser, versione Node.js)

## 💬 Community

- **Discussioni**: Usa GitHub Discussions per domande
- **Issues**: Solo per bug e feature request
- **PR**: Segui il template e le linee guida

## 📄 Licenza

Contribuendo a CosplayRadar, accetti che i tuoi contributi siano licenziati sotto la MIT License.

---

Grazie per contribuire a CosplayRadar! 🎭✨
