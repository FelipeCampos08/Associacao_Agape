import streamlit as st
import pandas as pd
import plotly.express as px
from database import SessionLocal, Aluno, Projeto, Turma, Matricula

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# --- PROTEÇÃO DE ACESSO ---
if "autenticado" not in st.session_state or not st.session_state.autenticado:
    st.warning("⚠️ Precisa de iniciar sessão para aceder a esta página.")
    st.stop()
# --------------------------

st.title("📊 Painel de Indicadores (Dashboard)")
st.write("Visão geral quantitativa dos atendimentos e projetos da Associação Ágape.")
st.markdown("---")

db = SessionLocal()

try:
    with st.spinner("Carregando indicadores..."):
        # --- BUSCA DOS DADOS MACRO ---
        total_alunos_ativos = db.query(Aluno).filter(Aluno.status_ativo == True).count()
        total_projetos = db.query(Projeto).count()
        total_turmas = db.query(Turma).count()
        total_matriculas = db.query(Matricula).count()

        # ==========================================
        # SEÇÃO 1: CARDS NUMÉRICOS (MÉTRICAS)
        # ==========================================
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Alunos Ativos", f"{total_alunos_ativos} 🧑‍🎓")
        col2.metric("Projetos Cadastrados", f"{total_projetos} ⚽")
        col3.metric("Turmas Abertas", f"{total_turmas} 🏫")
        col4.metric("Matrículas Realizadas", f"{total_matriculas} ✅")
        
        st.markdown("<br>", unsafe_allow_html=True) # Respiro visual

        # ==========================================
        # SEÇÃO 2: GRÁFICOS ANALÍTICOS
        # ==========================================
        # Gráfico 1: Matrículas por Projeto
        projetos = db.query(Projeto).all()
        turmas = db.query(Turma).all()
        matriculas = db.query(Matricula).all()

        dados_grafico = []
        for p in projetos:
            # Pega os IDs das turmas que pertencem a este projeto
            turmas_do_projeto = [t.id for t in turmas if t.projeto_id == p.id]
            # Conta quantas matrículas existem nessas turmas
            contagem = sum(1 for m in matriculas if m.turma_id in turmas_do_projeto)
            dados_grafico.append({"Projeto": p.nome, "Matrículas": contagem})

        df_projetos = pd.DataFrame(dados_grafico)

        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            st.subheader("Ocupação por Projeto")
            if not df_projetos.empty and df_projetos["Matrículas"].sum() > 0:
                # Gráfico de Barras usando Plotly (Fica com a cor laranja da Ágape)
                fig1 = px.bar(df_projetos, x="Projeto", y="Matrículas", 
                              color_discrete_sequence=["#F26522"],
                              text="Matrículas")
                fig1.update_traces(textposition='outside')
                fig1.update_layout(xaxis_title="", yaxis_title="Nº de Alunos", margin=dict(t=20, b=20, l=0, r=0))
                st.plotly_chart(fig1, width='content')
            else:
                st.info("Ainda não há matrículas suficientes para gerar este gráfico.")

        with col_graf2:
            st.subheader("Distribuição (Proporção)")
            if not df_projetos.empty and df_projetos["Matrículas"].sum() > 0:
                # Gráfico de Pizza
                fig2 = px.pie(df_projetos, names="Projeto", values="Matrículas", hole=0.4,
                              color_discrete_sequence=px.colors.sequential.Oranges_r)
                fig2.update_layout(margin=dict(t=20, b=20, l=0, r=0))
                st.plotly_chart(fig2, width='content')
            else:
                st.info("Ainda não há matrículas suficientes para gerar este gráfico.")

finally:
    db.close()