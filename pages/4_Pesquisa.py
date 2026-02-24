import streamlit as st
import pandas as pd
import json
from database import SessionLocal, Aluno, Projeto, Turma, Matricula

st.set_page_config(page_title="Pesquisa e Relatórios", page_icon="🔍", layout="wide")
st.title("🔍 Pesquisa e Painel Geral")
st.write("Consulte os dados cadastrais, verifique as matrículas e acompanhe a lotação dos projetos.")

db = SessionLocal()

try:
    # Criando as abas da interface
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
            opcoes_alunos = {a.id: f"{a.nome_completo} (CPF: {a.cpf if a.cpf else 'N/A'})" for a in alunos}
            aluno_id_selecionado = st.selectbox(
                "Digite ou selecione o nome do aluno:", 
                options=list(opcoes_alunos.keys()), 
                format_func=lambda x: opcoes_alunos[x]
            )

            if aluno_id_selecionado:
                aluno = db.query(Aluno).filter(Aluno.id == aluno_id_selecionado).first()
                
                st.markdown("---")
                st.subheader(f"Perfil: {aluno.nome_completo}")
                
                # Dados Básicos em Colunas
                col1, col2, col3 = st.columns(3)
                col1.info(f"**Data de Nasc.:** {aluno.data_nascimento.strftime('%d/%m/%Y')}")
                col2.info(f"**RG:** {aluno.rg if aluno.rg else 'Não informado'}")
                col3.info(f"**CPF:** {aluno.cpf if aluno.cpf else 'Não informado'}")

                # Dados Completos (Lendo o JSON)
                with st.expander("📄 Ver Ficha de Cadastro Completa"):
                    dados_completos = json.loads(aluno.dados_cadastrais_json)
                    # O st.json cria uma visualização em árvore muito bonita para dados estruturados
                    st.json(dados_completos)

                # Projetos em que o aluno está matriculado
                st.markdown("### 📚 Matrículas Ativas")
                matriculas_aluno = db.query(Matricula).filter(Matricula.aluno_id == aluno.id).all()
                
                if matriculas_aluno:
                    lista_matriculas = []
                    for m in matriculas_aluno:
                        turma = db.query(Turma).filter(Turma.id == m.turma_id).first()
                        projeto = db.query(Projeto).filter(Projeto.id == turma.projeto_id).first()
                        
                        lista_matriculas.append({
                            "Projeto": projeto.nome,
                            "Turma": turma.nome_turma,
                            "Horário": turma.horario,
                            "Local": projeto.local,
                            "Data da Matrícula": m.data_matricula.strftime('%d/%m/%Y')
                        })
                    
                    # Exibe como uma tabela interativa
                    st.dataframe(pd.DataFrame(lista_matriculas), use_container_width=True, hide_index=True)
                else:
                    st.warning("Este aluno ainda não está matriculado em nenhum projeto social.")

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
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    st.write(f"**📍 Local:** {projeto.local}")
                    st.write(f"**📝 Descrição:** {projeto.descricao}")
                with col_p2:
                    st.write(f"**👨‍🏫 Professor/Responsável:** {projeto.nome_professor}")
                    status_pagamento = f"Remunerado (R$ {projeto.remuneracao_professor})" if projeto.remuneracao_professor > 0 else "Voluntário"
                    st.write(f"**💼 Vínculo:** {status_pagamento}")

                st.markdown("### 📊 Relatório de Turmas e Vagas")
                turmas_proj = db.query(Turma).filter(Turma.projeto_id == projeto.id).all()
                
                if turmas_proj:
                    lista_turmas = []
                    for t in turmas_proj:
                        qtd_matriculados = db.query(Matricula).filter(Matricula.turma_id == t.id).count()
                        vagas_livres = t.vagas_totais - qtd_matriculados
                        
                        lista_turmas.append({
                            "Turma": t.nome_turma,
                            "Horário": t.horario,
                            "Vagas Totais": t.vagas_totais,
                            "Alunos Matriculados": qtd_matriculados,
                            "Vagas Disponíveis": vagas_livres,
                            "Status": "🔴 Lotada" if vagas_livres <= 0 else "🟢 Vagas Abertas"
                        })
                    
                    df_turmas = pd.DataFrame(lista_turmas)
                    st.dataframe(df_turmas, use_container_width=True, hide_index=True)
                    
                    # Extra: Ver a lista de chamada da turma
                    st.markdown("#### 📋 Lista de Chamada")
                    turma_escolhida_nome = st.selectbox("Selecione a turma para ver os alunos matriculados:", [t.nome_turma for t in turmas_proj])
                    
                    if turma_escolhida_nome:
                        turma_selecionada = next(t for t in turmas_proj if t.nome_turma == turma_escolhida_nome)
                        alunos_da_turma = db.query(Matricula).filter(Matricula.turma_id == turma_selecionada.id).all()
                        
                        if alunos_da_turma:
                            lista_chamada = []
                            for m in alunos_da_turma:
                                al = db.query(Aluno).filter(Aluno.id == m.aluno_id).first()
                                lista_chamada.append({
                                    "Nome do Aluno": al.nome_completo, 
                                    "Telefone de Contato": json.loads(al.dados_cadastrais_json).get("contato_resp1", "N/A")
                                })
                            st.table(pd.DataFrame(lista_chamada))
                        else:
                            st.info("Nenhum aluno matriculado nesta turma ainda.")

                else:
                    st.warning("Este projeto ainda não possui turmas cadastradas.")

finally:
    db.close()