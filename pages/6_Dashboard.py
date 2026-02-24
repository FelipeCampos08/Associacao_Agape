import streamlit as st
import pandas as pd
import json
import plotly.express as px
from database import SessionLocal, Aluno, Projeto, Turma, Matricula

st.set_page_config(page_title="Dashboard Ágape", page_icon="📊", layout="wide")
st.title("📊 Painel de Indicadores e Estatísticas")

db = SessionLocal()

try:
    alunos = db.query(Aluno).all()
    projetos = db.query(Projeto).all()
    turmas = db.query(Turma).all()
    matriculas = db.query(Matricula).all()

    # --- MÉTRICAS PRINCIPAIS (Kpis) ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Alunos", len(alunos))
    col2.metric("Projetos Ativos", len(projetos))
    col3.metric("Turmas Abertas", len(turmas))
    
    # Cálculo da Folha Salarial
    folha_salarial = sum([p.remuneracao_professor for p in projetos if p.remuneracao_professor is not None])
    col4.metric("Folha Salarial Mensal", f"R$ {folha_salarial:.2f}")

    st.markdown("---")

    if alunos:
        # Extraindo dados do JSON para análise
        dados_extraidos = []
        todas_vulnerabilidades = []
        
        for a in alunos:
            dict_dados = json.loads(a.dados_cadastrais_json)
            
            # Pega o gênero (se não existir, coloca Não Informado)
            genero = dict_dados.get("genero", "Não Informado")
            
            # Pega escolaridade
            periodo = dict_dados.get("periodo", "Não Informado")
            
            # Pega as vulnerabilidades (que é uma lista)
            vuln = dict_dados.get("vulnerabilidades", [])
            for v in vuln:
                if v != "Nenhuma":
                    todas_vulnerabilidades.append(v)
            
            dados_extraidos.append({
                "Gênero": genero,
                "Período Escolar": periodo
            })
            
        df_alunos = pd.DataFrame(dados_extraidos)

        # --- GRÁFICOS ---
        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            st.subheader("Distribuição por Gênero")
            contagem_genero = df_alunos['Gênero'].value_counts().reset_index()
            contagem_genero.columns = ['Gênero', 'Quantidade']
            fig_genero = px.pie(contagem_genero, values='Quantidade', names='Gênero', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_genero, use_container_width=True)

        with col_graf2:
            st.subheader("Período Escolar dos Alunos")
            contagem_periodo = df_alunos['Período Escolar'].value_counts().reset_index()
            contagem_periodo.columns = ['Período', 'Quantidade']
            fig_periodo = px.bar(contagem_periodo, x='Período', y='Quantidade', color='Período', text_auto=True)
            st.plotly_chart(fig_periodo, use_container_width=True)

        st.markdown("---")
        
        # Gráfico muito importante para a Psicologia/Assistência Social
        st.subheader("⚠️ Mapa de Vulnerabilidades Sociais")
        if todas_vulnerabilidades:
            df_vuln = pd.DataFrame(todas_vulnerabilidades, columns=["Vulnerabilidade"])
            contagem_vuln = df_vuln["Vulnerabilidade"].value_counts().reset_index()
            contagem_vuln.columns = ["Vulnerabilidade", "Casos Identificados"]
            
            fig_vuln = px.bar(contagem_vuln, y='Vulnerabilidade', x='Casos Identificados', orientation='h', 
                              color='Casos Identificados', color_continuous_scale='Reds', text_auto=True)
            fig_vuln.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_vuln, use_container_width=True)
        else:
            st.info("Nenhuma vulnerabilidade mapeada nos alunos cadastrados até o momento.")

    else:
        st.info("Cadastre alunos para visualizar os gráficos de estatísticas.")

finally:
    db.close()