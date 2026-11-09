from datetime import datetime
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    email:Mapped[str]=mapped_column(String(255), unique=True)
    hashed_password:Mapped[str]=mapped_column(String(255))
    bookmarks:Mapped[list["Bookmark"]]=relationship(back_populates="owner")

class Bookmark(Base):
    __tablename__="bookmarks"
    id:Mapped[int]=mapped_column(primary_key=True)
    title:Mapped[str]=mapped_column(String(200))
    url:Mapped[str]=mapped_column(String(2000))
    note:Mapped[str | None]=mapped_column(String(255))
    tag:Mapped[str | None]=mapped_column(String(255))
    created_at:Mapped[datetime]=mapped_column(server_default=func.now())
    owner_id:Mapped[int]=mapped_column(ForeignKey("users.id"))

    owner:Mapped["User"]=relationship(back_populates="bookmarks")
