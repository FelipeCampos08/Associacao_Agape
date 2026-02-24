import streamlit as st
from datetime import date
from database import SessionLocal, Aluno, Projeto, Turma, Matricula

st.set_page_config(page_title="Matrículas", page_icon="📝")
st.title("Matrícula de Alunos")
st.write("Vincule os alunos cadastrados às turmas dos projetos sociais disponíveis.")

# Abrindo conexão com o banco
db = SessionLocal()

try:
    # --- 1. BUSCANDO DADOS INICIAIS ---
    alunos = db.query(Aluno).all()
    projetos = db.query(Projeto).all()

    # Se não houver alunos ou projetos, avisamos o usuário e paramos a tela por aqui
    if not alunos:
        st.warning("⚠️ Nenhum aluno cadastrado no sistema. Vá para a tela de Cadastro de Alunos primeiro.")
        st.stop()
        
    if not projetos:
        st.warning("⚠️ Nenhum projeto cadastrado no sistema. Vá para a tela de Cadastro de Projetos primeiro.")
        st.stop()

    st.markdown("---")

    # --- 2. SELEÇÃO DE ALUNO ---
    st.header("1. Selecione o Aluno")
    
    # Criamos um dicionário para formatar a visualização no selectbox (Nome - CPF)
    opcoes_alunos = {aluno.id: f"{aluno.nome_completo} (CPF: {aluno.cpf if aluno.cpf else 'Não informado'})" for aluno in alunos}
    
    aluno_id_selecionado = st.selectbox(
        "Buscar Aluno:", 
        options=list(opcoes_alunos.keys()), 
        format_func=lambda x: opcoes_alunos[x]
    )

    # --- 3. SELEÇÃO DE PROJETO E TURMA ---
    st.header("2. Selecione o Projeto e a Turma")
    
    opcoes_projetos = {projeto.id: projeto.nome for projeto in projetos}
    
    projeto_id_selecionado = st.selectbox(
        "Selecione o Projeto:", 
        options=list(opcoes_projetos.keys()), 
        format_func=lambda x: opcoes_projetos[x]
    )

    # Buscar as turmas apenas do projeto selecionado
    turmas_do_projeto = db.query(Turma).filter(Turma.projeto_id == projeto_id_selecionado).all()

    if not turmas_do_projeto:
        st.error("Este projeto não possui turmas cadastradas.")
    else:
        opcoes_turmas = {turma.id: f"{turma.nome_turma} - {turma.horario}" for turma in turmas_do_projeto}
        
        turma_id_selecionada = st.selectbox(
            "Selecione a Turma:", 
            options=list(opcoes_turmas.keys()), 
            format_func=lambda x: opcoes_turmas[x]
        )

        # --- 4. LÓGICA DE VAGAS ---
        turma_escolhida = db.query(Turma).filter(Turma.id == turma_id_selecionada).first()
        
        # Conta quantas matrículas já existem para esta turma específica
        quantidade_matriculados = db.query(Matricula).filter(Matricula.turma_id == turma_id_selecionada).count()
        vagas_disponiveis = turma_escolhida.vagas_totais - quantidade_matriculados

        st.markdown("### Situação da Turma")
        
        # Mostra as vagas com cores dinâmicas
        if vagas_disponiveis > 0:
            st.success(f"✅ **{vagas_disponiveis} vagas disponíveis** (Total: {turma_escolhida.vagas_totais} vagas)")
        else:
            st.error(f"❌ **Turma Lotada** (Total: {turma_escolhida.vagas_totais} vagas preenchidas)")

        st.markdown("---")

        # --- 5. EFETIVAR MATRÍCULA ---
        if st.button("Confirmar Matrícula", type="primary"):
            
            # Regra de negócio 2: Verificar se o aluno já está no projeto (em qualquer turma dele)
            ids_turmas_projeto = [t.id for t in turmas_do_projeto]
            
            ja_matriculado_no_projeto = db.query(Matricula).filter(
                Matricula.aluno_id == aluno_id_selecionado,
                Matricula.turma_id.in_(ids_turmas_projeto)
            ).first()

            if ja_matriculado_no_projeto:
                st.warning(f"⚠️ O aluno selecionado já está matriculado neste projeto!")
            
            # Regra de negócio 3: Verificar se há vagas
            elif vagas_disponiveis <= 0:
                st.error("❌ Não é possível matricular: A turma selecionada está lotada.")
                
            else:
                # Tudo certo, vamos matricular!
                try:
                    nova_matricula = Matricula(
                        aluno_id=aluno_id_selecionado,
                        turma_id=turma_id_selecionada,
                        data_matricula=date.today()
                    )
                    db.add(nova_matricula)
                    db.commit()
                    st.success("🎉 Matrícula realizada com sucesso!")
                    st.balloons() # Um efeitinho visual legal do Streamlit para comemorar!
                    
                except Exception as e:
                    db.rollback()
                    st.error(f"Ocorreu um erro ao salvar a matrícula: {e}")

finally:
    db.close() # Sempre fechamos a conexão com o banco no final