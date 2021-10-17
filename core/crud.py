from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import redis
import json

from starlette.status import HTTP_404_NOT_FOUND

from passlib.context import CryptContext
from jose import JWTError, jwt

from . import models, schemas
from . import send_email
from tasks import send_mail


SECRET_KEY = 'aaff0953f14077534f5cea536f32487d2e07253a3254873f8b30e4d0e4468863'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_id(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id)
    return db_user


def get_users(db: Session, skip: int = 0, limit: int = 100):
    redis_client = redis.Redis()
    cache = redis_client.get('users')
    if cache:
        redis_client.close()
        return json.loads(cache)
    users = []
    for user in db.query(models.User).offset(skip).limit(limit).all():
        user = user.__dict__
        user.pop('_sa_instance_state')
        users.append(user)
    redis_client.set('users', json.dumps(users), ex=120)
    redis_client.close()
    return users


async def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.hashed_password)
    db_user = models.User(email=user.email, hashed_password=hashed_password, username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # await send_email.send_email_async(user.email, 'Successfully created')
    # await send_mail.delay(user.email, 'Successfully created')
    return db_user


def update_user(db: Session, user_id: int, user):
    db_user = db.query(models.User).filter(models.User.username==user.username).first()
    if db_user:
        if not db_user.id == user_id:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='User with such username already exists')
    db_user = db.query(models.User).filter(models.User.email==user.email).first()
    if db_user:
        if not db_user.id == user_id:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='User with such username already exists')
    user_to_update = db.query(models.User).filter(models.User.id==user_id).first()
    user_to_update.email = user.email
    user_to_update.username = user.username
    user_to_update.phone_number = user.phone_number
    db.commit()
    return user_to_update


def delete_user(db: Session, db_user):
    db.delete(db_user)
    db.commit()
    return db_user


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_videos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Video).offset(skip).limit(limit).all()


def get_video(db: Session, vid_id: int):
    return db.query(models.Video).filter(models.Video.id == vid_id).first()


def create_user_video(db: Session, video: schemas.VideoCreate, user_id: int):
    db_video = models.Video(**video, owner_id=user_id)
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    
    return db_video


def delete_video(db: Session, video):
    db.delete(video)
    db.commit()
    return video


def get_user(db, username: str):
    db_users = db.query(models.User).all()
    for db_user in db_users:
        if db_user.username == username:
            return db_user


def create_access_token(data: dict):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.now() + timedelta(days=7)})
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(db, token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user