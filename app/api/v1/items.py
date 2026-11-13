# app/api/v1/items.py
from typing import Annotated
from fastapi import APIRouter, Query, status
from app.api.deps import DBSession, ItemServiceDep, CurrentUser
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse, PaginatedItems

router = APIRouter()

@router.post(
    "/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new item"
)
async def create_item(
    payload: ItemCreate,
    service: ItemServiceDep,
) -> ItemResponse:
    return await service.create_item(payload)

@router.get(
    "/",
    response_model=PaginatedItems,
    summary="List items with pagination"
)
async def list_items(
    service: ItemServiceDep,
    offset: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max records to return")] = 100,
) -> PaginatedItems:
    return await service.list_items(offset=offset, limit=limit)

@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Get an item by ID"
)
async def get_item(
    item_id: int,
    service: ItemServiceDep,
) -> ItemResponse:
    return await service.get_item(item_id)

@router.patch(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Update an item"
)
async def update_item(
    item_id: int,
    payload: ItemUpdate,
    service: ItemServiceDep,
    current_user: CurrentUser,
) -> ItemResponse:
    return await service.update_item(item_id, payload)

@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an item"
)
async def delete_item(
    item_id: int,
    service: ItemServiceDep,
    current_user: CurrentUser,
) -> None:
    await service.delete_item(item_id)