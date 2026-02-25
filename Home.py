import streamlit as st
import bcrypt
from database import SessionLocal, Usuario

st.set_page_config(page_title="Início de Sessão - Sistema Ágape", page_icon="🔐", layout="centered")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

db = SessionLocal()

try:
    # --- CRIAÇÃO DO PRIMEIRO UTILIZADOR (ADMIN) ---
    if not db.query(Usuario).first():
        senha_plana = "123".encode('utf-8')
        senha_hash = bcrypt.hashpw(senha_plana, bcrypt.gensalt()).decode('utf-8')
        
        # Criamos o usuário mestre já com a tag is_admin=True
        admin = Usuario(nome="Administrador", email="admin@agape.com", senha=senha_hash, is_admin=True)
        db.add(admin)
        db.commit()

    if not st.session_state.autenticado:
        st.title("🔐 Acesso Restrito")
        st.write("Bem-vindo ao Sistema Ágape. Por favor, inicie sessão para continuar.")
        
        with st.form("form_login"):
            email_digitado = st.text_input("E-mail")
            senha_digitada = st.text_input("Palavra-passe", type="password")
            btn_login = st.form_submit_button("Entrar", type="primary")
            
            if btn_login:
                usuario = db.query(Usuario).filter(Usuario.email == email_digitado).first()
                
                if usuario and bcrypt.checkpw(senha_digitada.encode('utf-8'), usuario.senha.encode('utf-8')):
                    st.session_state.autenticado = True
                    st.session_state.nome_usuario = usuario.nome
                    st.session_state.email_usuario = usuario.email
                    st.session_state.is_admin = usuario.is_admin # <-- GUARDAMOS O PERFIL AQUI
                    st.success("Sessão iniciada com sucesso! A recarregar...")
                    st.rerun()
                else:
                    st.error("❌ E-mail ou palavra-passe incorretos.")
                    
    else:
        st.title(f"Bem-vindo(a), {st.session_state.nome_usuario}! 🕊️")
        
        # Mostra um selinho especial se a pessoa for Administradora
        if st.session_state.get("is_admin", False):
            st.info("🛡️ Você está logado com uma conta de **Administrador**. Acesso total liberado.")
            
        st.write("Utilize o menu lateral para navegar entre as funcionalidades do sistema.")

        st.markdown("""
        ---
        ### 📌 Módulos Disponíveis:
        * **Cadastro de Alunos:** Formulário para adicionar novas crianças e adolescentes.
        * **Projetos e Turmas:** Gestão das iniciativas sociais e professores.
        * **Matrículas:** Ecrã para alocar os alunos nas vagas disponíveis.
        * **Pesquisa:** Painel geral para procurar dados.
        * **Avançado:** Edição, eliminação e gestão de acessos (Restrito).
        * **Relatórios:** Geração de PDFs para impressão.
        """)
        
        if st.button("Sair do Sistema (Logout)"):
            st.session_state.autenticado = False
            # Limpa o crachá da memória ao sair
            if "is_admin" in st.session_state:
                del st.session_state.is_admin
            st.rerun()

finally:
    db.close()