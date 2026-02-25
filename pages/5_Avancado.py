import streamlit as st
import json
import datetime
from database import SessionLocal, Aluno, Projeto, Turma, Matricula

st.set_page_config(page_title="Avançado e Edição", page_icon="⚙️", layout="wide")
st.title("⚙️ Administração Avançada")
st.write("Área restrita para edição de dados, exclusão e gestão de matrículas.")

db = SessionLocal()

@st.cache_data
def carregar_campos():
    with open("config_campos.json", "r", encoding="utf-8") as f:
        return json.load(f)["cadastro_aluno"]

try:
    aba_status, aba_desmatricular, aba_editar_aluno, aba_editar_proj, aba_excluir = st.tabs([
        "🔄 Status", "❌ Desmatricular", "✏️ Editar Aluno", "✏️ Editar Projetos/Turmas", "🗑️ Excluir Registros"
    ])

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
            
            if st.button("Atualizar Status", key="btn_status"):
                aluno_selecionado.status_ativo = (novo_status == "Ativo")
                db.commit()
                st.success(f"Status atualizado para {novo_status}!")
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
            if st.button("Cancelar Matrícula", type="primary"):
                db.query(Matricula).filter(Matricula.id == mat_selecionada).delete()
                db.commit()
                st.success("Matrícula cancelada com sucesso!")
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

            if st.button("Salvar Alterações do Aluno", type="primary", key="btn_salvar_aluno"):
                aluno_edit.nome_completo = novas_respostas.get("nome_completo", aluno_edit.nome_completo)
                aluno_edit.data_nascimento = novas_respostas.get("data_nascimento", aluno_edit.data_nascimento)
                aluno_edit.rg = novas_respostas.get("rg", aluno_edit.rg)
                aluno_edit.cpf = novas_respostas.get("cpf", aluno_edit.cpf)
                
                respostas_json_safe = novas_respostas.copy()
                if "data_nascimento" in respostas_json_safe:
                    respostas_json_safe["data_nascimento"] = respostas_json_safe["data_nascimento"].strftime("%Y-%m-%d")
                
                aluno_edit.dados_cadastrais_json = json.dumps(respostas_json_safe, ensure_ascii=False)
                
                db.commit()
                st.success("Dados do aluno atualizados com sucesso!")
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
                
                if st.button("Atualizar Projeto", type="primary"):
                    proj_selec.nome = novo_nome
                    proj_selec.descricao = nova_desc
                    proj_selec.local = novo_local
                    db.commit()
                    st.success("Projeto atualizado com sucesso!")
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
                        
                    if st.button("Atualizar Turma", type="primary"):
                        turma_selec.nome_turma = t_nome
                        turma_selec.horario = t_horario
                        turma_selec.vagas_totais = t_vagas
                        turma_selec.ano_letivo = t_ano
                        turma_selec.nome_professor = t_prof
                        turma_selec.cpf_professor = t_cpf
                        turma_selec.remuneracao_professor = t_remun
                        db.commit()
                        st.success("Dados da turma e do professor atualizados!")
                        st.rerun()

    # ==========================================
    # ABA 5: EXCLUIR REGISTROS
    # ==========================================
    with aba_excluir:
        st.header("Exclusão Permanente")
        col_ex_aluno, col_ex_proj = st.columns(2)
        
        with col_ex_aluno:
            st.subheader("🗑️ Excluir Aluno")
            st.warning("⚠️ Apaga todo o histórico do aluno. Prefira inativar na aba 'Status'.")
            if alunos_todos:
                opcoes_excluir = {a.id: a.nome_completo for a in alunos_todos}
                aluno_id = st.selectbox("Selecione o aluno:", options=list(opcoes_excluir.keys()), format_func=lambda x: opcoes_excluir[x])
                if st.button("Excluir Aluno"):
                    db.query(Matricula).filter(Matricula.aluno_id == aluno_id).delete()
                    db.query(Aluno).filter(Aluno.id == aluno_id).delete()
                    db.commit()
                    st.success("Aluno excluído.")
                    st.rerun()

        with col_ex_proj:
            st.subheader("🗑️ Excluir Projeto ou Turma")
            tipo_exclusao = st.radio("O que você deseja excluir?", ["O Projeto Completo (Catálogo e Turmas)", "Apenas uma Turma Específica"])
            
            projetos = db.query(Projeto).all()
            if projetos:
                opcoes_projetos_ex = {p.id: p.nome for p in projetos}
                
                if tipo_exclusao == "O Projeto Completo (Catálogo e Turmas)":
                    proj_id = st.selectbox("Selecione o projeto para excluir:", options=list(opcoes_projetos_ex.keys()), format_func=lambda x: opcoes_projetos_ex[x], key="excluir_proj_completo")
                    st.warning("⚠️ Isso apagará o projeto, TODAS as suas turmas e desmatriculará os alunos vinculados.")
                    
                    if st.button("Excluir Projeto e Turmas"):
                        turmas = db.query(Turma).filter(Turma.projeto_id == proj_id).all()
                        ids_turmas = [t.id for t in turmas]
                        if ids_turmas:
                            db.query(Matricula).filter(Matricula.turma_id.in_(ids_turmas)).delete(synchronize_session=False)
                        db.query(Turma).filter(Turma.projeto_id == proj_id).delete()
                        db.query(Projeto).filter(Projeto.id == proj_id).delete()
                        db.commit()
                        st.success("Projeto excluído com sucesso.")
                        st.rerun()
                
                else:
                    proj_id = st.selectbox("Selecione o projeto:", options=list(opcoes_projetos_ex.keys()), format_func=lambda x: opcoes_projetos_ex[x], key="excluir_proj_turma")
                    turmas_do_proj = db.query(Turma).filter(Turma.projeto_id == proj_id).all()
                    
                    if not turmas_do_proj:
                        st.info("Este projeto não possui turmas cadastradas para excluir.")
                    else:
                        opcoes_turma_ex = {t.id: f"{t.nome_turma} ({t.ano_letivo})" for t in turmas_do_proj}
                        turma_id_ex = st.selectbox("Selecione a turma para excluir:", options=list(opcoes_turma_ex.keys()), format_func=lambda x: opcoes_turma_ex[x])
                        st.warning("⚠️ Isso apagará a turma e desmatriculará todos os alunos vinculados a ela.")
                        
                        if st.button("Excluir Apenas a Turma"):
                            db.query(Matricula).filter(Matricula.turma_id == turma_id_ex).delete(synchronize_session=False)
                            db.query(Turma).filter(Turma.id == turma_id_ex).delete()
                            db.commit()
                            st.success("Turma excluída com sucesso.")
                            st.rerun()

finally:
    db.close()