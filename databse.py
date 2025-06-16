from sqlalchemy import create_engine ,Column ,String ,Boolean ,Integer 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# DATABASE SETUP

DATABASE_URL = 'postgresql://postgres:Test123@localhost/Project1' 
engine = create_engine(DATABASE_URL)
sessionLocal = sessionmaker(autocommit=False , autoflush=False, bind = engine)
Base = declarative_base()


# DATABSE MODEl

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer , primary_key=True, index=True)
    username = Column(String ,unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_pwd = Column(String)
    is_active =Column(Boolean , default=True)
    role = Column(String)

