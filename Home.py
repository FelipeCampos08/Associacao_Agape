import streamlit as st
import bcrypt
from database import SessionLocal, Usuario

VERSION = "1.0"

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
                    st.session_state.is_admin = usuario.is_admin
                    st.success("Sessão iniciada com sucesso! A recarregar...")
                    st.rerun()
                else:
                    st.error("❌ E-mail ou palavra-passe incorretos.")
                    
    else:
        st.title(f"Bem-vindo(a), {st.session_state.nome_usuario}!")
        
        if st.session_state.get("is_admin", False):
            st.info("🛡️ Conta de **Administrador**. Acesso total liberado.")
            
        st.write("Selecione um dos módulos abaixo para começar os trabalhos de hoje:")
        st.markdown("<br>", unsafe_allow_html=True)

        # --- MENU DE NAVEGAÇÃO EM GRID ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.page_link("pages/1_Cadastro_de_Alunos.py", label="Cadastro de Alunos", icon="📝")
            st.page_link("pages/2_Cadastro_de_Projetos.py", label="Projetos e Turmas", icon="⚽")
            st.page_link("pages/3_Matriculas.py", label="Matrículas", icon="✅")
            
        with col2:
            st.page_link("pages/4_Pesquisa.py", label="Pesquisa Geral", icon="🔍")
            st.page_link("pages/7_Relatorios.py", label="Relatórios e Impressões", icon="🖨️")
            
            # Esconde o botão do Avançado se não for Admin
            if st.session_state.get("is_admin", False):
                st.page_link("pages/5_Avancado.py", label="Administração Avançada", icon="⚙️")
        
        st.markdown("---")
        if st.button("Sair do Sistema (Logout)"):
            st.session_state.autenticado = False
            if "is_admin" in st.session_state:
                del st.session_state.is_admin
            st.rerun()

        # --- MARCA D'ÁGUA / RODAPÉ ---     
        st.markdown(f"""
            <div style="position: fixed; bottom: 10px; right: 20px; color: #888888; font-size: 12px; z-index: 100;">
                <b>Sistema Ágape</b> v{VERSION} | Se você começar, outros vão te acompanhar.
            </div>
        """, unsafe_allow_html=True)

finally:
    db.close()