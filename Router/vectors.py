from fastapi import APIRouter ,Depends ,HTTPException ,status ,Path ,Request
from qdrant_client.http import models
from .auth import get_current_user
from .query import client
from typing import Annotated
from fastapi.templating import Jinja2Templates


router = APIRouter(prefix='/admin' , tags=['admin'])
templates = Jinja2Templates(directory="templates")
collection_name = "db1"
user_dependency=Annotated[dict,Depends(get_current_user)]


@router.get("/",status_code=status.HTTP_200_OK)
async def render_admin_dashboard(user:user_dependency , request:Request):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse("admin.html",{"request":request})


@router.get("/get_vector/",status_code=status.HTTP_200_OK)
async def get_all_vector_ids( user:user_dependency):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    all_ids = []
    next_page = None

    while True:
        response = client.scroll(
            collection_name=collection_name,
            limit=100,  # You can adjust the batch size
            with_payload=False,
            offset=next_page
        )

        points, next_page = response
        all_ids.extend([point.id for point in points])

        if next_page is None:
            break

    return {"count": len(all_ids),"ids":all_ids }

@router.get("/get_vector_by_id/{vector_id}",status_code=status.HTTP_200_OK)
async def get_vector_by_id(user:user_dependency , vector_id:str=Path(min_length=36,max_length=36)):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    response = client.retrieve(
        collection_name=collection_name,
        ids=[vector_id],
        with_payload=True,
        with_vectors=False
    )
    if response:
        payload = response[0].payload
        return payload.get('page_content', 'No page_content found')
    else:
        return f"Vector with ID '{vector_id}' not found."

@router.delete("/delete_vector/{vector_id}" ,status_code=status.HTTP_204_NO_CONTENT)
async def delete_vector_by_id(user:user_dependency , vector_id:str=Path(min_length=36,max_length=36)):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    response = client.retrieve(
        collection_name=collection_name,
        ids=[vector_id],
        with_payload=False,
        with_vectors=False
    )
    if not response:
        return (f"Vector ID '{vector_id}' not found in collection '{collection_name}'.")

    client.delete(
        collection_name=collection_name,
        points_selector=models.PointIdsList(
            points=[vector_id]
        )
    )
    return (f"Vector ID '{vector_id}' successfully deleted.")
