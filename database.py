from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine

engine = create_engine("sqlite:///data.db")
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

    def __repr__(self) -> str:
        return f'User({self.amino_profileid})'

# Non-data related class
class ActiveUser:
    def __init__(self, userid, signature) -> None:
        self.userid = userid
        self.signature = signature
        

if __name__ == "__main__":
    Base.metadata.create_all(engine)

