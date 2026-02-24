import streamlit as st
from database import SessionLocal, Aluno, Projeto, Turma, Matricula

st.set_page_config(page_title="Avançado", page_icon="⚙️", layout="wide")
st.title("⚙️ Administração Avançada")
st.write("Área restrita para edição, exclusão e gestão de matrículas.")

db = SessionLocal()

try:
    aba_desmatricular, aba_alunos, aba_projetos = st.tabs(["❌ Desmatricular Aluno", "✏️ Gerenciar Alunos", "🏗️ Gerenciar Projetos"])

    # ==========================================
    # ABA 1: DESMATRICULAR
    # ==========================================
    with aba_desmatricular:
        st.header("Remover Aluno de uma Turma")
        matriculas = db.query(Matricula).all()
        
        if not matriculas:
            st.info("Não há matrículas ativas no sistema.")
        else:
            opcoes_mat = {}
            for m in matriculas:
                aluno = db.query(Aluno).filter(Aluno.id == m.aluno_id).first()
                turma = db.query(Turma).filter(Turma.id == m.turma_id).first()
                projeto = db.query(Projeto).filter(Projeto.id == turma.projeto_id).first()
                opcoes_mat[m.id] = f"{aluno.nome_completo} - {projeto.nome} ({turma.nome_turma})"
                
            mat_selecionada = st.selectbox("Selecione a matrícula para cancelar:", options=list(opcoes_mat.keys()), format_func=lambda x: opcoes_mat[x])
            
            if st.button("Cancelar Matrícula", type="primary"):
                mat_para_deletar = db.query(Matricula).filter(Matricula.id == mat_selecionada).first()
                db.delete(mat_para_deletar)
                db.commit()
                st.success("Matrícula cancelada com sucesso! A vaga voltou a ficar disponível.")
                st.rerun() # Atualiza a tela

    # ==========================================
    # ABA 2: GERENCIAR ALUNOS (Excluir)
    # ==========================================
    with aba_alunos:
        st.header("Excluir Aluno do Sistema")
        st.warning("⚠️ Atenção: Excluir um aluno também apagará todo o seu histórico e matrículas associadas.")
        
        alunos = db.query(Aluno).all()
        if alunos:
            opcoes_alunos = {a.id: a.nome_completo for a in alunos}
            aluno_id = st.selectbox("Selecione o aluno:", options=list(opcoes_alunos.keys()), format_func=lambda x: opcoes_alunos[x])
            
            if st.button("🗑️ Excluir Aluno Definitivamente"):
                # Primeiro deleta as matriculas do aluno para não dar erro no banco
                db.query(Matricula).filter(Matricula.aluno_id == aluno_id).delete()
                # Depois deleta o aluno
                aluno_para_deletar = db.query(Aluno).filter(Aluno.id == aluno_id).first()
                db.delete(aluno_para_deletar)
                db.commit()
                st.success("Aluno e matrículas excluídos com sucesso.")
                st.rerun()

    # ==========================================
    # ABA 3: GERENCIAR PROJETOS (Excluir)
    # ==========================================
    with aba_projetos:
        st.header("Excluir Projeto")
        st.warning("⚠️ Atenção: Excluir um projeto apagará todas as suas turmas e desmatriculará todos os alunos vinculados a ele.")
        
        projetos = db.query(Projeto).all()
        if projetos:
            opcoes_projetos = {p.id: p.nome for p in projetos}
            proj_id = st.selectbox("Selecione o projeto:", options=list(opcoes_projetos.keys()), format_func=lambda x: opcoes_projetos[x])
            
            if st.button("🗑️ Excluir Projeto e Turmas"):
                turmas = db.query(Turma).filter(Turma.projeto_id == proj_id).all()
                ids_turmas = [t.id for t in turmas]
                
                # Deleta matriculas vinculadas às turmas deste projeto
                if ids_turmas:
                    db.query(Matricula).filter(Matricula.turma_id.in_(ids_turmas)).delete(synchronize_session=False)
                # Deleta as turmas
                db.query(Turma).filter(Turma.projeto_id == proj_id).delete()
                # Deleta o projeto
                proj_para_deletar = db.query(Projeto).filter(Projeto.id == proj_id).first()
                db.delete(proj_para_deletar)
                
                db.commit()
                st.success("Projeto, turmas e matrículas excluídos com sucesso.")
                st.rerun()

finally:
    db.close()