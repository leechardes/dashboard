# Instruções Completas para Usar GitHub com Claude Code

## Configuração Inicial

### 1. Verificar se o GitHub CLI está instalado
```bash
which gh
# Se não estiver instalado:
# Linux/WSL: sudo apt install gh
# Mac: brew install gh
```

### 2. Autenticar no GitHub
```bash
# Verificar status de autenticação
gh auth status

# Se não estiver autenticado, fazer login
gh auth login
# Escolher: GitHub.com > HTTPS > Authenticate with browser
```

## Criar um Novo Repositório

### Opção 1: Usando GitHub CLI (Recomendado)
```bash
# Navegar até o diretório do projeto
cd /caminho/do/projeto

# Inicializar git se necessário
git init

# Criar .gitignore apropriado
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
.venv/
venv/
ENV/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
EOF

# Adicionar todos os arquivos
git add -A

# Fazer primeiro commit
git commit -m "Initial commit"

# Criar repositório no GitHub e fazer push
gh repo create nome-do-repositorio --public --source=. --remote=origin --push

# Para repositório privado, use --private ao invés de --public
```

### Opção 2: Repositório já existe no GitHub
```bash
# Adicionar remote
git remote add origin https://github.com/seu-usuario/nome-repo.git
# OU para SSH
git remote add origin git@github.com:seu-usuario/nome-repo.git

# Fazer push inicial
git push -u origin main
```

## Comandos Git Essenciais

### Status e Histórico
```bash
# Ver status atual
git status

# Ver histórico de commits
git log --oneline -10

# Ver diferenças não commitadas
git diff

# Ver diferenças staged
git diff --staged
```

### Fazer Commits
```bash
# Adicionar arquivos específicos
git add arquivo1.py arquivo2.py

# Adicionar todos os arquivos modificados
git add -A

# Commit com mensagem
git commit -m "Descrição clara da mudança"

# Commit com mensagem detalhada
git commit -m "Título do commit

Descrição mais detalhada das mudanças:
- Mudança 1
- Mudança 2

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Push e Pull
```bash
# Enviar commits para o GitHub
git push

# Buscar e integrar mudanças do GitHub
git pull

# Apenas buscar mudanças (sem integrar)
git fetch
```

### Branches
```bash
# Criar nova branch
git checkout -b nome-da-branch

# Mudar para branch existente
git checkout nome-da-branch

# Listar branches
git branch -a

# Fazer merge de branch
git checkout main
git merge nome-da-branch

# Deletar branch local
git branch -d nome-da-branch

# Push de nova branch
git push -u origin nome-da-branch
```

## Criar Pull Request

### Usando GitHub CLI
```bash
# Criar PR da branch atual
gh pr create --title "Título do PR" --body "Descrição detalhada"

# Criar PR interativo
gh pr create

# Criar PR com template completo
gh pr create --title "Adiciona nova feature X" --body "$(cat <<'EOF'
## Resumo
Descrição breve das mudanças

## Mudanças
- Adicionado recurso X
- Corrigido bug Y
- Melhorado performance de Z

## Testes
- [ ] Testes unitários passando
- [ ] Testado manualmente
- [ ] Documentação atualizada

## Screenshots (se aplicável)
[Adicionar imagens se necessário]
EOF
)"

# Listar PRs
gh pr list

# Ver status de PR
gh pr status

# Fazer merge de PR
gh pr merge [número]
```

## Trabalhando com Issues

```bash
# Criar issue
gh issue create --title "Bug: Descrição" --body "Detalhes do bug"

# Listar issues
gh issue list

# Ver issue específica
gh issue view [número]

# Comentar em issue
gh issue comment [número] --body "Comentário"

# Fechar issue
gh issue close [número]
```

## Reverter Mudanças

### Descartar mudanças locais
```bash
# Descartar mudanças em arquivo específico
git checkout -- arquivo.py

# Descartar TODAS as mudanças não commitadas
git reset --hard HEAD

# Voltar ao commit anterior (mantendo mudanças)
git reset --soft HEAD~1

# Voltar ao commit anterior (descartando mudanças)
git reset --hard HEAD~1
```

### Reverter commit já enviado
```bash
# Criar novo commit que desfaz o anterior
git revert HEAD

# Reverter commit específico
git revert [hash-do-commit]
```

## Exemplo Prático Completo

### Cenário: Criar projeto dashboard e publicar no GitHub

```bash
# 1. Navegar até o diretório
cd /srv/projects/shared/dashboard

# 2. Inicializar git
git init

# 3. Criar .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
.venv/
.env
.streamlit/secrets.toml
logs/
*.log
*.backup
EOF

# 4. Adicionar arquivos
git add -A

# 5. Primeiro commit
git commit -m "Initial commit: Dashboard Streamlit

- Configuração inicial do projeto
- Views principais implementadas
- Sistema de métricas funcionando

Co-Authored-By: Claude <noreply@anthropic.com>"

# 6. Criar repo no GitHub (para usuário leechardes)
gh repo create dashboard --public --source=. --remote=origin --push

# 7. Verificar que foi criado
echo "Repositório criado em: https://github.com/leechardes/dashboard"

# 8. Fazer mudanças e commit
# ... editar arquivos ...
git add -A
git commit -m "Adiciona nova funcionalidade X"
git push

# 9. Criar branch para nova feature
git checkout -b feature/material-icons
# ... fazer mudanças ...
git add -A
git commit -m "Substitui emojis por Material Icons"
git push -u origin feature/material-icons

# 10. Criar Pull Request
gh pr create --title "Substitui emojis por Material Icons" \
  --body "Implementa design mais profissional usando Material Icons"
```

## Configurações Úteis

### Configurar informações do usuário
```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@example.com"
```

### Aliases úteis
```bash
# Criar aliases para comandos frequentes
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.cm commit
git config --global alias.last 'log -1 HEAD'
git config --global alias.unstage 'reset HEAD --'
```

### Ver configurações
```bash
git config --list
```

## Troubleshooting

### Problema: "fatal: not a git repository"
```bash
# Solução: Inicializar git
git init
```

### Problema: "error: failed to push some refs"
```bash
# Solução: Fazer pull primeiro
git pull --rebase origin main
git push
```

### Problema: Conflitos de merge
```bash
# Ver arquivos com conflito
git status

# Editar arquivos para resolver conflitos
# Procurar por <<<<<<< HEAD

# Após resolver
git add arquivo-resolvido.py
git commit -m "Resolve conflitos de merge"
```

### Problema: Commit na branch errada
```bash
# Mover último commit para outra branch
git checkout branch-correta
git cherry-pick [hash-do-commit]
git checkout branch-errada
git reset --hard HEAD~1
```

## Dicas Importantes

1. **SEMPRE** verifique o status antes de commitar
   ```bash
   git status
   git diff
   ```

2. **NUNCA** commite senhas ou tokens
   - Use .gitignore
   - Use variáveis de ambiente
   - Use gh secret set para GitHub Actions

3. **Commits pequenos e frequentes**
   - Mais fácil de revisar
   - Mais fácil de reverter
   - Melhor histórico

4. **Mensagens de commit claras**
   - Use presente do indicativo
   - Seja específico
   - Mencione issue se houver: "Fix #123"

5. **Branches para features**
   - main/master sempre estável
   - Uma branch por feature
   - Delete após merge

## Comandos para Contexto no Chat

Quando pedir ajuda ao Claude Code, forneça contexto:

```bash
# Mostrar status atual
git status

# Mostrar últimos commits
git log --oneline -5

# Mostrar remotes
git remote -v

# Mostrar branch atual
git branch --show-current

# Verificar autenticação GitHub
gh auth status
```

## Template para Pedir Ajuda

```
Preciso ajuda com Git/GitHub.

Contexto:
- Diretório: /srv/projects/shared/dashboard
- Branch atual: main
- Status: [colar saída de git status]
- Objetivo: [descrever o que quer fazer]

Problema:
[Descrever o problema ou o que precisa fazer]
```

## Resumo Rápido

```bash
# Workflow básico diário
git pull                    # Atualizar local
# ... fazer mudanças ...
git add -A                  # Adicionar mudanças
git commit -m "mensagem"    # Commitar
git push                    # Enviar ao GitHub

# Criar novo projeto no GitHub
gh repo create nome --public --source=. --push

# Criar PR
gh pr create --title "Título" --body "Descrição"
```

---

**Nota**: Este documento foi criado para ser usado como referência rápida ao trabalhar com Claude Code ou qualquer assistente de IA para operações Git/GitHub.