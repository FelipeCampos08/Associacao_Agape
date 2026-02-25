import streamlit as st
from datetime import date
from database import SessionLocal, Aluno, Projeto, Turma, Matricula

st.set_page_config(page_title="Matrículas", page_icon="📝")
st.title("Matrícula de Alunos")

db = SessionLocal()

try:
    # NOVO: Filtra apenas alunos com status_ativo == True
    alunos_ativos = db.query(Aluno).filter(Aluno.status_ativo == True).all()
    projetos = db.query(Projeto).all()

    if not alunos_ativos:
        st.warning("⚠️ Nenhum aluno ATIVO cadastrado no sistema.")
        st.stop()
    if not projetos:
        st.warning("⚠️ Nenhum projeto cadastrado no sistema.")
        st.stop()

    st.header("1. Selecione o Aluno (Somente Ativos)")
    opcoes_alunos = {aluno.id: f"{aluno.nome_completo} (CPF: {aluno.cpf if aluno.cpf else 'N/A'})" for aluno in alunos_ativos}
    aluno_id_selecionado = st.selectbox("Buscar Aluno:", options=list(opcoes_alunos.keys()), format_func=lambda x: opcoes_alunos[x])

    st.header("2. Selecione o Projeto e a Turma")
    opcoes_projetos = {projeto.id: projeto.nome for projeto in projetos}
    projeto_id_selecionado = st.selectbox("Selecione o Projeto:", options=list(opcoes_projetos.keys()), format_func=lambda x: opcoes_projetos[x])

    # NOVO: Filtro visual de ano letivo
    ano_filtro = st.number_input("Filtrar turmas pelo Ano Letivo:", min_value=2024, max_value=2100, value=date.today().year)
    turmas_do_projeto = db.query(Turma).filter(Turma.projeto_id == projeto_id_selecionado, Turma.ano_letivo == ano_filtro).all()

    if not turmas_do_projeto:
        st.error(f"Este projeto não possui turmas cadastradas para o ano de {ano_filtro}.")
    else:
        opcoes_turmas = {turma.id: f"{turma.nome_turma} - {turma.horario} ({turma.ano_letivo})" for turma in turmas_do_projeto}
        turma_id_selecionada = st.selectbox("Selecione a Turma:", options=list(opcoes_turmas.keys()), format_func=lambda x: opcoes_turmas[x])

        turma_escolhida = db.query(Turma).filter(Turma.id == turma_id_selecionada).first()
        quantidade_matriculados = db.query(Matricula).filter(Matricula.turma_id == turma_id_selecionada).count()
        vagas_disponiveis = turma_escolhida.vagas_totais - quantidade_matriculados

        st.markdown("### Situação da Turma")
        if vagas_disponiveis > 0:
            st.success(f"✅ **{vagas_disponiveis} vagas disponíveis**")
        else:
            st.error(f"❌ **Turma Lotada**")

        if st.button("Confirmar Matrícula", type="primary"):
            ids_turmas_projeto = [t.id for t in turmas_do_projeto]
            ja_matriculado_no_projeto = db.query(Matricula).filter(Matricula.aluno_id == aluno_id_selecionado, Matricula.turma_id.in_(ids_turmas_projeto)).first()

            if ja_matriculado_no_projeto:
                st.warning(f"⚠️ O aluno já está matriculado neste projeto para o ano de {ano_filtro}!")
            elif vagas_disponiveis <= 0:
                st.error("❌ A turma está lotada.")
            else:
                try:
                    nova_matricula = Matricula(aluno_id=aluno_id_selecionado, turma_id=turma_id_selecionada, data_matricula=date.today())
                    db.add(nova_matricula)
                    db.commit()
                    st.success("🎉 Matrícula realizada com sucesso!")
                    st.balloons()
                except Exception as e:
                    db.rollback()
                    st.error(f"Erro ao salvar: {e}")
finally:
    db.close()