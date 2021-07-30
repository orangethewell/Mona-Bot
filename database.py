from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import create_engine
import datetime, os

engine = create_engine(os.environ["DATABASE_URI"], echo=True)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    amino_profile_id = Column(String)
    entrypoint_id = Column(String)
    amino_coins_count = Column(Integer)
    last_tip_max_count = Column(Integer)
    signature = Column(String)
    password = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow())

    def __repr__(self) -> str:
        return f'User({self.amino_profileid})'

class Admin(Base):
    __tablename__ = 'admin'

    id = Column(Integer, primary_key=True)
    amino_profile_id = Column(String)
    privileges_level = Column(Integer)

# Non-data related class
class ActiveUser:
    def __init__(self, userid, signature) -> None:
        self.userid = userid
        self.signature = signature
        

if __name__ == "__main__":
    Admin.__table__.create(engine)
    User.__table__.create(engine)

