import streamlit as st
import datetime
from database import SessionLocal, Projeto, Turma

st.set_page_config(page_title="Gestão de Projetos e Turmas", page_icon="⚽", layout="wide")
st.title("Gestão de Projetos e Turmas")
st.write("Cadastre novos projetos no catálogo ou abra novas turmas para projetos já existentes (Ciclo Anual).")

db = SessionLocal()

try:
    aba_projeto, aba_turma = st.tabs(["🆕 1. Cadastrar Novo Projeto", "📅 2. Abrir Novas Turmas"])

    # ==========================================
    # ABA 1: CADASTRAR PROJETO (Catálogo)
    # ==========================================
    with aba_projeto:
        st.header("Cadastrar Novo Projeto")
        st.info("Aqui você cria a 'ideia' do projeto. As turmas, horários e professores serão definidos na próxima aba.")
        
        nome_projeto = st.text_input("Nome do Projeto *", placeholder="Ex: Escolinha de Futebol")
        descricao = st.text_area("Descrição do Projeto", placeholder="Breve resumo sobre as atividades...")
        local = st.text_input("Local de Realização *", placeholder="Ex: Quadra da Comunidade")
        
        if st.button("Salvar Projeto", type="primary"):
            if not nome_projeto.strip() or not local.strip():
                st.error("⚠️ Preencha o nome e o local do projeto.")
            else:
                projeto_existente = db.query(Projeto).filter(Projeto.nome == nome_projeto.strip()).first()
                if projeto_existente:
                    st.warning(f"❌ O projeto '{nome_projeto}' já existe no catálogo.")
                else:
                    novo_projeto = Projeto(nome=nome_projeto.strip(), descricao=descricao.strip(), local=local.strip())
                    db.add(novo_projeto)
                    db.commit()
                    st.success(f"✅ Projeto '{nome_projeto}' cadastrado com sucesso! Agora vá na aba ao lado para abrir as turmas.")
                    st.rerun() # Atualiza a tela para o projeto aparecer na outra aba

    # ==========================================
    # ABA 2: ABRIR TURMAS E PROFESSORES
    # ==========================================
    with aba_turma:
        st.header("Abrir Turmas e Definir Professores")
        
        projetos = db.query(Projeto).all()
        if not projetos:
            st.warning("Nenhum projeto cadastrado. Crie um projeto na aba ao lado primeiro.")
        else:
            opcoes_projetos = {p.id: p.nome for p in projetos}
            projeto_selecionado_id = st.selectbox("Selecione o Projeto:", options=list(opcoes_projetos.keys()), format_func=lambda x: opcoes_projetos[x])
            
            st.markdown("---")
            num_turmas = st.number_input("Quantas turmas deseja abrir para este projeto agora?", min_value=1, step=1, value=1)
            ano_atual = datetime.date.today().year
            
            turmas_dados = []
            
            for i in range(int(num_turmas)):
                st.subheader(f"Configuração da Turma {i+1}")
                
                # Linha 1: Dados da Turma
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    nome_turma = st.text_input(f"Nome da Turma", value=f"Turma {i+1}", key=f"nome_turma_{i}")
                with col2:
                    horario = st.text_input(f"Horário *", placeholder="Ex: 14h às 16h", key=f"horario_{i}")
                with col3:
                    vagas = st.number_input(f"Vagas *", min_value=1, step=1, value=15, key=f"vagas_{i}")
                with col4:
                    ano_letivo = st.number_input(f"Ano Letivo *", min_value=2024, max_value=2100, value=ano_atual, step=1, key=f"ano_{i}")
                    
                # Linha 2: Dados do Professor daquela Turma
                col_p1, col_p2, col_p3, col_p4 = st.columns(4)
                with col_p1:
                    nome_prof = st.text_input(f"Professor(a) *", key=f"prof_{i}", placeholder="Nome do responsável")
                with col_p2:
                    cpf_prof = st.text_input(f"CPF do Prof.", key=f"cpf_{i}")
                with col_p3:
                    remunerado = st.selectbox(f"Remunerado?", ["Não", "Sim"], key=f"remun_{i}")
                with col_p4:
                    valor_remuneracao = st.number_input(f"Valor (R$)", min_value=0.0, step=50.0, key=f"valor_{i}") if remunerado == "Sim" else 0.0
                
                st.divider()
                
                turmas_dados.append({
                    "nome_turma": nome_turma,
                    "horario": horario,
                    "vagas_totais": vagas,
                    "ano_letivo": ano_letivo,
                    "nome_professor": nome_prof,
                    "cpf_professor": cpf_prof,
                    "remuneracao_professor": valor_remuneracao
                })

            if st.button("Salvar Turmas", type="primary", key="btn_salvar_turmas"):
                # Validação
                erros = []
                for idx, t in enumerate(turmas_dados):
                    if not t["horario"].strip() or not t["nome_professor"].strip():
                        erros.append(f"Turma {idx+1}")
                
                if erros:
                    st.error(f"⚠️ Preencha o Horário e o Nome do Professor para as turmas: {', '.join(erros)}")
                else:
                    try:
                        for t in turmas_dados:
                            nova_turma = Turma(
                                projeto_id=projeto_selecionado_id,
                                nome_turma=t["nome_turma"].strip(),
                                horario=t["horario"].strip(),
                                vagas_totais=t["vagas_totais"],
                                ano_letivo=t["ano_letivo"],
                                nome_professor=t["nome_professor"].strip(),
                                cpf_professor=t["cpf_professor"].strip(),
                                remuneracao_professor=t["remuneracao_professor"]
                            )
                            db.add(nova_turma)
                        
                        db.commit()
                        st.success(f"✅ {num_turmas} turma(s) abertas com sucesso para o projeto!")
                    except Exception as e:
                        db.rollback()
                        st.error(f"Erro ao salvar: {e}")
finally:
    db.close()