#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}   FINALIZANDO INSTALAÇÃO DO DEV DASHBOARD    ${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ Este script precisa ser executado com sudo${NC}"
   echo -e "${YELLOW}Execute: sudo bash finalize-service.sh${NC}"
   exit 1
fi

echo -e "${GREEN}✅ Executando como root/sudo${NC}"
echo ""

# Step 1: Stop any running streamlit processes
echo -e "${YELLOW}1. Parando processos Streamlit existentes...${NC}"
pkill -f "streamlit run" 2>/dev/null || true
sleep 2
echo -e "${GREEN}   ✓ Processos parados${NC}"
echo ""

# Step 2: Copy service file
echo -e "${YELLOW}2. Instalando arquivo de serviço...${NC}"
cp /srv/projects/shared/dashboard/streamlit-dashboard.service /etc/systemd/system/
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ Arquivo de serviço copiado${NC}"
else
    echo -e "${RED}   ✗ Erro ao copiar arquivo de serviço${NC}"
    exit 1
fi
echo ""

# Step 3: Reload systemd
echo -e "${YELLOW}3. Recarregando configuração do systemd...${NC}"
systemctl daemon-reload
echo -e "${GREEN}   ✓ Systemd recarregado${NC}"
echo ""

# Step 4: Enable service for auto-start
echo -e "${YELLOW}4. Habilitando início automático...${NC}"
systemctl enable streamlit-dashboard.service
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ Serviço habilitado para início automático${NC}"
else
    echo -e "${RED}   ✗ Erro ao habilitar serviço${NC}"
    exit 1
fi
echo ""

# Step 5: Start the service
echo -e "${YELLOW}5. Iniciando o serviço...${NC}"
systemctl start streamlit-dashboard.service
sleep 3
echo -e "${GREEN}   ✓ Serviço iniciado${NC}"
echo ""

# Step 6: Check service status
echo -e "${YELLOW}6. Verificando status do serviço...${NC}"
echo ""
systemctl status streamlit-dashboard.service --no-pager | head -15
echo ""

# Step 7: Verify if service is running
if systemctl is-active --quiet streamlit-dashboard.service; then
    echo -e "${GREEN}===============================================${NC}"
    echo -e "${GREEN}     ✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!     ${NC}"
    echo -e "${GREEN}===============================================${NC}"
    echo ""
    echo -e "${GREEN}📊 Dashboard disponível em:${NC}"
    echo -e "${BLUE}   http://localhost:8081${NC}"
    echo -e "${BLUE}   http://$(hostname -I | awk '{print $1}'):8081${NC}"
    echo ""
    echo -e "${GREEN}⚙️ Configurações:${NC}"
    echo -e "   • Porta: 8081"
    echo -e "   • Auto-reload: HABILITADO"
    echo -e "   • Início automático: HABILITADO"
    echo ""
    echo -e "${GREEN}📝 Comandos úteis:${NC}"
    echo -e "   ${YELLOW}Ver status:${NC}     sudo systemctl status streamlit-dashboard"
    echo -e "   ${YELLOW}Ver logs:${NC}       sudo journalctl -u streamlit-dashboard -f"
    echo -e "   ${YELLOW}Reiniciar:${NC}      sudo systemctl restart streamlit-dashboard"
    echo -e "   ${YELLOW}Parar:${NC}          sudo systemctl stop streamlit-dashboard"
    echo -e "   ${YELLOW}Desabilitar:${NC}    sudo systemctl disable streamlit-dashboard"
    echo ""
    echo -e "${GREEN}📁 Localização do projeto:${NC}"
    echo -e "   /srv/projects/shared/dashboard"
    echo ""
    echo -e "${BLUE}===============================================${NC}"
    echo -e "${BLUE}    O dashboard reiniciará automaticamente     ${NC}"
    echo -e "${BLUE}    após reinicialização do servidor!          ${NC}"
    echo -e "${BLUE}===============================================${NC}"
else
    echo -e "${RED}===============================================${NC}"
    echo -e "${RED}     ❌ ERRO NA INSTALAÇÃO DO SERVIÇO         ${NC}"
    echo -e "${RED}===============================================${NC}"
    echo ""
    echo -e "${YELLOW}Verifique os logs com:${NC}"
    echo -e "   sudo journalctl -u streamlit-dashboard -n 50"
    echo ""
    echo -e "${YELLOW}Tente executar manualmente:${NC}"
    echo -e "   cd /srv/projects/shared/dashboard"
    echo -e "   ./manage.sh"
    exit 1
fi