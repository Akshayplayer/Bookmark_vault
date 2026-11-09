from datetime import datetime
from pydantic import BaseModel, Field, field_validator, EmailStr


# What the client SENDS to create a bookmark.
# No id or created_at: the database generates those.
class BookmarkCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=1, max_length=2000)
    note: str | None = Field(default=None, max_length=255)   # "= None" makes the field optional
    tag: str | None = Field(default=None, max_length=255)
    @field_validator("url")
    @classmethod
    def add_scheme(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            return "https://" + v
        return v



# What the client SENDS to edit a bookmark.
# Everything is optional, so they can change just one field.
class BookmarkUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    url: str | None = Field(default=None, min_length=1, max_length=2000)
    note: str | None = Field(default=None, max_length=255)
    tag: str | None = Field(default=None, max_length=255)
    @field_validator("url")
    @classmethod
    def add_scheme(cls, v: str) -> str:
        if v is None:
            return v
        if not v.startswith(("http://", "https://")):
            return "https://" + v
        return v


# What the API SENDS BACK.
# Includes the database-generated fields.
class BookmarkOut(BaseModel):
    id: int
    title: str
    url: str
    note: str | None
    tag: str | None
    created_at: datetime
    owner_id: int

    # Lets Pydantic read a SQLAlchemy object (models.Bookmark), not only a dict.
    model_config = {"from_attributes": True} # Without it, returning a database object from an endpoint fails, because Pydantic expects a dict.


class UserCreate(BaseModel):
    email: EmailStr
    password:str=Field(min_length=8)
    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()


class UserOut(BaseModel):
    id:int
    email:EmailStr

class Token(BaseModel):
    access_token:str
    token_type:str