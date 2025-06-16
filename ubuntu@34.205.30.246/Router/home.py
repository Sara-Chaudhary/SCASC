from fastapi import APIRouter ,status ,UploadFile ,Depends ,HTTPException ,Request ,File
from fastapi.responses import JSONResponse ,RedirectResponse
from .auth import get_current_user
from typing import Annotated
from fastapi.templating import Jinja2Templates
from tempfile import NamedTemporaryFile
import shutil
import redis
from celery.result import AsyncResult
from .task import make_qdrant
from celery_app import celery


router = APIRouter(prefix='/home',tags=['home'])

user_dependency=Annotated[dict,Depends(get_current_user)]

templates = Jinja2Templates(directory="templates")

redis_conn = redis.Redis(host='localhost' , port=6379 )


# Page render
@router.get("/" , status_code=status.HTTP_200_OK)
async def render_home_page(user:user_dependency,request:Request):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    if user['role'] == 'admin':
        return RedirectResponse(url="/admin/", status_code=302)
    else:
        return RedirectResponse(url="/home/user", status_code=302)
    
@router.get("/user")
async def user_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
    
    
# api to upload pdf
@router.post("/uploadfiles", status_code=status.HTTP_201_CREATED)  
async def upload_pdf(user:Annotated[dict,Depends(get_current_user)] ,file: UploadFile = File(...)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    if not file.filename.endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Only PDF files are supported."})

    try:
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name
        # Send task to Celery
        task = make_qdrant.delay(tmp_file_path)
        return {"message": "Processing started", "task_id": task.id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
def get_status(user:user_dependency,task_id: str):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    result = AsyncResult(task_id, app=celery)
    return {
        "task_id": task_id,
        "state": result.state,
        "result": result.result
    }

    