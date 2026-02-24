from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, Date
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Cria o banco de dados local chamado 'agape.db'
engine = create_engine('sqlite:///agape.db', echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# --- TABELAS ---

class Aluno(Base):
    __tablename__ = 'alunos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_completo = Column(String, nullable=False)
    data_nascimento = Column(Date, nullable=False)
    rg = Column(String)
    cpf = Column(String)
    
    # Vamos armazenar todos os dados adicionais do formulário JSON como uma string (ou JSON nativo) 
    # para não precisarmos criar 30 colunas na tabela. Isso dá flexibilidade!
    dados_cadastrais_json = Column(Text, nullable=False) 
    
    matriculas = relationship("Matricula", back_populates="aluno")

class Projeto(Base):
    __tablename__ = 'projetos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False, unique=True)
    descricao = Column(Text)
    local = Column(String)
    
    # Dados do Professor responsável
    nome_professor = Column(String)
    cpf_professor = Column(String)
    remuneracao_professor = Column(Float, nullable=True) # Se for voluntário, fica nulo ou 0
    
    turmas = relationship("Turma", back_populates="projeto")

class Turma(Base):
    __tablename__ = 'turmas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    projeto_id = Column(Integer, ForeignKey('projetos.id'))
    nome_turma = Column(String, nullable=False) # Ex: Turma Manhã 1
    horario = Column(String, nullable=False)
    vagas_totais = Column(Integer, nullable=False)
    
    projeto = relationship("Projeto", back_populates="turmas")
    matriculas = relationship("Matricula", back_populates="turma")

class Matricula(Base):
    __tablename__ = 'matriculas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    aluno_id = Column(Integer, ForeignKey('alunos.id'))
    turma_id = Column(Integer, ForeignKey('turmas.id'))
    data_matricula = Column(Date, nullable=False)
    
    aluno = relationship("Aluno", back_populates="matriculas")
    turma = relationship("Turma", back_populates="matriculas")

# Comando para criar as tabelas no arquivo agape.db
Base.metadata.create_all(engine)