import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import date
from database import SessionLocal, Aluno, Projeto, Turma, Matricula

st.set_page_config(page_title="Dashboard Ágape", page_icon="📊", layout="wide")
st.title("📊 Painel de Indicadores e Estatísticas")

db = SessionLocal()

try:
    ano_atual = date.today().year
    
    # Filtra alunos ativos para as métricas principais
    alunos_ativos = db.query(Aluno).filter(Aluno.status_ativo == True).all()
    projetos = db.query(Projeto).all()
    # Pega apenas turmas do ano atual para folha salarial
    turmas_ano_atual = db.query(Turma).filter(Turma.ano_letivo == ano_atual).all()
    matriculas = db.query(Matricula).all()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Alunos Ativos", len(alunos_ativos))
    col2.metric("Projetos no Catálogo", len(projetos))
    col3.metric(f"Turmas Abertas ({ano_atual})", len(turmas_ano_atual))
    
    # O cálculo de salário agora é feito pelas turmas do ano!
    folha_salarial = sum([t.remuneracao_professor for t in turmas_ano_atual if t.remuneracao_professor is not None])
    col4.metric("Folha Salarial Mensal Estimada", f"R$ {folha_salarial:.2f}")

    st.markdown("---")

    if alunos_ativos:
        dados_extraidos = []
        todas_vulnerabilidades = []
        
        for a in alunos_ativos:
            dict_dados = json.loads(a.dados_cadastrais_json)
            genero = dict_dados.get("genero", "Não Informado")
            periodo = dict_dados.get("periodo", "Não Informado")
            
            vuln = dict_dados.get("vulnerabilidades", [])
            for v in vuln:
                if v != "Nenhuma":
                    todas_vulnerabilidades.append(v)
            
            dados_extraidos.append({
                "Gênero": genero,
                "Período Escolar": periodo
            })
            
        df_alunos = pd.DataFrame(dados_extraidos)

        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            st.subheader("Distribuição por Gênero (Ativos)")
            contagem_genero = df_alunos['Gênero'].value_counts().reset_index()
            contagem_genero.columns = ['Gênero', 'Quantidade']
            fig_genero = px.pie(contagem_genero, values='Quantidade', names='Gênero', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_genero, use_container_width=True)

        with col_graf2:
            st.subheader("Período Escolar dos Alunos (Ativos)")
            contagem_periodo = df_alunos['Período Escolar'].value_counts().reset_index()
            contagem_periodo.columns = ['Período', 'Quantidade']
            fig_periodo = px.bar(contagem_periodo, x='Período', y='Quantidade', color='Período', text_auto=True)
            st.plotly_chart(fig_periodo, use_container_width=True)

        st.markdown("---")
        
        st.subheader("⚠️ Mapa de Vulnerabilidades Sociais (Ativos)")
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
        st.info("Cadastre alunos ativos para visualizar os gráficos de estatísticas.")

finally:
    db.close()