import streamlit as st
from database import SessionLocal, Aluno, Projeto, Turma, Matricula

st.set_page_config(page_title="Avançado", page_icon="⚙️", layout="wide")
st.title("⚙️ Administração Avançada")

db = SessionLocal()

try:
    # NOVO: Aba de Status do Aluno
    aba_status, aba_desmatricular, aba_alunos, aba_projetos = st.tabs(["🔄 Status de Alunos", "❌ Desmatricular", "✏️ Excluir Alunos", "🏗️ Excluir Projetos"])

    # ==========================================
    # ABA 1: STATUS DO ALUNO (Ativo/Inativo)
    # ==========================================
    with aba_status:
        st.header("Alterar Status do Aluno (Ciclo Anual)")
        st.write("Alunos inativos não aparecem na tela de matrículas, mas seu histórico é preservado para estatísticas.")
        
        alunos_todos = db.query(Aluno).all()
        if alunos_todos:
            opcoes_status = {a.id: f"{'🟢' if a.status_ativo else '🔴'} {a.nome_completo}" for a in alunos_todos}
            aluno_status_id = st.selectbox("Selecione o aluno para alterar o status:", options=list(opcoes_status.keys()), format_func=lambda x: opcoes_status[x])
            
            aluno_selecionado = db.query(Aluno).filter(Aluno.id == aluno_status_id).first()
            novo_status = st.radio("Definir como:", ["Ativo", "Inativo"], index=0 if aluno_selecionado.status_ativo else 1)
            
            if st.button("Atualizar Status"):
                aluno_selecionado.status_ativo = (novo_status == "Ativo")
                db.commit()
                st.success(f"Status do aluno atualizado para {novo_status}!")
                st.rerun()

    # ==========================================
    # ABA 2: DESMATRICULAR
    # ==========================================
    with aba_desmatricular:
        st.header("Remover Aluno de uma Turma")
        matriculas = db.query(Matricula).all()
        if matriculas:
            opcoes_mat = {}
            for m in matriculas:
                aluno = db.query(Aluno).filter(Aluno.id == m.aluno_id).first()
                turma = db.query(Turma).filter(Turma.id == m.turma_id).first()
                projeto = db.query(Projeto).filter(Projeto.id == turma.projeto_id).first()
                opcoes_mat[m.id] = f"{aluno.nome_completo} - {projeto.nome} ({turma.nome_turma} | {turma.ano_letivo})"
                
            mat_selecionada = st.selectbox("Selecione a matrícula para cancelar:", options=list(opcoes_mat.keys()), format_func=lambda x: opcoes_mat[x])
            if st.button("Cancelar Matrícula", type="primary"):
                db.query(Matricula).filter(Matricula.id == mat_selecionada).delete()
                db.commit()
                st.success("Matrícula cancelada com sucesso!")
                st.rerun()

    # ==========================================
    # ABA 3 e 4: EXCLUIR ALUNOS E PROJETOS
    # ==========================================
    with aba_alunos:
        st.warning("⚠️ Excluir apagará todo o histórico do aluno. Prefira usar a aba 'Status de Alunos' para inativá-lo.")
        if alunos_todos:
            opcoes_excluir = {a.id: a.nome_completo for a in alunos_todos}
            aluno_id = st.selectbox("Selecione o aluno para excluir:", options=list(opcoes_excluir.keys()), format_func=lambda x: opcoes_excluir[x])
            if st.button("🗑️ Excluir Aluno Definitivamente"):
                db.query(Matricula).filter(Matricula.aluno_id == aluno_id).delete()
                db.query(Aluno).filter(Aluno.id == aluno_id).delete()
                db.commit()
                st.success("Aluno excluído com sucesso.")
                st.rerun()

    with aba_projetos:
        projetos = db.query(Projeto).all()
        if projetos:
            opcoes_projetos = {p.id: p.nome for p in projetos}
            proj_id = st.selectbox("Selecione o projeto:", options=list(opcoes_projetos.keys()), format_func=lambda x: opcoes_projetos[x])
            if st.button("🗑️ Excluir Projeto e Turmas"):
                turmas = db.query(Turma).filter(Turma.projeto_id == proj_id).all()
                ids_turmas = [t.id for t in turmas]
                if ids_turmas:
                    db.query(Matricula).filter(Matricula.turma_id.in_(ids_turmas)).delete(synchronize_session=False)
                db.query(Turma).filter(Turma.projeto_id == proj_id).delete()
                db.query(Projeto).filter(Projeto.id == proj_id).delete()
                db.commit()
                st.success("Projeto e turmas excluídos.")
                st.rerun()

finally:
    db.close()