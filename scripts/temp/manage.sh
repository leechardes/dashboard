#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if service is installed
check_service() {
    if systemctl list-unit-files | grep -q streamlit-dashboard.service; then
        return 0
    else
        return 1
    fi
}

# Function to run in development mode (without systemd)
run_dev() {
    echo -e "${GREEN}=== Executando em Modo Desenvolvimento ===${NC}"
    echo -e "${YELLOW}Auto-reload está habilitado!${NC}"
    echo -e "${YELLOW}Pressione Ctrl+C para parar${NC}"
    echo ""
    
    # Kill any existing streamlit process
    pkill -f "streamlit run" 2>/dev/null || true
    
    # Set environment variables
    export STREAMLIT_SERVER_PORT=8081
    export STREAMLIT_SERVER_ADDRESS=0.0.0.0
    export STREAMLIT_SERVER_RUN_ON_SAVE=true
    export STREAMLIT_SERVER_FILE_WATCHER_TYPE=auto
    export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    
    # Run streamlit
    cd /srv/projects/shared/dashboard
    ~/.local/bin/streamlit run app.py \
        --server.port 8081 \
        --server.address 0.0.0.0 \
        --server.runOnSave true \
        --server.fileWatcherType auto
}

# Main menu
echo -e "${BLUE}=== Streamlit Dashboard Manager ===${NC}"
echo ""

if check_service; then
    echo -e "${GREEN}Serviço systemd está instalado${NC}"
    echo ""
    echo "Opções:"
    echo "  1) Ver status do serviço"
    echo "  2) Ver logs do serviço"
    echo "  3) Reiniciar serviço"
    echo "  4) Parar serviço"
    echo "  5) Iniciar serviço"
    echo "  6) Executar em modo desenvolvimento (sem systemd)"
    echo "  7) Desinstalar serviço"
    echo "  0) Sair"
    echo ""
    read -p "Escolha uma opção: " choice
    
    case $choice in
        1)
            sudo systemctl status streamlit-dashboard --no-pager
            ;;
        2)
            echo -e "${YELLOW}Mostrando logs (Ctrl+C para sair)...${NC}"
            sudo journalctl -u streamlit-dashboard -f
            ;;
        3)
            sudo systemctl restart streamlit-dashboard
            echo -e "${GREEN}Serviço reiniciado!${NC}"
            sudo systemctl status streamlit-dashboard --no-pager
            ;;
        4)
            sudo systemctl stop streamlit-dashboard
            echo -e "${YELLOW}Serviço parado!${NC}"
            ;;
        5)
            sudo systemctl start streamlit-dashboard
            echo -e "${GREEN}Serviço iniciado!${NC}"
            sudo systemctl status streamlit-dashboard --no-pager
            ;;
        6)
            sudo systemctl stop streamlit-dashboard 2>/dev/null || true
            run_dev
            ;;
        7)
            echo -e "${YELLOW}Desinstalando serviço...${NC}"
            sudo systemctl stop streamlit-dashboard
            sudo systemctl disable streamlit-dashboard
            sudo rm /etc/systemd/system/streamlit-dashboard.service
            sudo systemctl daemon-reload
            echo -e "${GREEN}Serviço desinstalado!${NC}"
            ;;
        0)
            exit 0
            ;;
        *)
            echo -e "${RED}Opção inválida!${NC}"
            ;;
    esac
else
    echo -e "${YELLOW}Serviço systemd não está instalado${NC}"
    echo ""
    echo "Opções:"
    echo "  1) Instalar como serviço systemd"
    echo "  2) Executar em modo desenvolvimento"
    echo "  0) Sair"
    echo ""
    read -p "Escolha uma opção: " choice
    
    case $choice in
        1)
            echo -e "${YELLOW}Execute o seguinte comando para instalar:${NC}"
            echo "sudo bash install-service.sh"
            ;;
        2)
            run_dev
            ;;
        0)
            exit 0
            ;;
        *)
            echo -e "${RED}Opção inválida!${NC}"
            ;;
    esac
fi

echo ""
echo -e "${GREEN}Dashboard disponível em: http://localhost:8081${NC}"