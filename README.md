# Sistema de Gestão - Associação Ágape v1.0

Este é o repositório oficial do sistema de gestão desenvolvido sob medida para a **Associação Ágape (Missões Urbanas)**. O objetivo principal desta aplicação é digitalizar, centralizar e organizar os dados de alunos, famílias em situação de vulnerabilidade, projetos sociais e matrículas, abandonando o uso de papéis e planilhas soltas.

## 🚀 Módulos e Funcionalidades

O sistema foi arquitetado para ser simples e intuitivo para a equipe administrativa da ONG, contendo as seguintes funcionalidades:

* **🔐 Autenticação:** Sistema de login seguro com controle de sessão e senhas criptografadas (hashing). Separação de perfis (Administrador e Usuário Comum).
* **📝 Cadastro de Alunos:** Formulário dinâmico com campos separados em colunas (Dados Pessoais, Responsáveis, Endereço, Vulnerabilidades e Saúde), gerados a partir de um arquivo JSON mapeado.
* **⚽ Projetos e Turmas:** Gerenciamento das iniciativas da ONG (ex: Futebol, Ballet) e controle de professores, horários e locais.
* **✅ Matrículas:** Alocação de alunos nas turmas disponíveis.
* **🔍 Pesquisa Geral:** Painel de filtros rápidos para encontrar informações cadastrais e listas de chamada ativas.
* **⚙️ Avançado:** Área restrita (para Administradores) permitindo edição de fichas cadastrais, desmatrículas, exclusão de registros e gerenciamento de acessos da equipe.
* **🖨️ Relatórios em PDF:** Geração nativa de documentos formatados contendo estatísticas do ano letivo, lista de chamada por professor e fichas resumidas para impressão.
* **📊 Dashboard:** Painel quantitativo com indicadores e gráficos de barras/pizza para análise visual da ocupação dos projetos.

## 🛠️ Stack Tecnológico (Arquitetura)

* **Frontend / Framework:** [Streamlit](https://streamlit.io/) (Interface responsiva, UI/UX em Python).
* **Backend:** Python 3.10+.
* **Banco de Dados:** PostgreSQL hospedado na nuvem ([Supabase](https://supabase.com/)).
* **ORM:** SQLAlchemy (Mapeamento Objeto-Relacional para segurança contra SQL Injection).
* **Geração de PDF:** Biblioteca `fpdf2`.
* **Criptografia:** Biblioteca `bcrypt` para proteção de senhas.
* **Deploy:** Streamlit Community Cloud (CI/CD conectado à branch main do GitHub).

## 💻 Como rodar o projeto localmente (Para Desenvolvedores)

Se você precisa testar novas funcionalidades sem afetar o banco de dados oficial da nuvem, siga este passo a passo:

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/FelipeCampos08/Associacao_Agape.git
   cd Associacao_Agape
   ```

2. **Crie e ative um Ambiente Virtual:**
    ```bash
    python -m venv venv
    ```

    ```bash
    # No Windows:
    venv\Scripts\activate
    ```

    ```bash
    # No Mac/Linux:
    source venv/bin/activate
    ```

3. **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Configure os Segredos (Secrets):**
Crie uma pasta chamada .streamlit na raiz do projeto e um arquivo secrets.toml dentro dela:
    ```bash
    # Exemplo para uso de banco SQLite local (Para testes isolados)
    DATABASE_URL = "sqlite:///agape_teste.db"
    ```

5. **Inicie o servidor:**
    ```bash    
    streamlit run Home.py
    ```

    O sistema criará o banco de dados e um usuário administrador padrão (admin@agape.com / 123) no primeiro acesso.
    
🔒 Considerações de Segurança
As senhas de banco de dados (DATABASE_URL) jamais devem ser commitadas. Elas estão protegidas no arquivo .gitignore.

Na nuvem, o acesso é feito utilizando o Connection Pooler do Supabase (IPv4) configurado diretamente nas opções avançadas (Secrets) do painel do Streamlit Cloud.

Toda a lógica de deleção de dados (CASCADE) é tratada via aplicação (Backend) para preservar a integridade referencial e não deixar matrículas órfãs.    