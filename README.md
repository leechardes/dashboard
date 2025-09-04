# 📊 Streamlit Development Dashboard

Dashboard completo para desenvolvimento e monitoramento de projetos implementado em Streamlit.

## 🎯 Funcionalidades

- **Dashboard Principal**: Visão geral de projetos e sistema
- **Claude Manager**: Gerenciamento completo de processos Claude
- **Monitor de Sistema**: Acompanhamento de recursos em tempo real
- **Logs Centralizados**: Visualização de logs de diferentes fontes

## 📁 Estrutura do Projeto

```
/srv/projects/shared/dashboard/
├── app.py                          # Aplicação principal Streamlit
├── scripts/                        # Scripts de gerenciamento
│   ├── common.sh                   # Funções compartilhadas
│   ├── start.sh                    # Script de inicialização
│   ├── stop.sh                     # Script de parada
│   ├── restart.sh                  # Script de reinicialização
│   ├── status.sh                   # Status do dashboard
│   ├── logs.sh                     # Visualização de logs
│   ├── install-service.sh          # Instalação como serviço
│   └── uninstall-service.sh        # Remoção do serviço
├── systemd/
│   └── streamlit-dashboard.service # Arquivo de serviço systemd
├── pages/                          # Páginas do dashboard
│   └── 🤖_Claude_Manager.py       # Interface do Claude Manager
├── components/                     # Componentes reutilizáveis
│   ├── claude_monitor.py          # Monitoramento Claude
│   ├── claude_actions.py          # Ações sobre processos
│   └── claude_config.py           # Configurações
├── config/
│   └── claude_limits.json         # Configurações persistentes
├── logs/                          # Logs do sistema
│   └── claude_actions.log         # Log de ações
├── .env                           # Variáveis de ambiente
├── Makefile                       # Comandos de gerenciamento
└── requirements.txt               # Dependências Python
```

## 🚀 Installation as System Service

### Quick Setup
```bash
# Install and start as service
make install-service

# Check service status
make service-status

# View service logs
make service-logs
```

### Manual Management
```bash
# Start/stop/restart
make start
make stop  
make restart

# Check status
make status

# View logs
make logs
```

### Service Commands
```bash
# Enable auto-start on boot
make enable-service

# Disable auto-start
make disable-service

# Uninstall service
make uninstall-service
```

## 💻 Manual Installation

### Pré-requisitos
- Python 3.8+
- Virtual environment support
- sudo access (for systemd service)

### Instalação
```bash
# Clone ou acesse o diretório do projeto
cd /srv/projects/shared/dashboard

# Instalar dependências
make install

# Iniciar dashboard
make start
```

### Comandos Principais
```bash
# Gerenciamento básico
make install    # Instalar dependências
make start      # Iniciar dashboard
make stop       # Parar dashboard
make restart    # Reiniciar dashboard
make status     # Ver status
make logs       # Ver logs
make clean      # Limpar arquivos temporários

# Modo desenvolvimento
make dev        # Executar em modo desenvolvimento (foreground)

# Testes e manutenção
make test       # Executar testes básicos
make update     # Atualizar dependências
make backup     # Criar backup do projeto
```

## ⚙️ Configuration

### Environment Variables
O dashboard utiliza as seguintes variáveis de ambiente (arquivo `.env`):

```bash
# Server configuration
STREAMLIT_SERVER_PORT=8081
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Project paths
PROJECT_ROOT=/srv/projects
DOCS_PATH=/srv/projects
LOGS_PATH=/var/log
```

### Systemd Service
Quando instalado como serviço systemd, o dashboard:
- Inicia automaticamente no boot do sistema
- Executa como usuário `devadmin`
- Logs são direcionados para `/var/log/streamlit-dashboard.log`
- Reinicia automaticamente em caso de falha
- Utiliza configurações de segurança restritivas

## 📊 Claude Manager

### Funcionalidades Principais
- **Monitor de Processos**: Visualização em tempo real de processos Claude
- **Ações em Lote**: Kill individual ou por usuário
- **Analytics**: Gráficos de uso de recursos e estatísticas
- **Configuração**: Limites por usuário e configurações globais
- **Logs**: Histórico completo de ações executadas

### Segurança
- Confirmações obrigatórias para ações destrutivas
- Log completo de todas as ações
- Validação de configurações
- Backup automático de configurações

## 🔧 System Requirements

- **RAM**: Mínimo 512MB, recomendado 1GB+
- **CPU**: 1 core mínimo
- **Disk**: 100MB para aplicação + logs
- **Network**: Porta 8081 disponível
- **OS**: Linux com systemd (Ubuntu 18.04+, CentOS 7+)

## 📋 Service Management Commands

### Makefile Commands
```bash
# Basic management (scripts-based)
make start              # Start dashboard using scripts
make stop               # Stop dashboard using scripts
make restart            # Restart dashboard using scripts
make status             # Check dashboard status
make logs               # View dashboard logs

# Systemd service management
make install-service    # Install as systemd service
make uninstall-service  # Remove systemd service
make enable-service     # Enable auto-start on boot
make disable-service    # Disable auto-start
make service-status     # Check systemd service status
make service-logs       # View systemd service logs
make service-start      # Start systemd service
make service-stop       # Stop systemd service
make service-restart    # Restart systemd service
```

### Direct systemctl Commands
```bash
# Service control
sudo systemctl start streamlit-dashboard
sudo systemctl stop streamlit-dashboard
sudo systemctl restart streamlit-dashboard
sudo systemctl status streamlit-dashboard

# Enable/disable auto-start
sudo systemctl enable streamlit-dashboard
sudo systemctl disable streamlit-dashboard

# View logs
sudo journalctl -u streamlit-dashboard
sudo journalctl -u streamlit-dashboard -f  # Follow logs
```

## 🌐 Access

### URLs
- **Local**: http://localhost:8081
- **Network**: http://[server-ip]:8081 (se configurado)

### Pages
- **Main Dashboard**: Página inicial com visão geral
- **🤖 Claude Manager**: Gerenciamento de processos Claude
- **Other pages**: Páginas adicionais conforme configuração

## 🔍 Troubleshooting

### Dashboard não inicia
```bash
# Verificar status
make status

# Ver logs
make logs

# Verificar virtual environment
ls -la .venv/

# Reinstalar dependências
make clean && make install
```

### Serviço systemd não funciona
```bash
# Verificar status do serviço
sudo systemctl status streamlit-dashboard

# Ver logs do serviço
sudo journalctl -u streamlit-dashboard

# Verificar arquivo de serviço
cat /etc/systemd/system/streamlit-dashboard.service

# Recarregar e reiniciar
sudo systemctl daemon-reload
sudo systemctl restart streamlit-dashboard
```

### Porta em uso
```bash
# Verificar o que está usando a porta
sudo lsof -i :8081
sudo netstat -tuln | grep 8081

# Alterar porta no .env
echo "STREAMLIT_SERVER_PORT=8082" >> .env
```

### Problemas de permissão
```bash
# Verificar ownership
ls -la /srv/projects/shared/dashboard/

# Corrigir permissões (se necessário)
sudo chown -R devadmin:devadmin /srv/projects/shared/dashboard/
chmod +x scripts/*.sh
```

## 📝 Logs

### Locations
- **Manual mode**: `./streamlit.log`
- **Service mode**: `/var/log/streamlit-dashboard.log`
- **Service errors**: `/var/log/streamlit-dashboard.error.log`
- **Action logs**: `./logs/claude_actions.log`

### Log Viewing
```bash
# Recent logs
make logs

# Follow logs
make logs -f

# Service logs
make service-logs

# Error logs only
bash scripts/logs.sh -e

# Filter logs
bash scripts/logs.sh --filter ERROR
```

## 🔄 Updates

### Updating the Dashboard
```bash
# Update dependencies
make update

# Restart to apply changes
make restart

# For service installations
make service-restart
```

### Updating Service Configuration
```bash
# Edit service file
sudo vim /etc/systemd/system/streamlit-dashboard.service

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart streamlit-dashboard
```

## 🛡️ Security Notes

- Dashboard executa como usuário `devadmin`
- Acesso liberado na rede (0.0.0.0) - configure firewall se necessário
- Logs podem conter informações sensíveis
- Ações destrutivas requerem confirmação
- Configurações são validadas antes de aplicar

## 🎯 Status do Projeto

✅ **IMPLEMENTAÇÃO COMPLETA**
- ✅ Scripts de gerenciamento organizados
- ✅ Serviço systemd configurado
- ✅ Makefile atualizado com todos os comandos
- ✅ Auto-start no boot configurável
- ✅ Logs centralizados e organizados
- ✅ Interface completa do Claude Manager
- ✅ Sistema de configuração persistente
- ✅ Documentação completa

**Dashboard está pronto para uso em produção!** 🎉