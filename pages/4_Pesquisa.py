import streamlit as st
import pandas as pd
import json
from database import SessionLocal, Aluno, Projeto, Turma, Matricula

st.set_page_config(page_title="Pesquisa e Relatórios", page_icon="🔍", layout="wide")

# --- PROTEÇÃO DE ACESSO ---
if "autenticado" not in st.session_state or not st.session_state.autenticado:
    st.warning("⚠️ Você precisa fazer login para acessar esta página.")
    st.stop() # Interrompe a leitura do código aqui e bloqueia a tela
# --------------------------

st.title("🔍 Pesquisa e Painel Geral")
st.write("Consulte os dados cadastrais, verifique as matrículas e acompanhe a lotação dos projetos.")

db = SessionLocal()

try:
    aba_alunos, aba_projetos = st.tabs(["🎓 Pesquisa de Alunos", "⚽ Pesquisa de Projetos e Vagas"])

    # ==========================================
    # ABA 1: PESQUISA DE ALUNOS
    # ==========================================
    with aba_alunos:
        st.header("Buscar Aluno")
        alunos = db.query(Aluno).all()
        
        if not alunos:
            st.info("Nenhum aluno cadastrado na base de dados.")
        else:
            # Mostra o status visualmente no selectbox
            opcoes_alunos = {a.id: f"{'🟢' if a.status_ativo else '🔴'} {a.nome_completo} (CPF: {a.cpf if a.cpf else 'N/A'})" for a in alunos}
            aluno_id_selecionado = st.selectbox(
                "Digite ou selecione o nome do aluno:", 
                options=list(opcoes_alunos.keys()), 
                format_func=lambda x: opcoes_alunos[x]
            )

            if aluno_id_selecionado:
                aluno = db.query(Aluno).filter(Aluno.id == aluno_id_selecionado).first()
                
                st.markdown("---")
                st.subheader(f"Perfil: {aluno.nome_completo}")
                if not aluno.status_ativo:
                    st.warning("⚠️ Este aluno está marcado como INATIVO no sistema.")
                
                col1, col2, col3 = st.columns(3)
                col1.info(f"**Data de Nasc.:** {aluno.data_nascimento.strftime('%d/%m/%Y')}")
                col2.info(f"**RG:** {aluno.rg if aluno.rg else 'Não informado'}")
                col3.info(f"**CPF:** {aluno.cpf if aluno.cpf else 'Não informado'}")

                with st.expander("📄 Ver Ficha de Cadastro Completa"):
                    dados_completos = json.loads(aluno.dados_cadastrais_json)
                    
                    # Formata as chaves tirando o underline e capitalizando
                    col_f1, col_f2 = st.columns(2)
                    itens = list(dados_completos.items())
                    metade = len(itens) // 2
                    
                    with col_f1:
                        for chave, valor in itens[:metade]:
                            chave_limpa = chave.replace("_", " ").title()
                            # Se for uma lista (ex: vulnerabilidades), junta com vírgula
                            valor_limpo = ", ".join(valor) if isinstance(valor, list) else valor
                            st.write(f"**{chave_limpa}:** {valor_limpo}")
                            
                    with col_f2:
                        for chave, valor in itens[metade:]:
                            chave_limpa = chave.replace("_", " ").title()
                            valor_limpo = ", ".join(valor) if isinstance(valor, list) else valor
                            st.write(f"**{chave_limpa}:** {valor_limpo}")

                st.markdown("### 📚 Matrículas (Histórico)")
                matriculas_aluno = db.query(Matricula).filter(Matricula.aluno_id == aluno.id).all()
                
                if matriculas_aluno:
                    lista_matriculas = []
                    for m in matriculas_aluno:
                        turma = db.query(Turma).filter(Turma.id == m.turma_id).first()
                        projeto = db.query(Projeto).filter(Projeto.id == turma.projeto_id).first()
                        
                        lista_matriculas.append({
                            "Ano Letivo": turma.ano_letivo,
                            "Projeto": projeto.nome,
                            "Turma": turma.nome_turma,
                            "Professor": turma.nome_professor,
                            "Horário": turma.horario,
                            "Local": projeto.local,
                            "Data da Matrícula": m.data_matricula.strftime('%d/%m/%Y')
                        })
                    
                    df_mat = pd.DataFrame(lista_matriculas)
                    # Ordenando do ano mais recente para o mais antigo
                    df_mat = df_mat.sort_values(by="Ano Letivo", ascending=False)
                    st.dataframe(df_mat, use_container_width=True, hide_index=True)
                else:
                    st.warning("Este aluno não possui histórico de matrículas.")

    # ==========================================
    # ABA 2: PESQUISA DE PROJETOS E VAGAS
    # ==========================================
    with aba_projetos:
        st.header("Visão Geral dos Projetos")
        projetos = db.query(Projeto).all()
        
        if not projetos:
            st.info("Nenhum projeto cadastrado na base de dados.")
        else:
            opcoes_projetos = {p.id: p.nome for p in projetos}
            projeto_id_selec = st.selectbox(
                "Selecione o Projeto para ver os detalhes:", 
                options=list(opcoes_projetos.keys()), 
                format_func=lambda x: opcoes_projetos[x]
            )

            if projeto_id_selec:
                projeto = db.query(Projeto).filter(Projeto.id == projeto_id_selec).first()
                
                st.markdown("---")
                st.write(f"**📍 Local do Projeto:** {projeto.local}")
                st.write(f"**📝 Descrição:** {projeto.descricao}")

                st.markdown("### 📊 Relatório de Turmas e Vagas")
                turmas_proj = db.query(Turma).filter(Turma.projeto_id == projeto.id).all()
                
                if turmas_proj:
                    lista_turmas = []
                    for t in turmas_proj:
                        qtd_matriculados = db.query(Matricula).filter(Matricula.turma_id == t.id).count()
                        vagas_livres = t.vagas_totais - qtd_matriculados
                        
                        lista_turmas.append({
                            "Ano Letivo": t.ano_letivo,
                            "Turma": t.nome_turma,
                            "Horário": t.horario,
                            "Professor": t.nome_professor,
                            "Vagas Totais": t.vagas_totais,
                            "Matriculados": qtd_matriculados,
                            "Vagas Disponíveis": vagas_livres,
                            "Status": "🔴 Lotada" if vagas_livres <= 0 else "🟢 Vagas Abertas"
                        })
                    
                    df_turmas = pd.DataFrame(lista_turmas)
                    df_turmas = df_turmas.sort_values(by="Ano Letivo", ascending=False)
                    st.dataframe(df_turmas, use_container_width=True, hide_index=True)
                    
                    st.markdown("#### 📋 Lista de Chamada")
                    opcoes_chamada = {t.id: f"{t.nome_turma} ({t.ano_letivo})" for t in turmas_proj}
                    turma_escolhida_id = st.selectbox("Selecione a turma para ver os alunos:", options=list(opcoes_chamada.keys()), format_func=lambda x: opcoes_chamada[x])
                    
                    if turma_escolhida_id:
                        alunos_da_turma = db.query(Matricula).filter(Matricula.turma_id == turma_escolhida_id).all()
                        
                        if alunos_da_turma:
                            lista_chamada = []
                            for m in alunos_da_turma:
                                al = db.query(Aluno).filter(Aluno.id == m.aluno_id).first()
                                lista_chamada.append({
                                    "Nome do Aluno": al.nome_completo, 
                                    "Status": "Ativo" if al.status_ativo else "Inativo",
                                    "Telefone de Contato": json.loads(al.dados_cadastrais_json).get("contato_resp1", "N/A")
                                })
                            st.table(pd.DataFrame(lista_chamada))
                        else:
                            st.info("Nenhum aluno matriculado nesta turma.")

                else:
                    st.warning("Este projeto ainda não possui turmas cadastradas.")

finally:
    db.close()