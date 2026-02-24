import streamlit as st

# Configuração global da página (Aba do navegador, ícone e layout)
st.set_page_config(
    page_title="Sistema Ágape",
    page_icon="🕊️",
    layout="wide"
)

st.title("Bem-vindo ao Sistema Ágape 🕊️")
st.write("Utilize o menu lateral para navegar entre as funcionalidades do sistema.")

st.markdown("""
---
### 📌 Módulos Disponíveis:

* **Cadastro de Alunos:** Formulário dinâmico para adicionar novas crianças e adolescentes à base.
* **Cadastro de Projetos:** Gerenciamento das iniciativas sociais, definição de turmas, vagas e professores.
* **Matrículas:** Tela para alocar os alunos cadastrados nas vagas disponíveis dos projetos.
* **Pesquisa:** Painel geral para buscar dados, verificar lotação de turmas e gerar relatórios rápidos.

---
*Desenvolvido com Python & Streamlit para otimizar o tempo e ajudar a transformar vidas!*
""")