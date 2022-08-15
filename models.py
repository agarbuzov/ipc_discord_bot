from flask import url_for

from sqlalchemy import Text
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import Integer
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import BigInteger
from sqlalchemy import LargeBinary
from sqlalchemy import UniqueConstraint
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy.orm import Session

from sqlalchemy.sql import func

from sqlalchemy.ext.declarative import declarative_base

engine = create_engine("sqlite:///discord.db", connect_args={"check_same_thread": False},
                       poolclass=StaticPool, echo=False)
Base = declarative_base()
session = Session(bind=engine)


class UserGuild(Base):
    __tablename__ = 'user_guild'
    guild_id = Column(ForeignKey("guild.id"), primary_key=True)
    user_id = Column(ForeignKey("user.id"), primary_key=True)


class User(Base):
    __tablename__ = 'user'
    id = Column(BigInteger, primary_key=True)
    username = Column(String)
    avatar = Column(String)
    avatar_decoration = Column(String)
    discriminator = Column(Integer)
    public_flags = Column(Integer)
    flags = Column(Integer)
    banner = Column(Integer)
    banner_color = Column(String)
    accent_color = Column(String)
    locale = Column(String(2))
    mfa_enabled = Column(Boolean)
    guilds = relationship("Guild", secondary='user_guild')

    def get_icon_url(self):
        url = f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png?size=64" if self.avatar else url_for(
            "static", filename="img/default_avatar.jpg")
        return url


class Guild(Base):
    __tablename__ = 'guild'
    id = Column(BigInteger, primary_key=True)
    name = Column(String(255))


class UserSession(Base):
    __tablename__ = 'user_session'
    user_id = Column(BigInteger, ForeignKey('user.id'))
    user = relationship("User")
    access_token = Column(String, primary_key=True)
    expires_in = Column(DateTime)
    token_type = Column(String)
    scope = Column(String)
    refresh_token = Column(String)


class Playlist(Base):
    __tablename__ = 'playlist'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    cover = Column(Text)
    cover_type = Column(String)
    creator_id = Column(BigInteger, ForeignKey("user.id"))
    creator = relationship("User")
    tracks = relationship("Track", backref=backref("playlist"), cascade="all,delete")


class Track(Base):
    __tablename__ = 'track'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
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


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    identifier = Column(String)
    platform = Column(String)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    broadcaster_id = Column(BigInteger)
    body = Column(String)
    creator_id = Column(BigInteger, ForeignKey('user.id'))
    creator = relationship("User")
    __table_args__ = (
        UniqueConstraint("broadcaster_id", "guild_id", "channel_id"),
    )
