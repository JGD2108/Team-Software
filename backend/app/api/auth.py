from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_admin
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.common import LoginIn, Token, UserCreate, UserOut, UserUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])


@router.post("/login", response_model=Token)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_access_token(user.email, user.role)
    log_action(db, user, "user", "login", user.id)
    db.commit()
    return {"access_token": token, "user": user}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@users_router.get("", response_model=list[UserOut])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.name).all()


@users_router.post("", response_model=UserOut)
def create_user(payload: UserCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if payload.role not in {"admin", "plant_user"}:
        raise HTTPException(status_code=400, detail="Rol inválido")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="El email ya existe")
    user = User(name=payload.name.strip(), email=payload.email.strip(), role=payload.role, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    log_action(db, admin, "user", "create", user.id, after={"email": user.email, "role": user.role})
    db.commit()
    db.refresh(user)
    return user


@users_router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if payload.role is not None and payload.role not in {"admin", "plant_user"}:
        raise HTTPException(status_code=400, detail="Rol inválido")
    if payload.email is not None and payload.email != user.email and db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="El email ya existe")
    before = {"name": user.name, "email": user.email, "role": user.role, "is_active": user.is_active}
    if payload.name is not None:
        user.name = payload.name.strip()
    if payload.email is not None:
        user.email = payload.email.strip()
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.password_hash = hash_password(payload.password)
    log_action(db, admin, "user", "update", user.id, before=before, after={"name": user.name, "email": user.email, "role": user.role, "is_active": user.is_active})
    db.commit()
    db.refresh(user)
    return user


@users_router.patch("/{user_id}/activate", response_model=UserOut)
def activate_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.is_active = True
    log_action(db, admin, "user", "activate", user.id)
    db.commit()
    db.refresh(user)
    return user


@users_router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.is_active = False
    log_action(db, admin, "user", "deactivate", user.id)
    db.commit()
    db.refresh(user)
    return user
