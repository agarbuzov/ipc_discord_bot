from sqlalchemy import Text
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import BigInteger
from sqlalchemy import UniqueConstraint
from sqlalchemy import create_engine

from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy.orm import Session

from sqlalchemy.sql import func

from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///discord.db', echo=True)
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


class Playlist(Base):
    __tablename__ = 'playlist'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    guild_id = Column(Integer)
    creator = Column(String)
    tracks = relationship("Track", backref=backref("playlist"), cascade="all,delete")
    __table_args__ = (UniqueConstraint('name', 'guild_id', name='_playlist_guild_id_uc'),)


class Track(Base):
    __tablename__ = 'track'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    creator = Column(String)
    duration = Column(Integer)
    playlist_id = Column(Integer, ForeignKey("playlist.id"))


class History(Base):
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True)
    track = Column(String)
    type = Column(String)
    date = Column(DateTime(timezone=True), server_default=func.now())
    url = Column(String)
    user_id = Column(BigInteger, ForeignKey('user.id'))
    user = relationship("User")
