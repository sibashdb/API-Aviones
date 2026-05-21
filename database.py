import os
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Generator

# Cargar las variables del archivo .env (solo para desarrollo local)
load_dotenv()

# Leer las variables de entorno de forma segura
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Configurar el motor de la base de datos
engine = create_engine(DATABASE_URL, echo=True)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Inicializar el cliente de almacenamiento de Supabase
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY) 