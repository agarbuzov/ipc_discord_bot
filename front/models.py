from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy import BigInteger
from sqlalchemy import create_engine

from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session

from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///users.db', echo=True)
Base = declarative_base()
session = Session(bind=engine)


class User(Base):
    __tablename__ = 'user'
    id = Column(BigInteger, primary_key=True)
    username = Column(String(255))
    discriminator = Column(Integer)
    avatar = Column(String)
    avatar_decoration = Column(String)
    locale = Column(String(2))


class UserSession(Base):
    __tablename__ = 'user_session'
    session = Column(Text, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('user.id'))
    user = relationship("User")
