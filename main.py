from fastapi import FastAPI , Request ,HTTPException ,status
from databse import sessionLocal , Base ,engine
from Router import auth , home ,query , vectors
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse , JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware 


app = FastAPI()

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

origins = [
    "https://scasc.duckdns.org", 
    "http://localhost:3000", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(engine)

templates = Jinja2Templates(directory="templates")
app.mount("/static",StaticFiles(directory="static"),name="static")


def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

# API routing

@app.get("/")
async def welcome(request:Request):
    return templates.TemplateResponse("welcome.html", {"request":request})

@app.exception_handler(HTTPException)
async def auth_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401 and request.headers.get("accept", "").startswith("text/html"):
        return RedirectResponse(url="/auth/login-page", status_code=302)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

app.include_router(auth.router)
app.include_router(home.router)
app.include_router(query.router)
app.include_router(vectors.router)









