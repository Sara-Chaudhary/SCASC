from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request ,Response
from pydantic import BaseModel, Field
from databse import sessionLocal, Users
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError
from fastapi.templating import Jinja2Templates 
from fastapi.responses import JSONResponse ,RedirectResponse
from fastapi.security.utils import get_authorization_scheme_param


router = APIRouter(prefix="/auth", tags=["auth"])


# Hashing and Token Requiremnts
SECRET_KEY = "af7c0b6a5a72eb8dfc25408397f2c02909e8faffc2d4c3e530cf7587a37dfe0d"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def oauth2_bearer(request: Request):
    # 1. Try Authorization header
    auth: str = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(auth)

    if scheme.lower() == "bearer" and param:
        return param

    # 2. Try cookie fallback
    token = request.cookies.get("access_token")
    if token:
        return token

    raise HTTPException(status_code=401, detail="Not authenticated")


# Pydantic models
class Create_User_Request(BaseModel):
    username: str
    first_name: str
    last_name: str
    pwd: str
    role: str = Field(default="user")

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "user123",
                "first_name": "Sara",
                "last_name": "Chaudhary",
                "pwd": "test123",
                "role": "user",
            }
        }
    }


class Token(BaseModel):
    access_token: str
    token_type: str


# Open db session
def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

templates = Jinja2Templates(directory="templates")


# webpages


@router.get("/login-page")
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register-page")
def render_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# API endpoints


def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_pwd):
        return False
    return user


def create_access_token(
    username: str, user_id: int, user_role: str, expires_delta: timedelta
):
    encode = {"sub": username, "id": user_id, "role": user_role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")


        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="could not validate user",
            )
        return {"username": username, "id": user_id, "role": user_role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="could not validate user"
        )


# APIs


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_req: Create_User_Request):
    create_user_model = Users(
        username=create_user_req.username,
        first_name=create_user_req.first_name,
        last_name=create_user_req.last_name,
        hashed_pwd=bcrypt_context.hash(create_user_req.pwd),
        is_active=True,
        role=create_user_req.role,
    )
    db.add(create_user_model)
    db.commit()
    return {"username": create_user_req.username, "password": create_user_req.pwd}


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
):
    try:
        user = authenticate_user(form_data.username, form_data.password, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user",
            )
        token = create_access_token(
            user.username, user.id, user.role, timedelta(minutes=30)
        )
        response = JSONResponse(content={"access_token": token, "token_type": "bearer"})

        # Set token as cookie
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=1800,
            path="/"
        )

        return response

    except Exception as e:
        import traceback

        traceback.print_exc()  # for terminal logs
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
@router.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response