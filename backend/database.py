import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL) #engine is the connection manager. It holds a pool of connections to Postgres, and you create exactly one.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # engine is the connection manager. It holds a pool of connections to Postgres, and you create exactly one.
class Base(DeclarativeBase): # Base is the parent class of all your models. When SQLAlchemy sees a class inheriting from it, it knows that class is a table.
    pass

def get_db(): # get_db() opens a session, hands it to whoever asked (yield), and closes it afterward even if an error happened. FastAPI will call this automatically for each request. That pattern is called dependency injection
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()