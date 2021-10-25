from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, status, BackgroundTasks
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from core import models, schemas, crud, send_email
from core.database import SessionLocal, engine

import shutil, os
from typing import List
from tasks import send_mail


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Email already registered")
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Username already registered")
    return await crud.create_user(db=db, user=user)


@app.get("/users/")
def read_users(skip: int = 0, limit: int = 100, token: str = Depends(crud.oauth2_scheme), db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/me/")
async def read_me(token: str = Depends(crud.oauth2_scheme), db: Session = Depends(get_db)):
    current_user = await crud.get_current_user(db, token)
    return current_user


@app.put("/users/me/")
async def update_profile(user: schemas.UserUpdate, token: str = Depends(crud.oauth2_scheme), db: Session = Depends(get_db)):
    current_user = await crud.get_current_user(db, token)
    updated_user = crud.update_user(db, current_user.id, user)
    return updated_user


@app.get("/users/{user_id}/", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    return db_user


@app.delete('/users/{user_id}/', response_model=schemas.User)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    crud.delete_user(db, db_user)
    return db_user


@app.post('/users/{user_id}/videos/')
async def create_video(user_id: int,title: str, desc: str = None, token: str = Depends(crud.oauth2_scheme), file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not db.query(models.User).filter(models.User.id == user_id).first():
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")

    with open(f'media/{user_id}_{file.filename}', 'wb') as folder:
        shutil.copyfileobj(file.file, folder)

    video = {"title": title, "description": desc, "video": file.filename}
    crud.create_user_video(db, video, user_id)
    return 'Successfully created'


@app.get("/videos/", response_model=List[schemas.Video])
def read_videos(search: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    search_result = []
    videos = crud.get_videos(db, skip=skip, limit=limit)
    if search:
        for video in videos:
            if search.lower() in video.title.lower():
                search_result.append(video)
        return search_result
    return videos


@app.get("/videos/{vid_id}/", response_model=schemas.Video)
def read_video(vid_id: int, db: Session = Depends(get_db)):
    video = crud.get_video(db, vid_id)
    if not video:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Video not found")
    return video


@app.delete('/users/{user_id}/videos/{vid_id}/', response_model=schemas.Video)
def delete_video(user_id: int, vid_id: int, token: str = Depends(crud.oauth2_scheme), db: Session = Depends(get_db)):
    if not db.query(models.User).filter(models.User.id == user_id).first():
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    if not db.query(models.Video).filter(models.Video.id == vid_id).first():
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Video not found")
    video = db.query(models.Video).filter(models.Video.id == vid_id).first()
    if video.owner_id != user_id:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="You don't have permission")

    crud.delete_video(db, video)
    os.remove(f'media/{user_id}_{video.video}')
    return video


@app.post("/token/")
async def login(form_data: crud.OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = crud.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get('/send-email/asynchronous')
async def send_email_asynchronous():
    # await send_email.send_email_async('jbarakanov@gmail.com',
    # 'test')
    await send_mail('jbarakanov@gmail.com', 'Successfully created')
    return 'Success'