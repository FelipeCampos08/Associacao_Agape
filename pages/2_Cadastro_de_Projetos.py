import streamlit as st
import datetime
from database import SessionLocal, Projeto, Turma

st.set_page_config(page_title="Cadastro de Projetos", page_icon="⚽")
st.title("Cadastro de Projetos")
st.write("Preencha as informações do novo projeto social e defina as turmas.")

# --- 1. DADOS DO PROJETO ---
st.header("1. Dados do Projeto")
nome_projeto = st.text_input("Nome do Projeto *", placeholder="Ex: Escolinha de Futebol")
descricao = st.text_area("Descrição do Projeto", placeholder="Breve resumo sobre as atividades...")
local = st.text_input("Local de Realização *", placeholder="Ex: Quadra da Comunidade")

st.markdown("---")

# --- 2. CRIAÇÃO DINÂMICA DE TURMAS ---
st.header("2. Turmas e Vagas")
num_turmas = st.number_input("Número de Turmas *", min_value=1, step=1, value=1)

turmas_dados = []

# Este loop cria os campos dinamicamente baseados no número de turmas escolhido
for i in range(int(num_turmas)):
    st.subheader(f"Configuração da Turma {i+1}")
    
    # Usando colunas para deixar o layout mais bonito
    col1, col2 = st.columns(2)
    
    with col1:
        # A chave 'key' é essencial aqui para o Streamlit não confundir os campos de turmas diferentes
        horario = st.text_input(f"Horário da Turma {i+1} *", placeholder="Ex: Terças e Quintas, 14h às 16h", key=f"horario_{i}")
        nome_turma = st.text_input(f"Nome da Turma {i+1} (Opcional)", value=f"Turma {i+1}", key=f"nome_turma_{i}")
        
    with col2:
        vagas = st.number_input(f"Número de Vagas da Turma {i+1} *", min_value=1, step=1, value=15, key=f"vagas_{i}")
    
    # Guardamos os dados de cada turma em uma lista para salvar no banco depois
    turmas_dados.append({
        "nome_turma": nome_turma,
        "horario": horario,
        "vagas_totais": vagas
    })

st.markdown("---")

# --- 3. DADOS DO PROFESSOR/VOLUNTÁRIO ---
st.header("3. Dados do Professor Responsável")
nome_prof = st.text_input("Nome Completo *")

col3, col4 = st.columns(2)
with col3:
    data_nasc_prof = st.date_input("Data de Nascimento *", min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today())
with col4:
    # Calculando a idade automaticamente
    hoje = datetime.date.today()
    idade = hoje.year - data_nasc_prof.year - ((hoje.month, hoje.day) < (data_nasc_prof.month, data_nasc_prof.day))
    st.info(f"Idade calculada: **{idade} anos**")

rg_prof = st.text_input("RG")
cpf_prof = st.text_input("CPF *")

remunerado = st.radio("O professor é remunerado? *", ["Não", "Sim"])
valor_remuneracao = 0.0
if remunerado == "Sim":
    valor_remuneracao = st.number_input("Valor da Remuneração (R$)", min_value=0.0, step=50.0)

st.markdown("---")

# --- 4. VALIDAÇÃO E SALVAMENTO ---
if st.button("Salvar Projeto", type="primary"):
    
    # Validação básica de campos obrigatórios vazios
    campos_vazios = not nome_projeto.strip() or not local.strip() or not nome_prof.strip() or not cpf_prof.strip()
    horarios_vazios = any(not t["horario"].strip() for t in turmas_dados)
    
    if campos_vazios or horarios_vazios:
        st.error("⚠️ Por favor, preencha todos os campos obrigatórios marcados com asterisco (*).")
    else:
        db = SessionLocal()
        
        # 1. Verifica se o projeto já existe
        projeto_existente = db.query(Projeto).filter(Projeto.nome == nome_projeto.strip()).first()
        
        if projeto_existente:
            st.warning(f"❌ O projeto '{nome_projeto}' já está cadastrado no sistema.")
        else:
            try:
                # 2. Cria o Projeto
                novo_projeto = Projeto(
                    nome=nome_projeto.strip(),
                    descricao=descricao.strip(),
                    local=local.strip(),
                    nome_professor=nome_prof.strip(),
                    cpf_professor=cpf_prof.strip(),
                    remuneracao_professor=valor_remuneracao
                )
                
                db.add(novo_projeto)
                db.commit() 
                db.refresh(novo_projeto) # Atualiza o objeto para pegarmos o ID gerado pelo banco
                
                # 3. Cria as Turmas vinculadas ao ID do projeto recém-criado
                for t in turmas_dados:
                    nova_turma = Turma(
                        projeto_id=novo_projeto.id,
                        nome_turma=t["nome_turma"].strip(),
                        horario=t["horario"].strip(),
                        vagas_totais=t["vagas_totais"]
                    )
                    db.add(nova_turma)
                
                db.commit()
                st.success(f"✅ Projeto '{nome_projeto}' e suas {num_turmas} turma(s) foram cadastrados com sucesso!")
                
            except Exception as e:
                db.rollback()
                st.error(f"Erro ao salvar no banco de dados: {e}")
            finally:
                db.close()