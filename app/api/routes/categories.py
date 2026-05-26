from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


def _category_to_read(category: Category, product_count: int) -> CategoryRead:
    return CategoryRead(
        id=category.id,
        name=category.name,
        product_count=product_count,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


def _get_product_count(db: Session, category_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Product)
            .where(Product.category_id == category_id, Product.deleted_at.is_(None))
        )
        or 0
    )


def _get_attached_product_count(db: Session, category_id: int) -> int:
    return (
        db.scalar(
            select(func.count()).select_from(Product).where(Product.category_id == category_id)
        )
        or 0
    )


@router.get("", response_model=list[CategoryRead])
def list_categories(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[CategoryRead]:
    rows = db.execute(
        select(
            Category,
            func.count(Product.id).label("product_count"),
        )
        .outerjoin(
            Product,
            (Product.category_id == Category.id) & (Product.deleted_at.is_(None)),
        )
        .group_by(Category.id)
        .order_by(Category.id)
    ).all()
    return [
        _category_to_read(category, int(product_count or 0))
        for category, product_count in rows
    ]


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(
    category_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> CategoryRead:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return _category_to_read(category, _get_product_count(db, category.id))


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> CategoryRead:
    existing = db.scalar(select(Category).where(Category.name == payload.name))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists")

    category = Category(name=payload.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return _category_to_read(category, 0)


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> CategoryRead:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    if payload.name is not None:
        existing = db.scalar(
            select(Category).where(Category.name == payload.name, Category.id != category_id)
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists")
        category.name = payload.name

    db.commit()
    db.refresh(category)
    return _category_to_read(category, _get_product_count(db, category.id))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> None:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    attached_count = _get_attached_product_count(db, category_id)
    if attached_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete category with {attached_count} attached product(s)",
        )

    db.delete(category)
    db.commit()
