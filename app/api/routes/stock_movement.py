from itertools import product
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import SessionLocal, get_db
from app.models.category import Category
from app.models.product import Product
from app.models.stock_movement import StockMovement
from app.schemas import stock
from app.schemas.stock import StockUpdateRequest
from app.api.routes.products import _get_active_product

router = APIRouter(prefix="/stock_movements", tags=["Stock Movements"])


@router.post("/products/{id}/stock/increment")
def increase_stock(id:int,StockUpdateRequest: StockUpdateRequest):
    db = SessionLocal()
    try:
        print(StockUpdateRequest)
        print(id)
        product = db.scalar(
        select(Product).where(Product.id == id)
    )
        print(product)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        movement = db.add(
            StockMovement(
                product_id=product.id,
                change=int(StockUpdateRequest.qty),
                reason=StockUpdateRequest.reason,
            )
        )

        product.stock_quantity += StockUpdateRequest.qty
        db.commit()
        return {"message": "Stock incerement successfully"}
    except Exception as e:
        db.rollback()
        print(e)
    finally:
        db.close()



@router.post("/products/{id}/stock/decrement")
def decrease_stock(id:int,StockUpdateRequest: StockUpdateRequest):
    db = SessionLocal()
    try:
        print(StockUpdateRequest)
        print(id)
        product = db.scalar(
        select(Product).where(Product.id == id)
    )
        print(product)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        movement = db.add(
            StockMovement(
                product_id=product.id,
                change=int(StockUpdateRequest.qty),
                reason=StockUpdateRequest.reason,
            )
        )

        if product.stock_quantity <StockUpdateRequest.qty:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough stocks"
        )
        product.stock_quantity -= StockUpdateRequest.qty
        db.commit()
        return {"message": "Stock decrement successfully"}
    except Exception as e:
        db.rollback()
        print(e)
    finally:
        db.close()
