import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Always load .env from the project root
project_root = os.path.dirname(os.path.dirname(__file__))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

POSTGRES_DSN = os.getenv('POSTGRES_DSN')
print("POSTGRES_DSN:", repr(POSTGRES_DSN))  # <--- Add this line

engine = create_engine(POSTGRES_DSN, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()