import streamlit as st
import json
import datetime
import bcrypt
from database import SessionLocal, Aluno, Projeto, Turma, Matricula, Usuario

st.set_page_config(page_title="Avançado e Edição", page_icon="⚙️", layout="wide")

if "autenticado" not in st.session_state or not st.session_state.autenticado:
    st.warning("⚠️ Precisa de iniciar sessão para aceder a esta página.")
    st.stop()

st.title("⚙️ Administração Avançada")
st.write("Área restrita para edição de dados, eliminação e gestão de matrículas.")

if "mensagem_sucesso" in st.session_state:
    st.success(st.session_state.mensagem_sucesso)
    del st.session_state.mensagem_sucesso

db = SessionLocal()

@st.cache_data
def carregar_campos():
    with open("config_campos.json", "r", encoding="utf-8") as f:
        return json.load(f)["cadastro_aluno"]

try:
    # --- LÓGICA DE ABAS DINÂMICAS (Oculta a aba de usuários para quem não é Admin) ---
    nomes_abas = ["🔄 Estado", "❌ Desmatricular", "✏️ Editar Aluno", "✏️ Editar Projetos", "🗑️ Eliminar Registos"]
    
    eh_admin = st.session_state.get("is_admin", False)
    if eh_admin:
        nomes_abas.append("👥 Gerir Utilizadores (Admin)")

    abas = st.tabs(nomes_abas)
    
    aba_status, aba_desmatricular, aba_editar_aluno, aba_editar_proj, aba_excluir = abas[:5]

    # ==========================================
    # ABA 1: STATUS DO ALUNO (Ativo/Inativo)
    # ==========================================
    with aba_status:
        st.header("Alterar Status do Aluno (Ciclo Anual)")
        alunos_todos = db.query(Aluno).all()
        if alunos_todos:
            opcoes_status = {a.id: f"{'🟢' if a.status_ativo else '🔴'} {a.nome_completo}" for a in alunos_todos}
            aluno_status_id = st.selectbox("Selecione o aluno:", options=list(opcoes_status.keys()), format_func=lambda x: opcoes_status[x], key="sel_status")
            
            aluno_selecionado = db.query(Aluno).filter(Aluno.id == aluno_status_id).first()
            novo_status = st.radio("Definir como:", ["Ativo", "Inativo"], index=0 if aluno_selecionado.status_ativo else 1)
            
            # BOTÃO COM CONFIRMAÇÃO
            with st.popover("🔄 Atualizar Status"):
                st.write(f"Deseja realmente alterar o status deste aluno para **{novo_status}**?")
                if st.button("Sim, Atualizar Status", key="conf_status", type="primary"):
                    aluno_selecionado.status_ativo = (novo_status == "Ativo")
                    db.commit()
                    st.session_state.mensagem_sucesso = f"Status atualizado para {novo_status} com sucesso!"
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
            
            # BOTÃO COM CONFIRMAÇÃO
            with st.popover("❌ Cancelar Matrícula"):
                st.warning("Tem certeza? O aluno perderá a vaga nesta turma.")
                if st.button("Sim, Cancelar Matrícula", key="conf_desmatricular", type="primary"):
                    db.query(Matricula).filter(Matricula.id == mat_selecionada).delete()
                    db.commit()
                    st.session_state.mensagem_sucesso = "Matrícula cancelada com sucesso! A vaga está livre novamente."
                    st.rerun()

    # ==========================================
    # ABA 3: EDITAR ALUNO (Dinâmico)
    # ==========================================
    with aba_editar_aluno:
        st.header("Editar Dados Cadastrais do Aluno")
        if alunos_todos:
            opcoes_alunos_edit = {a.id: a.nome_completo for a in alunos_todos}
            aluno_edit_id = st.selectbox("Selecione o aluno para editar:", options=list(opcoes_alunos_edit.keys()), format_func=lambda x: opcoes_alunos_edit[x], key="sel_edit_aluno")
            
            aluno_edit = db.query(Aluno).filter(Aluno.id == aluno_edit_id).first()
            dados_atuais = json.loads(aluno_edit.dados_cadastrais_json)
            config = carregar_campos()
            novas_respostas = {}

            st.markdown("---")
            for categoria, campos in config.items():
                st.subheader(categoria.replace("_", " ").title())
                for campo in campos:
                    nome = campo["nome"]
                    tipo = campo["tipo"]
                    label = campo["label"]
                    valor_atual = dados_atuais.get(nome)
                    
                    key = f"edit_aluno_{nome}_{aluno_edit_id}"
                    
                    if tipo == "text":
                        novas_respostas[nome] = st.text_input(label, value=valor_atual if valor_atual else "", key=key)
                    elif tipo == "date":
                        try:
                            d_atual = datetime.datetime.strptime(valor_atual, "%Y-%m-%d").date() if valor_atual else datetime.date.today()
                        except:
                            d_atual = datetime.date.today()
                        novas_respostas[nome] = st.date_input(label, value=d_atual, min_value=datetime.date(1990, 1, 1), max_value=datetime.date.today(), key=key)
                    elif tipo == "number":
                        novas_respostas[nome] = st.number_input(label, value=float(valor_atual) if valor_atual else 0.0, step=0.1, key=key)
                    elif tipo == "selectbox":
                        opcoes = campo.get("opcoes", [])
                        idx = opcoes.index(valor_atual) if valor_atual in opcoes else 0
                        novas_respostas[nome] = st.selectbox(label, options=opcoes, index=idx, key=key)
                    elif tipo == "multiselect":
                        opcoes = campo.get("opcoes", [])
                        val_sel = valor_atual if isinstance(valor_atual, list) else []
                        novas_respostas[nome] = st.multiselect(label, options=opcoes, default=val_sel, key=key)
                    elif tipo == "textarea":
                        novas_respostas[nome] = st.text_area(label, value=valor_atual if valor_atual else "", key=key)
                    elif tipo == "radio_com_detalhe":
                        idx = 1 if valor_atual == "Sim" else 0
                        novas_respostas[nome] = st.radio(label, options=["Não", "Sim"], index=idx, key=key)
                        if novas_respostas[nome] == "Sim":
                            val_detalhe = dados_atuais.get(f"{nome}_detalhe", "")
                            novas_respostas[f"{nome}_detalhe"] = st.text_input(f"Especifique ({campo['label']}):", value=val_detalhe, key=f"{key}_detalhe")

            st.markdown("---")
            # BOTÃO COM CONFIRMAÇÃO
            with st.popover("💾 Salvar Alterações do Aluno"):
                st.write("Confirma a atualização dos dados cadastrais deste aluno?")
                if st.button("Sim, Salvar Alterações", key="conf_salvar_aluno", type="primary"):
                    aluno_edit.nome_completo = novas_respostas.get("nome_completo", aluno_edit.nome_completo)
                    aluno_edit.data_nascimento = novas_respostas.get("data_nascimento", aluno_edit.data_nascimento)
                    aluno_edit.rg = novas_respostas.get("rg", aluno_edit.rg)
                    aluno_edit.cpf = novas_respostas.get("cpf", aluno_edit.cpf)
                    
                    respostas_json_safe = novas_respostas.copy()
                    if "data_nascimento" in respostas_json_safe:
                        respostas_json_safe["data_nascimento"] = respostas_json_safe["data_nascimento"].strftime("%Y-%m-%d")
                    
                    aluno_edit.dados_cadastrais_json = json.dumps(respostas_json_safe, ensure_ascii=False)
                    
                    db.commit()
                    st.session_state.mensagem_sucesso = "Dados do aluno atualizados com sucesso!"
                    st.rerun()

    # ==========================================
    # ABA 4: EDITAR PROJETOS E TURMAS
    # ==========================================
    with aba_editar_proj:
        st.header("Editar Projetos e Turmas")
        tipo_edicao = st.radio("O que você deseja editar?", ["O Projeto (Catálogo)", "A Turma (Professor, Horário, Vagas)"], horizontal=True)
        
        projetos = db.query(Projeto).all()
        if not projetos:
            st.warning("Nenhum projeto cadastrado.")
        else:
            opcoes_proj_edit = {p.id: p.nome for p in projetos}
            
            if tipo_edicao == "O Projeto (Catálogo)":
                proj_id_edit = st.selectbox("Selecione o Projeto:", options=list(opcoes_proj_edit.keys()), format_func=lambda x: opcoes_proj_edit[x], key="sel_edit_proj")
                proj_selec = db.query(Projeto).filter(Projeto.id == proj_id_edit).first()
                
                novo_nome = st.text_input("Nome do Projeto", value=proj_selec.nome)
                nova_desc = st.text_area("Descrição", value=proj_selec.descricao)
                novo_local = st.text_input("Local", value=proj_selec.local)
                
                # BOTÃO COM CONFIRMAÇÃO
                with st.popover("💾 Atualizar Projeto"):
                    st.write("Confirma as alterações nas informações deste projeto?")
                    if st.button("Sim, Atualizar Projeto", key="conf_salvar_proj", type="primary"):
                        proj_selec.nome = novo_nome
                        proj_selec.descricao = nova_desc
                        proj_selec.local = novo_local
                        db.commit()
                        st.session_state.mensagem_sucesso = "Projeto atualizado no catálogo com sucesso!"
                        st.rerun()
            
            else:
                proj_id_edit = st.selectbox("Selecione o Projeto:", options=list(opcoes_proj_edit.keys()), format_func=lambda x: opcoes_proj_edit[x], key="sel_edit_proj_turma")
                turmas_do_proj = db.query(Turma).filter(Turma.projeto_id == proj_id_edit).all()
                
                if not turmas_do_proj:
                    st.warning("Nenhuma turma cadastrada para este projeto.")
                else:
                    opcoes_turma_edit = {t.id: f"{t.nome_turma} ({t.ano_letivo})" for t in turmas_do_proj}
                    turma_id_edit = st.selectbox("Selecione a Turma:", options=list(opcoes_turma_edit.keys()), format_func=lambda x: opcoes_turma_edit[x])
                    turma_selec = db.query(Turma).filter(Turma.id == turma_id_edit).first()
                    
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        t_nome = st.text_input("Nome da Turma", value=turma_selec.nome_turma)
                        t_horario = st.text_input("Horário", value=turma_selec.horario)
                        t_vagas = st.number_input("Vagas Totais", value=turma_selec.vagas_totais, min_value=1)
                        t_ano = st.number_input("Ano Letivo", value=turma_selec.ano_letivo, min_value=2024)
                    with col2:
                        t_prof = st.text_input("Professor(a)", value=turma_selec.nome_professor)
                        t_cpf = st.text_input("CPF do Professor", value=turma_selec.cpf_professor if turma_selec.cpf_professor else "")
                        t_remun = st.number_input("Remuneração (R$)", value=float(turma_selec.remuneracao_professor) if turma_selec.remuneracao_professor else 0.0, step=50.0)
                        
                    # BOTÃO COM CONFIRMAÇÃO
                    with st.popover("💾 Atualizar Turma"):
                        st.write("Confirma as alterações nos dados desta turma e professor?")
                        if st.button("Sim, Atualizar Turma", key="conf_salvar_turma", type="primary"):
                            turma_selec.nome_turma = t_nome
                            turma_selec.horario = t_horario
                            turma_selec.vagas_totais = t_vagas
                            turma_selec.ano_letivo = t_ano
                            turma_selec.nome_professor = t_prof
                            turma_selec.cpf_professor = t_cpf
                            turma_selec.remuneracao_professor = t_remun
                            db.commit()
                            st.session_state.mensagem_sucesso = "Dados da turma e do professor atualizados com sucesso!"
                            st.rerun()

    # ==========================================
    # ABA 5: EXCLUIR REGISTROS
    # ==========================================
    with aba_excluir:
        st.header("Exclusão Permanente")
        col_ex_aluno, col_ex_proj = st.columns(2)
        
        with col_ex_aluno:
            st.subheader("🗑️ Excluir Aluno")
            st.info("💡 Dica: Se o aluno apenas parou de frequentar, prefira inativá-lo na aba 'Status'.")
            if alunos_todos:
                opcoes_excluir = {a.id: a.nome_completo for a in alunos_todos}
                aluno_id = st.selectbox("Selecione o aluno:", options=list(opcoes_excluir.keys()), format_func=lambda x: opcoes_excluir[x])
                
                # BOTÃO COM CONFIRMAÇÃO
                with st.popover("Excluir Aluno"):
                    st.error("⚠️ **ATENÇÃO:** Esta ação é IRREVERSÍVEL. Todo o histórico do aluno será apagado.")
                    if st.button("Sim, Excluir Definitivamente", key="conf_excluir_aluno", type="primary"):
                        db.query(Matricula).filter(Matricula.aluno_id == aluno_id).delete()
                        db.query(Aluno).filter(Aluno.id == aluno_id).delete()
                        db.commit()
                        st.session_state.mensagem_sucesso = "Aluno e histórico excluídos permanentemente."
                        st.rerun()

        with col_ex_proj:
            st.subheader("🗑️ Excluir Projeto ou Turma")
            tipo_exclusao = st.radio("O que você deseja excluir?", ["O Projeto Completo (Catálogo e Turmas)", "Apenas uma Turma Específica"])
            
            projetos = db.query(Projeto).all()
            if projetos:
                opcoes_projetos_ex = {p.id: p.nome for p in projetos}
                
                if tipo_exclusao == "O Projeto Completo (Catálogo e Turmas)":
                    proj_id = st.selectbox("Selecione o projeto para excluir:", options=list(opcoes_projetos_ex.keys()), format_func=lambda x: opcoes_projetos_ex[x], key="excluir_proj_completo")
                    
                    # BOTÃO COM CONFIRMAÇÃO
                    with st.popover("Excluir Projeto"):
                        st.error("⚠️ **ATENÇÃO:** O projeto, todas as suas turmas e matrículas serão apagados.")
                        if st.button("Sim, Excluir Projeto e Turmas", key="conf_excluir_proj_total", type="primary"):
                            turmas = db.query(Turma).filter(Turma.projeto_id == proj_id).all()
                            ids_turmas = [t.id for t in turmas]
                            if ids_turmas:
                                db.query(Matricula).filter(Matricula.turma_id.in_(ids_turmas)).delete(synchronize_session=False)
                            db.query(Turma).filter(Turma.projeto_id == proj_id).delete()
                            db.query(Projeto).filter(Projeto.id == proj_id).delete()
                            db.commit()
                            st.session_state.mensagem_sucesso = "Projeto e todas as dependências excluídos com sucesso."
                            st.rerun()
                
                else:
                    proj_id = st.selectbox("Selecione o projeto:", options=list(opcoes_projetos_ex.keys()), format_func=lambda x: opcoes_projetos_ex[x], key="excluir_proj_turma")
                    turmas_do_proj = db.query(Turma).filter(Turma.projeto_id == proj_id).all()
                    
                    if not turmas_do_proj:
                        st.info("Este projeto não possui turmas cadastradas para excluir.")
                    else:
                        opcoes_turma_ex = {t.id: f"{t.nome_turma} ({t.ano_letivo})" for t in turmas_do_proj}
                        turma_id_ex = st.selectbox("Selecione a turma para excluir:", options=list(opcoes_turma_ex.keys()), format_func=lambda x: opcoes_turma_ex[x])
                        
                        # BOTÃO COM CONFIRMAÇÃO
                        with st.popover("Excluir Apenas a Turma"):
                            st.error("⚠️ **ATENÇÃO:** A turma e as matrículas vinculadas a ela serão apagadas.")
                            if st.button("Sim, Excluir Turma", key="conf_excluir_turma_unica", type="primary"):
                                db.query(Matricula).filter(Matricula.turma_id == turma_id_ex).delete(synchronize_session=False)
                                db.query(Turma).filter(Turma.id == turma_id_ex).delete()
                                db.commit()
                                st.session_state.mensagem_sucesso = "Turma excluída com sucesso."
                                st.rerun()

    # ==========================================
    # ABA 6: GERIR UTILIZADORES (APENAS ADMIN)
    # ==========================================
    if eh_admin:
        aba_usuarios = abas[5]
        with aba_usuarios:
            st.header("Gestão de Acessos da Equipa")
            st.write("Controle exclusivo para Administradores.")
            st.markdown("---")
            
            # Dividimos em 3 colunas para acomodar a nova função de resetar senha
            col_add, col_reset, col_del = st.columns(3)
            
            with col_add:
                st.subheader("➕ Adicionar Utilizador")
                with st.form("form_novo_usuario"):
                    novo_nome = st.text_input("Nome Completo")
                    novo_email = st.text_input("E-mail")
                    nova_senha = st.text_input("Palavra-passe provisória", type="password")
                    
                    # Permite escolher se o novo funcionário também será admin
                    novo_perfil = st.selectbox("Perfil de Acesso", ["Comum", "Administrador"])
                    
                    btn_criar_user = st.form_submit_button("Criar Utilizador", type="primary")
                    
                    if btn_criar_user:
                        if not novo_nome or not novo_email or not nova_senha:
                            st.error("⚠️ Preencha todos os campos.")
                        elif db.query(Usuario).filter(Usuario.email == novo_email).first():
                            st.error("❌ Este e-mail já existe no sistema.")
                        else:
                            senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            is_adm = True if novo_perfil == "Administrador" else False
                            
                            novo_user = Usuario(nome=novo_nome, email=novo_email, senha=senha_hash, is_admin=is_adm)
                            db.add(novo_user)
                            db.commit()
                            st.session_state.mensagem_sucesso = f"Usuário {novo_nome} criado com sucesso!"
                            st.rerun()

            with col_reset:
                st.subheader("🔑 Redefinir Senha")
                usuarios_db = db.query(Usuario).all()
                opcoes_users_reset = {u.id: f"{u.nome} ({u.email})" for u in usuarios_db}
                
                with st.form("form_reset_senha"):
                    user_id_reset = st.selectbox("Selecione o usuário:", options=list(opcoes_users_reset.keys()), format_func=lambda x: opcoes_users_reset[x])
                    senha_recuperacao = st.text_input("Digite a nova palavra-passe", type="password")
                    btn_reset = st.form_submit_button("Salvar Nova Senha")
                    
                    if btn_reset:
                        if not senha_recuperacao:
                            st.error("⚠️ Digite uma nova senha.")
                        else:
                            user_para_reset = db.query(Usuario).filter(Usuario.id == user_id_reset).first()
                            senha_hash_nova = bcrypt.hashpw(senha_recuperacao.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            user_para_reset.senha = senha_hash_nova
                            db.commit()
                            st.session_state.mensagem_sucesso = f"Senha de {user_para_reset.nome} redefinida com sucesso!"
                            st.rerun()
                            
            with col_del:
                st.subheader("🗑️ Remover Acesso")
                usuarios_removiveis = [u for u in usuarios_db if u.email != st.session_state.get("email_usuario")]
                
                if not usuarios_removiveis:
                    st.info("Não existem outros utilizadores no sistema além de si.")
                else:
                    opcoes_users_del = {u.id: f"{u.nome} ({u.email})" for u in usuarios_removiveis}
                    user_id_del = st.selectbox("Selecione a pessoa a remover:", options=list(opcoes_users_del.keys()), format_func=lambda x: opcoes_users_del[x])
                    
                    with st.popover("Remover Acesso"):
                        st.error("⚠️ **ATENÇÃO:** O acesso será revogado imediatamente.")
                        if st.button("Sim, Remover", type="primary"):
                            db.query(Usuario).filter(Usuario.id == user_id_del).delete()
                            db.commit()
                            st.session_state.mensagem_sucesso = "Acesso revogado com sucesso!"
                            st.rerun()

finally:
    db.close()