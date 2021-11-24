from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy import create_engine

from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy.orm import Session

from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///playlists.db', echo=True)
Base = declarative_base()
session = Session(bind=engine)


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
