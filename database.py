from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, Date, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime

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
    status_ativo = Column(Boolean, default=True, nullable=False) 
    dados_cadastrais_json = Column(Text, nullable=False) 
    
    matriculas = relationship("Matricula", back_populates="aluno")

class Projeto(Base):
    __tablename__ = 'projetos'
    
    # O Projeto agora é apenas um "Guarda-chuva" (Catálogo)
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False, unique=True)
    descricao = Column(Text)
    local = Column(String)
    
    turmas = relationship("Turma", back_populates="projeto")

class Turma(Base):
    __tablename__ = 'turmas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    projeto_id = Column(Integer, ForeignKey('projetos.id'))
    nome_turma = Column(String, nullable=False)
    horario = Column(String, nullable=False)
    vagas_totais = Column(Integer, nullable=False)
    ano_letivo = Column(Integer, default=datetime.date.today().year, nullable=False)
    
    # Dados do Professor desceram para a Turma (Execução Anual)
    nome_professor = Column(String, nullable=False)
    cpf_professor = Column(String)
    remuneracao_professor = Column(Float, nullable=True)
    
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

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    senha = Column(String, nullable=False)
    
    # NOVO: Define se o usuário tem privilégios de administrador
    is_admin = Column(Boolean, default=False, nullable=False)

# Comando para criar as tabelas
Base.metadata.create_all(engine)