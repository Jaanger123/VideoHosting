from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class VideoBase(BaseModel):
    title: str
    description: Optional[str] = None


class VideoCreate(VideoBase):
    pass


class Video(VideoBase):
    id: int
    video: str
    created: datetime
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str
    username: str


class UserCreate(UserBase):
    hashed_password: str


class User(UserBase):
    id: int
    is_active: bool
    hashed_password: str
    videos: List[Video] = []

    class Config:
        orm_mode = True


class UserUpdate(UserBase):
    phone_number: str