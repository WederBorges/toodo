# To-be List

Aplicação web de gerenciamento de tarefas com autenticação de usuários, construída com Flask. O usuário cria uma conta, adiciona tarefas com nome e descrição, acompanha o progresso pelo dashboard e recebe notificações por e-mail sobre tarefas pendentes.

> Projeto de portfólio em desenvolvimento ativo — algumas funcionalidades estão sendo expandidas.

---

##  Stack

| Camada | Tecnologia |
|---|---|
| Back-end | Python 3.12+ / Flask |
| ORM | SQLAlchemy (mapped models) |
| Banco de dados | PostgreSQL (produção) / SQLite (fallback local) |
| Migrações | Alembic |
| Autenticação | Flask-Login |
| Segurança | Flask-WTF (CSRF Protection) |
| Agendamento | APScheduler |
| Notificações | Resend (e-mail transacional) |
| Templating | Jinja2 |
| Servidor de produção | Gunicorn |
| Containerização | Docker / Docker Compose |
| Deploy | Railway |
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
├── run.py                  # Ponto de entrada (web)
├── scheduler.py            # Job agendado de notificações por e-mail
├── services.py             # Conexão de banco compartilhada (scheduler)
├── Dockerfile              # Imagem usada por web + scheduler
├── docker-compose.yml      # Orquestração local dos dois serviços
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
SECRET_KEY=sua_chave_secreta_aqui
DATABASE_URL=postgresql://usuario:senha@host:porta/banco
RESEND_API_KEY=sua_api_key_resend
RESEND_FROM=notificacoes@seudominio.com
```

> Sem `DATABASE_URL`, a aplicação cai automaticamente para SQLite local — útil para rodar sem depender de um Postgres configurado.

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

##  Por que esse projeto

O Toodo nasceu como projeto de portfólio para aprender desenvolvimento back-end na prática, não seguindo tutorial, construindo, travando e debugando um problema real até resolver (Com auxílio de IA mas sem nenhuma linha de código de lógica copiado dela). A ideia desde o início foi simples (um gerenciador de tarefas), de propósito: o objetivo nunca foi a complexidade da regra de negócio, e sim usar uma base simples para estudar a fundo cada camada por trás de uma aplicação web em produção — autenticação, modelagem de dados, migrações de schema, segurança, deploy e infraestrutura.

##  O que foi aprendido construindo

Alguns dos aprendizados mais relevantes ao longo do desenvolvimento:

**Segurança — CSRF Protection**
Implementação de proteção CSRF via `Flask-WTF` (`CSRFProtect`), com decisão consciente de não migrar os formulários para classes `FlaskForm` — optando por manter o escopo da tarefa isolado. O ponto mais interessante não foi a implementação em si, mas a forma de propagação: em vez de injetar o token manualmente em cada template, a solução foi centralizada em um único script no template base (`bootstrap.html`), fora de qualquer `{% block %}`, que injeta o token automaticamente em todo formulário `POST` da aplicação via `document.querySelectorAll('form[method="post" i]')` — inclusive em formulários vindos de partials (`{% include %}`), já que o Jinja resolve includes no servidor antes de gerar o HTML final. A proteção foi validada manualmente via DevTools, alterando o token injetado e confirmando o retorno de `400 Bad Request` antes da requisição chegar à view function.

**Migração de banco de dados — SQLite → PostgreSQL**
Migração completa do banco local (SQLite) para PostgreSQL gerenciado (Railway), incluindo:
- Driver `psycopg` (v3) integrado ao SQLAlchemy;
- Cadeia de fallback de configuração (`DATABASE_URL` → `DATABASE_URL_PUBLIC` → SQLite local), permitindo rodar o mesmo código localmente ou em produção sem alterações;
- Substituição de `DATETIME` (específico do SQLite) por `TIMESTAMP`, compatível com Postgres;
- Remoção do `Base.metadata.create_all()` em favor do Alembic como única fonte de verdade do schema — uma decisão de arquitetura que evita divergência entre o código dos modelos e o estado real do banco;
- Diagnóstico e correção manual de uma migration corrompida, gerada por `--autogenerate` a partir de um estado transitório do banco local.

**Deploy e infraestrutura — Docker**
Resolução de um bug sutil no `Dockerfile`: a diferença entre **exec form** e **shell form** do `CMD`. A forma JSON array (`CMD ["gunicorn", ...]`) não passa por uma shell, então variáveis como `$PORT` (injetada dinamicamente pela Railway) nunca eram expandidas — o Gunicorn sempre subia na porta padrão. A correção usa a forma array chamando `sh -c` explicitamente (`CMD ["sh", "-c", "exec gunicorn run:app --bind 0.0.0.0:${PORT:-5000}"]`), unindo a sintaxe recomendada pelo Docker com a expansão de variáveis de ambiente necessária.

**Modelagem de dados e SQLAlchemy**
- Diferença entre `== None` (não funciona como esperado em contexto de ORM) e `.isnot(None)` (forma correta de comparar nulidade em uma query SQLAlchemy);
- `ON DELETE CASCADE` no nível do banco (via `ondelete="CASCADE"` no `ForeignKey`) combinado com `cascade="all, delete-orphan"` no relacionamento do ORM, garantindo integridade referencial real ao excluir uma conta — algo que o SQLite exigiria configuração adicional (`PRAGMA foreign_keys`) por conexão para funcionar;
- Diferença entre `server_default` (valor calculado pelo banco, útil quando o valor não é sempre passado explicitamente) e valor calculado em Python no momento do insert.

**Tratamento de dados de formulário**
Identificação de uma sutileza fácil de passar batido: `request.form.get("campo")` retorna string vazia (`""`) quando um campo existe no formulário mas foi deixado em branco — nunca `None`. Sem tratar esse caso (`if not email: email = None`), o banco armazenaria strings vazias em vez de `NULL`, o que quebraria a `UniqueConstraint` de e-mail na segunda conta criada sem e-mail (duas strings vazias colidem; dois valores `NULL` não).

**Infraestrutura de notificações**
Substituição do envio de e-mail via Gmail SMTP (sujeito a limites de envio e instabilidade em conta pessoal) por **Resend**, um serviço dedicado para envio transacional — decisão tomada visando confiabilidade em produção.

##  Roadmap futuro

- [ ] Cálculo de progresso por dia (tarefas concluídas hoje vs. pendentes hoje), e não apenas sobre o total histórico
- [ ] Recuperação de senha ("esqueci minha senha")
- [ ] Separação entre banco de produção e banco de desenvolvimento/teste no Railway
- [ ] Suíte de testes automatizados com `pytest`
- [ ] Refatoração para um padrão orientado a objetos mais explícito na camada de regras de negócio (classe dedicada para operações de tarefas)
- [ ] Página `/sobre` explicando o projeto, stack e aprendizados (no próprio site)
- [ ] Auditoria geral da pasta de migrations para garantir consistência total do histórico

---

##  Autor

**Weder Borges** — [GitHub](https://github.com/WederBorges)
