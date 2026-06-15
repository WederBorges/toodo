# 📝 Toodo

Aplicação web de gerenciamento de tarefas com autenticação de usuários, construída com Flask. O usuário cria uma conta, adiciona tarefas com nome e descrição, acompanha o progresso pelo dashboard e recebe notificações por e-mail sobre tarefas pendentes.

> Projeto de portfólio em desenvolvimento ativo — algumas funcionalidades estão sendo expandidas.

---

##  Stack

| Camada | Tecnologia |
|---|---|
| Back-end | Python 3.12+ / Flask |
| ORM | SQLAlchemy (mapped models) |
| Banco de dados | SQLite |
| Migrações | Alembic |
| Autenticação | Flask-Login |
| Agendamento | APScheduler |
| Notificações | smtplib (Gmail SMTP) |
| Templating | Jinja2 |
| Gerenciador de dependências | Poetry |
| Variáveis de ambiente | python-dotenv |

---

##  Banco de Dados

### Tabelas

**`user_account`**
| Coluna | Tipo | Descrição |
|---|---|---|
| id | Integer (PK) | Identificador único |
| user | String(30) | Nome de usuário |
| password | VARCHAR(100) | Senha hasheada |
| email | String | E-mail do usuário (opcional) |
| receber_mensagem | Boolean | Opt-in para notificações por e-mail |

**`tarefas`**
| Coluna | Tipo | Descrição |
|---|---|---|
| id | Integer (PK) | Identificador único |
| tarefa | String(300) | Nome da tarefa |
| descricao_obj | VARCHAR(300) | Descrição da tarefa |
| status | String(30) | `pendente` ou `concluido` |
| created_at | DateTime | Data de criação |
| responsavel_id | Integer (FK) | Referência ao usuário dono da tarefa |

---

##  Funcionalidades

- **Autenticação** — cadastro e login com nome de usuário e senha
- **Tarefas** — criação, edição, conclusão e exclusão de tarefas
- **Dashboard** — cards com total de tarefas, pendentes e barra de progresso de conclusão
- **Filtros** — visualização por todas, pendentes ou concluídas
- **Perfil** — edição de nome, e-mail e senha
- **Notificações por e-mail** — envio diário às 9h30 com lista de tarefas pendentes para usuários com e-mail cadastrado

---

##  Estrutura do Projeto

```
Toodolist/
├── app.py                  # Factory da aplicação Flask
├── run.py                  # Ponto de entrada
├── database/
│   └── conf.py             # Configuração do banco e Base declarativa
├── models/
│   └── models.py           # Modelos User e Tarefas
├── routes/
│   ├── auth.py             # Rotas de autenticação
│   ├── tarefas.py          # Rotas de tarefas
│   └── user.py             # Rotas de perfil
├── templates/              # Templates Jinja2
├── static/                 # CSS e arquivos estáticos
└── migrations/             # Migrações Alembic
```

---

##  Como rodar localmente

### Pré-requisitos

- Python 3.12+
- Poetry instalado

### Instalação

```bash
# Clone o repositório
git clone https://github.com/WederBorges/toodo.git
cd toodo/Toodolist

# Instale as dependências
poetry install

# Configure as variáveis de ambiente
cp .env.example .env
# edite o .env com suas credenciais
```

### Variáveis de ambiente

Crie um arquivo `.env` na raiz com:

```env
SECRET_KEY_=sua_chave_secreta_aqui
EMAIL_SENDER=seu_email@gmail.com
EMAIL_PASSWORD=sua_app_password_gmail
```

### Migrações

```bash
poetry run alembic upgrade head
```

### Executando

```bash
poetry run python run.py
```

Acesse em `http://127.0.0.1:5000`

---

##  Melhorias previstas

- [ ] Filtro de progresso por dia (tarefas concluídas no dia vs. pendentes no dia)
- [ ] Melhorias no sistema de notificações por e-mail
- [ ] Adição de prazo (deadline) nas tarefas

---

##  Autor

**Weder Borges** — [GitHub](https://github.com/WederBorges)
