from sqlalchemy.sql.sqltypes import DateTime
from datetime import datetime
import sqlalchemy

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

metadata = sqlalchemy.MetaData()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True)
    phone_number = Column(Integer, unique=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=False)

    videos = relationship("Video", back_populates="owner")


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    video = Column(String)
    title = Column(String, index=True)
    description = Column(String, index=True)
    created = Column(DateTime, default=datetime.now())
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="videos")
