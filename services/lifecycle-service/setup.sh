#!/bin/bash

# 🚀 Setup Script per Lifecycle Service
# Automatizza setup, test e deployment

set -e  # Exit on error

echo "🚀 Lifecycle Service Setup Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [[ ! -f "main.py" ]] || [[ ! -d "src" ]]; then
    log_error "Devi eseguire questo script dalla directory lifecycle-service"
    exit 1
fi

# Parse command line arguments
COMMAND=${1:-"help"}

case $COMMAND in
    "setup")
        log_info "Configurazione iniziale..."
        
        # Check Python version
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        log_info "Python version: $PYTHON_VERSION"
        
        if [[ $(echo "$PYTHON_VERSION < 3.9" | bc -l) -eq 1 ]]; then
            log_error "Python 3.9+ richiesto, trovato $PYTHON_VERSION"
            exit 1
        fi
        
        # Create virtual environment if it doesn't exist
        if [[ ! -d "venv" ]]; then
            log_info "Creazione virtual environment..."
            python3 -m venv venv
            log_success "Virtual environment creato"
        fi
        
        # Activate virtual environment
        log_info "Attivazione virtual environment..."
        source venv/bin/activate
        
        # Install dependencies
        log_info "Installazione dipendenze..."
        pip install --upgrade pip
        pip install -r requirements.txt
        log_success "Dipendenze installate"
        
        # Create __init__.py files
        log_info "Creazione file __init__.py..."
        touch src/__init__.py
        touch src/core/__init__.py
        touch src/database/__init__.py
        touch src/api/__init__.py
        log_success "File __init__.py creati"
        
        # Check configuration
        if [[ -f "config/lifecycle_rules.json" ]]; then
            log_success "Configurazione lifecycle_rules.json trovata"
        else
            log_error "File config/lifecycle_rules.json mancante!"
            exit 1
        fi
        
        log_success "Setup completato! Usa './setup.sh test' per testare il servizio"
        ;;
        
    "test")
        log_info "Esecuzione test completi..."
        
        # Activate virtual environment if exists
        if [[ -d "venv" ]]; then
            source venv/bin/activate
        fi
        
        # Run tests
        log_info "Test componenti base..."
        python test_service.py
        
        if [[ $? -eq 0 ]]; then
            log_success "Test base completati con successo"
        else
            log_error "Test base falliti"
            exit 1
        fi
        
        # Test stats
        log_info "Test statistiche..."
        python main.py stats > /dev/null
        
        if [[ $? -eq 0 ]]; then
            log_success "Test statistiche completato"
        else
            log_error "Test statistiche fallito"
            exit 1
        fi
        
        log_success "Tutti i test completati con successo!"
        ;;
        
    "start")
        log_info "Avvio del servizio..."
        
        # Activate virtual environment if exists
        if [[ -d "venv" ]]; then
            source venv/bin/activate
        fi
        
        # Check if service is already running
        if lsof -i :8001 >/dev/null 2>&1; then
            log_warning "Il servizio sembra già in esecuzione sulla porta 8001"
            log_info "Usa './setup.sh stop' per fermarlo prima"
            exit 1
        fi
        
        log_info "Avvio server su porta 8001..."
        python main.py server &
        SERVER_PID=$!
        
        # Save PID for stopping
        echo $SERVER_PID > .server_pid
        
        # Wait a bit and test
        sleep 3
        
        if curl -s http://localhost:8001/health > /dev/null; then
            log_success "Servizio avviato correttamente!"
            log_info "API disponibili su http://localhost:8001"
            log_info "Health check: http://localhost:8001/health"
            log_info "Statistiche: http://localhost:8001/stats"
            log_info "Documentazione: http://localhost:8001/docs"
            log_info "Usa './setup.sh stop' per fermare il servizio"
        else
            log_error "Errore nell'avvio del servizio"
            kill $SERVER_PID 2>/dev/null || true
            rm -f .server_pid
            exit 1
        fi
        ;;
        
    "stop")
        log_info "Arresto del servizio..."
        
        if [[ -f ".server_pid" ]]; then
            SERVER_PID=$(cat .server_pid)
            if kill $SERVER_PID 2>/dev/null; then
                log_success "Servizio arrestato (PID: $SERVER_PID)"
            else
                log_warning "Processo non trovato, probabilmente già arrestato"
            fi
            rm -f .server_pid
        else
            log_warning "File PID non trovato, arresto manuale dei processi..."
            pkill -f "python main.py server" || true
            log_info "Processi arrestati"
        fi
        ;;
        
    "docker")
        log_info "Avvio con Docker Compose..."
        
        # Check if docker-compose exists
        if ! command -v docker-compose &> /dev/null; then
            log_error "docker-compose non trovato. Installalo prima di continuare."
            exit 1
        fi
        
        # Build and start
        log_info "Build e avvio dei container..."
        docker-compose up --build -d
        
        if [[ $? -eq 0 ]]; then
            log_success "Container avviati con successo!"
            log_info "Servizi disponibili:"
            docker-compose ps
            log_info "Logs: docker-compose logs -f"
            log_info "Stop: docker-compose down"
        else
            log_error "Errore nell'avvio dei container"
            exit 1
        fi
        ;;
        
    "status")
        log_info "Status del servizio..."
        
        # Check if running locally
        if [[ -f ".server_pid" ]]; then
            SERVER_PID=$(cat .server_pid)
            if kill -0 $SERVER_PID 2>/dev/null; then
                log_success "Servizio locale in esecuzione (PID: $SERVER_PID)"
            else
                log_warning "File PID trovato ma processo non attivo"
                rm -f .server_pid
            fi
        fi
        
        # Check port
        if lsof -i :8001 >/dev/null 2>&1; then
            log_info "Porta 8001 in uso"
            if curl -s http://localhost:8001/health > /dev/null; then
                log_success "Health check OK"
                echo "📊 Statistiche rapide:"
                curl -s http://localhost:8001/stats | python -c "
import json, sys
data = json.load(sys.stdin)
summary = data['data']['lifecycle_stages']
print(f\"  📁 Serie totali: {summary['total_series']}\")
print(f\"  ⏰ In grace period: {summary['grace_period']}\")
print(f\"  ✅ Attive: {summary['active_tracking']}\")
print(f\"  📦 Archiviate: {summary['archived']}\")
" 2>/dev/null || echo "  (Dettagli non disponibili)"
            else
                log_warning "Servizio non risponde su porta 8001"
            fi
        else
            log_info "Nessun servizio in esecuzione sulla porta 8001"
        fi
        
        # Check Docker
        if docker-compose ps 2>/dev/null | grep -q "lifecycle-service"; then
            log_info "Container Docker in esecuzione:"
            docker-compose ps
        fi
        ;;
        
    "logs")
        log_info "Visualizzazione logs..."
        
        if [[ -f ".server_pid" ]]; then
            log_info "Logs del servizio locale:"
            tail -f /dev/null  # Local logs would need to be redirected to file
        fi
        
        if docker-compose ps 2>/dev/null | grep -q "lifecycle-service"; then
            log_info "Logs dei container Docker:"
            docker-compose logs -f lifecycle-service
        else
            log_warning "Nessun container Docker trovato"
        fi
        ;;
        
    "clean")
        log_info "Pulizia ambiente..."
        
        # Stop services
        ./setup.sh stop 2>/dev/null || true
        
        # Docker cleanup
        docker-compose down 2>/dev/null || true
        
        # Remove virtual environment
        if [[ -d "venv" ]]; then
            log_info "Rimozione virtual environment..."
            rm -rf venv
        fi
        
        # Remove PID file
        rm -f .server_pid
        
        log_success "Pulizia completata"
        ;;
        
    "help"|*)
        echo "🔧 Script di gestione Lifecycle Service"
        echo ""
        echo "Comandi disponibili:"
        echo "  setup   - Configurazione iniziale (venv, dipendenze, ecc.)"
        echo "  test    - Esegue tutti i test"
        echo "  start   - Avvia il servizio in background"
        echo "  stop    - Ferma il servizio"
        echo "  status  - Mostra lo status del servizio"
        echo "  docker  - Avvia con Docker Compose"
        echo "  logs    - Visualizza i logs"
        echo "  clean   - Pulizia completa dell'ambiente"
        echo "  help    - Mostra questo help"
        echo ""
        echo "Esempi:"
        echo "  ./setup.sh setup    # Setup iniziale"
        echo "  ./setup.sh test     # Test completo"
        echo "  ./setup.sh start    # Avvia servizio"
        echo "  ./setup.sh status   # Controlla status"
        echo "  ./setup.sh docker   # Usa Docker"
        ;;
esac
