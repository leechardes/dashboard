# 🤖 Claude Manager Dashboard

Dashboard completo de gestão de processos Claude implementado em Streamlit.

## 📁 Estrutura Implementada

```
/srv/projects/shared/dashboard/
├── pages/
│   └── 🤖_Claude_Manager.py     # Interface principal do dashboard
├── components/
│   ├── claude_monitor.py        # Monitoramento de processos Claude
│   ├── claude_actions.py        # Ações sobre processos (kill, cleanup, etc)
│   ├── claude_config.py         # Gerenciamento de configurações
│   └── psutil_mock.py          # Mock do psutil para testes
├── config/
│   └── claude_limits.json       # Arquivo de configuração persistente
└── logs/
    └── claude_actions.log       # Log de todas as ações executadas
```

## 🎯 Funcionalidades Implementadas

### ✅ Componente de Monitoramento (`claude_monitor.py`)
- **get_claude_processes()** - Lista todos os processos Claude em execução
- **get_memory_stats()** - Estatísticas de uso de memória
- **get_user_ranking()** - Ranking de usuários por consumo de recursos
- **identify_orphans()** - Identifica processos órfãos
- **get_old_processes()** - Identifica processos antigos (>2h)
- **get_system_resources()** - Recursos do sistema (CPU, memória)

### ✅ Componente de Ações (`claude_actions.py`)
- **kill_process(pid)** - Mata um processo específico
- **kill_user_processes(username)** - Mata todos os processos de um usuário
- **kill_all_processes()** - Mata todos os processos Claude
- **clean_old_processes(hours)** - Limpa processos antigos
- **clean_orphan_processes()** - Limpa processos órfãos
- **get_action_logs()** - Recupera logs de ações
- Log automático de todas as ações em `/logs/claude_actions.log`

### ✅ Componente de Configuração (`claude_config.py`)
- **load_config()** / **save_config()** - Carrega/salva configurações
- **get_user_limit(username)** - Obtém limites de um usuário
- **set_user_limit()** - Define limites por usuário
- **get_global_setting()** / **set_global_setting()** - Configurações globais
- **export_config()** / **import_config()** - Export/import de configurações
- **reset_to_default()** - Reset para configurações padrão

### ✅ Interface Principal (`🤖_Claude_Manager.py`)
Dashboard completo com 4 tabs:

#### 📊 Tab Monitor
- **Tabela de processos** com colunas: PID, User, Memory, CPU, Time, Status, Actions
- **Botão Kill individual** por processo
- **Filtros** por usuário e status (Todos, Normais, Antigos, Órfãos)
- **Ordenação** por Memória, CPU, Tempo, PID
- **Ações em lote** para usuário selecionado
- **Status visual** com emojis (🟢 Normal, 🟡 Alta Mem, 🔴 Antigo, ⚠️ Órfão)
- **Auto-refresh** configurável (1-30 segundos)

#### 📈 Tab Analytics
- **Gráfico de pizza** - Distribuição de memória por usuário
- **Histograma** - Distribuição de tempo de execução
- **Ranking de usuários** por consumo de recursos
- **Estatísticas gerais** (processos antigos, órfãos, médias)
- **Gráfico temporal** - Histórico de uso de recursos
- **Métricas principais** no header (Total processos, Memória, Usuários ativos, CPU)

#### ⚙️ Tab Config
- **Sub-tab Usuários**: Configurar limites por usuário (memória, max processos, tempo)
- **Sub-tab Global**: Limpeza automática, alertas, limites gerais
- **Sub-tab Segurança**: Confirmações, export/import de config, reset
- **Configuração persistente** em arquivo JSON
- **Validação** de configurações com valores mínimos

#### 📋 Tab Logs
- **Exibição de logs** de ações executadas
- **Filtros** por nível (SUCCESS/ERROR/INFO), ação e usuário
- **Limpeza de logs antigos** (configurável)
- **Histórico completo** de todas as operações

## 🔧 Controles Globais (Sidebar)
- **Auto-refresh** habilitável com intervalo configurável
- **Refresh manual**
- **Ações globais**: Limpar órfãos, Limpar processos antigos (>2h)
- **Contador regressivo** para próximo refresh

## ⚙️ Configurações Padrão

```json
{
  "global_settings": {
    "default_memory_limit_mb": 1024,
    "max_process_age_hours": 2,
    "auto_cleanup_enabled": true,
    "auto_cleanup_interval_minutes": 30,
    "orphan_cleanup_enabled": true,
    "alert_memory_threshold_mb": 2048,
    "alert_cpu_threshold_percent": 80,
    "max_processes_per_user": 10
  },
  "user_limits": {
    "default": {
      "memory_limit_mb": 1024,
      "max_processes": 5,
      "max_runtime_hours": 4,
      "priority": "normal"
    }
  }
}
```

## 🔒 Recursos de Segurança
- **Confirmações obrigatórias** para ações destrutivas (kill all, kill user)
- **Log completo** de todas as ações executadas
- **Validação** de configurações
- **Permissões** através de sudo quando necessário
- **Backup automático** de configurações

## 🎨 Interface e UX
- **Design responsivo** com layout wide
- **Ícones visuais**: 🔴 Kill, ⚠️ Warning, 🟢 OK, 🟡 Atenção
- **Cores semânticas**: Verde (OK), Amarelo (Aviso), Vermelho (Perigo)
- **Métricas em tempo real** com st.metric
- **Tabelas interativas** com st.dataframe
- **Gráficos dinâmicos** com Plotly
- **Auto-refresh visual** com contador

## 🚀 Como Usar

1. **Acessar o dashboard**: Navegue até a página "🤖 Claude Manager"
2. **Monitorar processos**: Use a tab "Monitor" para ver processos em tempo real
3. **Analisar dados**: Tab "Analytics" para insights e estatísticas
4. **Configurar limites**: Tab "Config" para definir limites por usuário
5. **Ver histórico**: Tab "Logs" para acompanhar ações executadas

## 📝 Log de Ações

Todas as ações são registradas em formato estruturado:
```
2025-09-02T20:16:17 - SUCCESS - KILL_PROCESS: PID 1234 - User: john - Memory: 512MB - Signal: SIGTERM
2025-09-02T20:16:18 - SUCCESS - KILL_USER_PROCESSES: User: john - Mortos: [1234, 1235]
```

## 🔄 Auto-Refresh

- **Habilitável** via sidebar
- **Intervalo configurável** (1-30 segundos)
- **Contador visual** mostra tempo restante
- **Refresh manual** sempre disponível

## 💡 Detecção Inteligente

O sistema identifica processos Claude através de:
- **Nomes de processo**: claude, anthropic, claude-api, claude-cli
- **Linha de comando**: Padrões específicos como --model claude
- **Detecção de órfãos**: Processos sem pai ou filhos de init
- **Processos antigos**: Baseado em tempo de execução configurável

## 🎯 Status do Projeto

✅ **IMPLEMENTAÇÃO COMPLETA** - Todos os componentes funcionais:
- ✅ Monitor de processos em tempo real
- ✅ Sistema de ações com logs
- ✅ Configuração persistente e flexível  
- ✅ Interface completa com 4 tabs funcionais
- ✅ Auto-refresh e controles interativos
- ✅ Gráficos e analytics
- ✅ Segurança e confirmações
- ✅ Mock para testes (funciona sem psutil)

**Dashboard está pronto para uso em produção!** 🎉