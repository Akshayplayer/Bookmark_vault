from fastapi import FastAPI, Depends, HTTPException
from database import Base,engine, get_db
from sqlalchemy.orm import Session
import schemas
import models
import auth
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine) 

@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/bookmarks",response_model=schemas.BookmarkOut, status_code=201)
def create_bookmark(data: schemas.BookmarkCreate, current_user: models.User = Depends(auth.get_current_user), db:Session=Depends(get_db)): # always place dependencies at the end and parameters at the first.
    bookmark = models.Bookmark(**data.model_dump(), owner_id=current_user.id)
    db.add(bookmark) # db.add() stages the change
    db.commit() #  db.commit() makes it permanent. Without the commit, nothing is saved.
    db.refresh(bookmark)
    return bookmark

@app.get("/bookmarks",response_model=list[schemas.BookmarkOut])
def list_bookmarks( tag: str | None = None, q: str | None = None, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    query = db.query(models.Bookmark).filter(models.Bookmark.owner_id == current_user.id)
    if tag:
        query = query.filter(models.Bookmark.tag == tag)
    if q:
        query = query.filter(models.Bookmark.title.ilike(f"%{q}%"))
    query = query.order_by(models.Bookmark.created_at.desc())
    return query.all()


@app.get("/bookmarks/{bookmark_id}",response_model=schemas.BookmarkOut) # {bookmark_id} in the URL is a path parameter, and FastAPI passes it in as a function argument.
def get_bookmark(bookmark_id:int, current_user: models.User = Depends(auth.get_current_user), db:Session=Depends(get_db)):
    bookmark= db.get(models.Bookmark, bookmark_id)
    if not bookmark or bookmark.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return bookmark

@app.put("/bookmarks/{bookmark_id}",response_model=schemas.BookmarkOut)
def update_bookmark(bookmark_id:int, data: schemas.BookmarkUpdate, current_user: models.User = Depends(auth.get_current_user), db:Session=Depends(get_db)):
    bookmark= db.get(models.Bookmark, bookmark_id)
    if not bookmark or bookmark.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    required = {"title", "url"}
    for key, value in data.model_dump(exclude_unset=True).items():
        if value is None and key in required:
            continue
        setattr(bookmark, key, value)
    db.commit()
    db.refresh(bookmark)
    return bookmark



@app.delete("/bookmarks/{bookmark_id}",status_code=204)
def delete_bookmark(bookmark_id:int, current_user: models.User = Depends(auth.get_current_user), db:Session=Depends(get_db)):
    bookmark= db.get(models.Bookmark, bookmark_id)
    if not bookmark or bookmark.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    db.delete(bookmark)
    db.commit()
        

@app.post("/register",response_model=schemas.UserOut, status_code=201)
def register_user(data: schemas.UserCreate, db:Session=Depends(get_db)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400,detail="Email already registered")
    user=models.User(email=data.email,hashed_password=auth.hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login",response_model=schemas.Token)
def login(form:OAuth2PasswordRequestForm=Depends(), db: Session = Depends(get_db)):
    user=db.query(models.User).filter(models.User.email==form.username).first()
    if not user or not auth.verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token=auth.create_access_token(user.id)
    return {"access_token":token, "token_type":"bearer"}