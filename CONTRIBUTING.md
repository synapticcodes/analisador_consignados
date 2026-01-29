# 🤝 Guia de Contribuição

Obrigado por considerar contribuir com a Calculadora de Consignados! Este documento fornece diretrizes para contribuir com o projeto.

## 📋 Código de Conduta

- Seja respeitoso e inclusivo
- Aceite críticas construtivas
- Foque no que é melhor para a comunidade
- Mostre empatia com outros membros da comunidade

## 🚀 Como Contribuir

### 1. Setup do Ambiente

```bash
# Fork o repositório e clone seu fork
git clone https://github.com/seu-usuario/calculadora-consignados.git
cd calculadora-consignados

# Configure o repositório upstream
git remote add upstream https://github.com/original-org/calculadora-consignados.git

# Crie o arquivo .env
cp .env.example .env
# Edite .env com suas credenciais

# Suba a infraestrutura
docker-compose up -d
```

### 2. Criando uma Branch

```bash
# Sempre crie uma branch a partir da main atualizada
git checkout main
git pull upstream main
git checkout -b feature/minha-feature
```

**Convenção de nomes de branches:**
- `feature/` - Nova funcionalidade
- `fix/` - Correção de bug
- `docs/` - Mudanças em documentação
- `refactor/` - Refatoração de código
- `test/` - Adição ou correção de testes
- `chore/` - Tarefas de manutenção

### 3. Fazendo Mudanças

#### Code Style

**Backend (Python):**
- Use [Black](https://black.readthedocs.io/) para formatação (linha 100 chars)
- Use [Ruff](https://docs.astral.sh/ruff/) para linting
- Siga PEP 8 e type hints
- Docstrings no formato Google Style

```bash
# Formatar código
make format-backend

# Verificar linting
make lint-backend
```

**Frontend (TypeScript/React):**
- Use [Prettier](https://prettier.io/) para formatação
- Use [ESLint](https://eslint.org/) para linting
- Siga as regras do `eslint-config-next`

```bash
# Formatar código
make format-frontend

# Verificar linting
make lint-frontend
```

#### Testes

**Todo código novo deve incluir testes!**

```bash
# Backend
make test-backend

# Frontend
make test-frontend

# Todos os testes
make test
```

**Cobertura mínima:** 80% para backend

#### Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>[escopo opcional]: <descrição>

[corpo opcional]

[rodapé opcional]
```

**Tipos:**
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação (não afeta código)
- `refactor`: Refatoração
- `test`: Testes
- `chore`: Tarefas de manutenção

**Exemplos:**
```bash
git commit -m "feat(extractor): adicionar suporte para novo layout INSS"
git commit -m "fix(evidence-gate): corrigir validação de valores negativos"
git commit -m "docs: atualizar README com instruções de deploy"
```

### 4. Submetendo Pull Request

```bash
# Push sua branch
git push origin feature/minha-feature
```

No GitHub:
1. Abra um Pull Request para `main`
2. Preencha o template de PR
3. Aguarde review
4. Faça ajustes se necessário

**Template de PR:**
```markdown
## Descrição
Breve descrição da mudança.

## Tipo de Mudança
- [ ] Bug fix
- [ ] Nova funcionalidade
- [ ] Breaking change
- [ ] Documentação

## Como Testar
Passos para testar as mudanças.

## Checklist
- [ ] Código segue o style guide
- [ ] Adicionei testes que provam que a correção/feature funciona
- [ ] Testes passam localmente
- [ ] Atualizei a documentação
```

## 🐛 Reportando Bugs

Use o [GitHub Issues](https://github.com/seu-org/calculadora-consignados/issues) e forneça:

1. **Descrição clara** do problema
2. **Passos para reproduzir**
3. **Comportamento esperado** vs **comportamento atual**
4. **Screenshots** (se aplicável)
5. **Ambiente**:
   - OS: [e.g. macOS 14.0]
   - Node: [e.g. 20.9.0]
   - Python: [e.g. 3.11.0]
   - Docker: [e.g. 24.0.0]

## 💡 Sugerindo Features

Use [GitHub Issues](https://github.com/seu-org/calculadora-consignados/issues) com:

1. **Descrição clara** da feature
2. **Casos de uso** (por que isso é útil?)
3. **Exemplos** de como deve funcionar
4. **Alternativas consideradas**

## 📖 Melhorando Documentação

Documentação é crucial! Contribuições de documentação são muito bem-vindas:

- Correção de typos
- Melhorias de clareza
- Novos tutoriais
- Traduções

## 🔍 Processo de Review

1. **Automated checks**: CI/CD roda testes e linting automaticamente
2. **Code review**: Pelo menos 1 aprovação é necessária
3. **Discussion**: Revisores podem pedir mudanças
4. **Merge**: Após aprovação, mantainer fará o merge

## ❓ Dúvidas

- **Issues**: [GitHub Issues](https://github.com/seu-org/calculadora-consignados/issues)
- **Discussions**: [GitHub Discussions](https://github.com/seu-org/calculadora-consignados/discussions)
- **Email**: suporte@seudominio.com

---

## 🙏 Obrigado!

Suas contribuições tornam este projeto melhor para todos. Obrigado por dedicar seu tempo! 🎉
