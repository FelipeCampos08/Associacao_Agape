import streamlit as st
import json
from datetime import date
from database import SessionLocal, Aluno

st.set_page_config(page_title="Cadastro de Alunos", page_icon="📝", layout="wide")

# --- PROTEÇÃO DE ACESSO ---
if "autenticado" not in st.session_state or not st.session_state.autenticado:
    st.warning("⚠️ Você precisa fazer login para acessar esta página.")
    st.stop() # Interrompe a leitura do código aqui e bloqueia a tela
# --------------------------

st.title("Cadastro de Alunos")

# Função para carregar o arquivo JSON
@st.cache_data
def carregar_campos():
    with open("config_campos.json", "r", encoding="utf-8") as f:
        return json.load(f)["cadastro_aluno"]

config = carregar_campos()

# Dicionário para guardar as respostas que o usuário digitar
respostas = {}

st.write("Preencha os dados abaixo. Campos marcados com * são obrigatórios.")

# Loop para gerar a interface dinamicamente lendo o JSON
for categoria, campos in config.items():
    st.markdown(f"### {categoria.replace('_', ' ').title()}")
    
    # Cria duas colunas para colocar os campos lado a lado
    cols = st.columns(2)
    
    for index, campo in enumerate(campos):
        nome = campo["nome"]
        label = campo["label"] + (" *" if campo.get("obrigatorio") else "")
        tipo = campo["tipo"]
        
        with cols[index % 2]:
            if tipo == "text":
                respostas[nome] = st.text_input(label, key=nome)
            elif tipo == "date":
                respostas[nome] = st.date_input(label, min_value=date(1990, 1, 1), max_value=date.today(), key=nome)
            elif tipo == "number":
                respostas[nome] = st.number_input(label, min_value=0.0, step=0.1, key=nome)
            elif tipo == "selectbox":
                respostas[nome] = st.selectbox(label, options=campo.get("opcoes", []), key=nome)
            elif tipo == "multiselect":
                respostas[nome] = st.multiselect(label, options=campo.get("opcoes", []), key=nome)
            elif tipo == "textarea":
                respostas[nome] = st.text_area(label, key=nome)
            elif tipo == "radio_com_detalhe":
                respostas[nome] = st.radio(label, options=["Não", "Sim"], key=nome, horizontal=True)
                if respostas[nome] == "Sim":
                    respostas[f"{nome}_detalhe"] = st.text_input(f"Especifique ({campo['label']}):", key=f"{nome}_detalhe")
    
    st.markdown("---")

# Botão de Salvar e Lógica de Banco de Dados
if st.button("Salvar Cadastro", type="primary"):
    erros = []
    
    # 1. Validação de campos obrigatórios
    for categoria, campos in config.items():
        for campo in campos:
            if campo.get("obrigatorio"):
                valor = respostas.get(campo["nome"])
                if valor is None or valor == "" or valor == []:
                    erros.append(campo["label"].replace(" *", ""))
                
                # Valida se o campo de detalhe do radio foi preenchido
                if campo["tipo"] == "radio_com_detalhe" and respostas.get(campo["nome"]) == "Sim":
                    if not respostas.get(f"{campo['nome']}_detalhe"):
                        erros.append(f"Detalhes de: {campo['label'].replace(' *', '')}")

    if erros:
        st.error(f"⚠️ Por favor, preencha os seguintes campos obrigatórios: {', '.join(erros)}")
    else:
        # 2. Verificação de Duplicidade no Banco de Dados
        db = SessionLocal()
        
        cpf_digitado = respostas.get("cpf", "").strip()
        nome_digitado = respostas.get("nome_completo", "").strip()
        data_nasc_digitada = respostas.get("data_nascimento")
        
        aluno_existente = None
        
        # Tenta achar por CPF se foi digitado, se não, busca por Nome + Data de Nascimento
        if cpf_digitado:
            aluno_existente = db.query(Aluno).filter(Aluno.cpf == cpf_digitado).first()
        
        if not aluno_existente:
            aluno_existente = db.query(Aluno).filter(
                Aluno.nome_completo == nome_digitado,
                Aluno.data_nascimento == data_nasc_digitada
            ).first()

        if aluno_existente:
            st.warning("❌ Este aluno já está cadastrado no sistema (combinação de CPF ou Nome + Data de Nascimento já existe).")
            db.close()
        else:
            # 3. Concluir Cadastro
            import json as json_lib
            
            rg_digitado = respostas.get("rg", "")
            
            # Converter a data para string para poder salvar o resto no JSON
            respostas_json_safe = respostas.copy()
            respostas_json_safe["data_nascimento"] = respostas_json_safe["data_nascimento"].strftime("%Y-%m-%d")
            dados_cadastrais_str = json_lib.dumps(respostas_json_safe, ensure_ascii=False)

            novo_aluno = Aluno(
                nome_completo=nome_digitado,
                data_nascimento=data_nasc_digitada,
                rg=rg_digitado,
                cpf=cpf_digitado,
                dados_cadastrais_json=dados_cadastrais_str
            )
            
            try:
                db.add(novo_aluno)
                db.commit()
                st.success(f"✅ Aluno(a) {nome_digitado} cadastrado com sucesso!")
            except Exception as e:
                db.rollback()
                st.error(f"Erro ao salvar no banco de dados: {e}")
            finally:
                db.close()