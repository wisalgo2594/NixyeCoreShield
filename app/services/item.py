from __future__ import annotations

import math
from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Item
from app.schemas.item import ItemCreate, ItemUpdate, PaginatedItems

MAX_LIMIT = 100
DEFAULT_LIMIT = 100

class ItemService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_item(self, data: ItemCreate) -> Item:
        if not math.isfinite(data.price) or data.price <= 0:
            raise HTTPException(status_code=422, detail="Invalid price")
        item = Item(name=data.name, description=data.description, price=data.price, is_active=data.is_active)
        self._db.add(item)
        try:
            await self._db.commit()
            await self._db.refresh(item)
            return item
        except IntegrityError:
            await self._db.rollback()
            raise HTTPException(status_code=409, detail="Integrity constraint violation")

    async def get_item(self, item_id: int) -> Item:
        result = await self._db.execute(select(Item).where(Item.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
        return item

    async def list_items(self, offset: int = 0, limit: int = DEFAULT_LIMIT) -> PaginatedItems:
        if offset < 0 or limit < 1 or limit > MAX_LIMIT:
            raise HTTPException(status_code=422, detail="Invalid pagination parameters")
        total = (await self._db.execute(select(func.count()).select_from(Item))).scalar_one()
        rows = (await self._db.execute(select(Item).order_by(Item.id).offset(offset).limit(limit))).scalars().all()
        return PaginatedItems(total=int(total), page=(offset // limit) + 1, size=limit, items=list(rows))

    async def update_item(self, item_id: int, data: ItemUpdate) -> Item:
        item = await self.get_item(item_id)
        delta = data.model_dump(exclude_unset=True, exclude_none=True)
        if not delta: return item
        for key, value in delta.items():
            setattr(item, key, value)
        try:
            await self._db.commit()
            await self._db.refresh(item)
            return item
        except IntegrityError:
            await self._db.rollback()
            raise HTTPException(status_code=409, detail="Integrity constraint violation")

    async def delete_item(self, item_id: int) -> None:
        stmt = delete(Item).where(Item.id == item_id)
        result = await self._db.execute(stmt)
        if result.rowcount == 0:
            await self._db.rollback()
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
        try:
            await self._db.commit()
        except IntegrityError:
            await self._db.rollback()
            raise HTTPException(status_code=409, detail="Integrity constraint violation")