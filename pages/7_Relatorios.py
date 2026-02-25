import streamlit as st
import json
import datetime
from fpdf import FPDF
from database import SessionLocal, Aluno, Projeto, Turma, Matricula

st.set_page_config(page_title="Relatórios e Documentos", page_icon="🖨️", layout="wide")
st.title("🖨️ Gerador de Relatórios Oficiais")
st.write("Gere relatórios completos em PDF para impressão e arquivamento físico.")

db = SessionLocal()

# --- CLASSE PARA FORMATAR O PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 14)
        self.cell(0, 10, "Relatório Anual - Ágape Missões Urbanas", border=False, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("helvetica", "I", 10)
        self.cell(0, 10, f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}", border=False, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C", new_x="LMARGIN", new_y="NEXT")

try:
    ano_atual = datetime.date.today().year
    
    st.markdown("---")
    st.subheader("Configuração do Relatório")
    ano_selecionado = st.number_input("Selecione o Ano Letivo para o relatório:", min_value=2024, max_value=2100, value=ano_atual, step=1)

    if st.button("Gerar Relatório em PDF", type="primary"):
        with st.spinner("Compilando dados e gerando o PDF... Isso pode levar alguns segundos."):
            
            # --- BUSCA DOS DADOS ---
            turmas_do_ano = db.query(Turma).filter(Turma.ano_letivo == ano_selecionado).all()
            ids_turmas = [t.id for t in turmas_do_ano]
            matriculas_do_ano = db.query(Matricula).filter(Matricula.turma_id.in_(ids_turmas)).all() if ids_turmas else []
            alunos_todos = db.query(Aluno).all()
            projetos_todos = db.query(Projeto).all()
            
            alunos_ativos = [a for a in alunos_todos if a.status_ativo]
            alunos_matriculados_ids = set([m.aluno_id for m in matriculas_do_ano])

            # --- INICIALIZA O PDF ---
            pdf = PDF()
            pdf.add_page()
            
            # ==========================================
            # SEÇÃO 1: ESTATÍSTICAS GERAIS
            # ==========================================
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, f"Estatísticas Gerais - Ano Letivo {ano_selecionado}", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(10)
            
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 8, f"Total de Alunos Cadastrados na Base (Ativos): {len(alunos_ativos)}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"Total de Alunos Diferentes Matriculados neste Ano: {len(alunos_matriculados_ids)}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"Total de Turmas Abertas neste Ano: {len(turmas_do_ano)}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"Total de Matrículas (Vagas ocupadas): {len(matriculas_do_ano)}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(10)

            # ==========================================
            # SEÇÃO 2: PROJETOS E LISTAS DE CHAMADA
            # ==========================================
            if not turmas_do_ano:
                pdf.add_page()
                pdf.set_font("helvetica", "B", 14)
                pdf.cell(0, 10, "Nenhuma turma cadastrada para este ano letivo.", new_x="LMARGIN", new_y="NEXT")
            else:
                for projeto in projetos_todos:
                    turmas_deste_projeto = [t for t in turmas_do_ano if t.projeto_id == projeto.id]
                    
                    for turma in turmas_deste_projeto:
                        pdf.add_page() 
                        pdf.set_font("helvetica", "B", 16)
                        pdf.cell(0, 10, f"Projeto: {projeto.nome}", new_x="LMARGIN", new_y="NEXT")
                        pdf.set_font("helvetica", "", 12)
                        
                        # Adicionado new_x e new_y aqui
                        pdf.multi_cell(0, 8, txt=f"Descrição: {projeto.descricao}", new_x="LMARGIN", new_y="NEXT")
                        pdf.cell(0, 8, f"Local: {projeto.local}", new_x="LMARGIN", new_y="NEXT")
                        pdf.ln(5)
                        
                        pdf.set_font("helvetica", "B", 14)
                        pdf.cell(0, 10, f"Turma: {turma.nome_turma} | Horário: {turma.horario}", new_x="LMARGIN", new_y="NEXT")
                        pdf.set_font("helvetica", "", 12)
                        pdf.cell(0, 8, f"Professor(a): {turma.nome_professor}", new_x="LMARGIN", new_y="NEXT")
                        pdf.ln(5)
                        
                        pdf.set_font("helvetica", "B", 12)
                        pdf.cell(0, 10, "Lista de Chamada (Alunos Matriculados):", new_x="LMARGIN", new_y="NEXT")
                        pdf.set_font("helvetica", "", 11)
                        
                        matriculas_desta_turma = [m for m in matriculas_do_ano if m.turma_id == turma.id]
                        if not matriculas_desta_turma:
                            pdf.cell(0, 8, "Nenhum aluno matriculado nesta turma.", new_x="LMARGIN", new_y="NEXT")
                        else:
                            for idx, m in enumerate(matriculas_desta_turma):
                                aluno_mat = next((a for a in alunos_todos if a.id == m.aluno_id), None)
                                if aluno_mat:
                                    dados_json = json.loads(aluno_mat.dados_cadastrais_json)
                                    contato = dados_json.get("contato_resp1", "Sem contato")
                                    resp = dados_json.get("nome_resp1", "Sem responsável")
                                    
                                    linha = f"{idx + 1}. {aluno_mat.nome_completo} | Resp: {resp} | Contato: {contato}"
                                    pdf.cell(0, 8, linha, new_x="LMARGIN", new_y="NEXT")

            # ==========================================
            # SEÇÃO 3: DADOS DE TODOS OS ALUNOS
            # ==========================================
            if alunos_ativos:
                pdf.add_page()
                pdf.set_font("helvetica", "B", 16)
                pdf.cell(0, 10, "Fichas Cadastrais - Todos os Alunos Ativos", new_x="LMARGIN", new_y="NEXT", align="C")
                pdf.ln(10)
                
                for aluno in alunos_ativos:
                    # Garantir que o cursor volte para a margem esquerda por segurança extra
                    pdf.set_x(pdf.l_margin) 
                    
                    pdf.set_font("helvetica", "B", 12)
                    pdf.cell(0, 8, f"Nome: {aluno.nome_completo}", new_x="LMARGIN", new_y="NEXT")
                    
                    pdf.set_font("helvetica", "", 10)
                    pdf.cell(0, 6, f"Data Nasc.: {aluno.data_nascimento.strftime('%d/%m/%Y')} | CPF: {aluno.cpf if aluno.cpf else 'N/A'}", new_x="LMARGIN", new_y="NEXT")
                    
                    dados_json = json.loads(aluno.dados_cadastrais_json)
                    
                    endereco = f"{dados_json.get('endereco', '')}, {dados_json.get('numero', '')} - {dados_json.get('bairro', '')}"
                    escola = f"{dados_json.get('nome_escola', '')} ({dados_json.get('periodo', '')})"
                    vulnerabilidades = ", ".join(dados_json.get('vulnerabilidades', []))
                    saude = f"Medicação Contínua: {dados_json.get('medicacao_continua', 'Não')}"
                    
                    # CORREÇÃO: Usando new_x e new_y nativos no multi_cell para evitar o erro de layout
                    pdf.multi_cell(0, 6, txt=f"Endereço: {endereco}", new_x="LMARGIN", new_y="NEXT")
                    pdf.multi_cell(0, 6, txt=f"Escola: {escola}", new_x="LMARGIN", new_y="NEXT")
                    pdf.multi_cell(0, 6, txt=f"Vulnerabilidades Mapeadas: {vulnerabilidades}", new_x="LMARGIN", new_y="NEXT")
                    pdf.multi_cell(0, 6, txt=f"Saúde: {saude}", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(5)

            # --- GERAÇÃO FINAL DO ARQUIVO ---
            pdf_bytes = pdf.output()
            
            st.success("✅ Relatório gerado com sucesso!")
            
            st.download_button(
                label="📥 Baixar Relatório (PDF)",
                data=bytes(pdf_bytes),
                file_name=f"Relatorio_Agape_{ano_selecionado}.pdf",
                mime="application/pdf",
                type="primary"
            )

finally:
    db.close()