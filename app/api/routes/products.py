from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any

from celery.utils.collections import force_mapping
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import ValidationError
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app import celery_app
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.category import Category
from app.models.product import Product, ProductStatus
from app.models.user import User
from app.schemas.product import (
    BulkGenerateProductsRequest,
    ProductCreate,
    ProductListParams,
    ProductListResponse,
    ProductRead,
    ProductSortBy,
    ProductUpdate,
    SortOrder,
)
from app.services.generate_csv import generate_csv_file
from app.services.generate_excel import generate_xlsx_file
from app.tasks.bulk_generate import bulk_generate_products_task
from openpyxl import Workbook

router = APIRouter(prefix="/products", tags=["products"])

SORT_COLUMNS: dict[ProductSortBy, ColumnElement[Any]] = {
    ProductSortBy.ID: Product.id,
    ProductSortBy.TITLE: Product.title,
    ProductSortBy.PRICE: Product.price,
    ProductSortBy.STOCK_QUANTITY: Product.stock_quantity,
    ProductSortBy.CREATED_AT: Product.created_at,
    ProductSortBy.STATUS: Product.status,
}


def _active_product_filter():
    return Product.deleted_at.is_(None)


def _get_active_product(db: Session, product_id: int) -> Product | None:
    return db.scalar(
        select(Product).where(Product.id == product_id, _active_product_filter())
    )


def _ensure_category_exists(db: Session, category_id: int) -> None:
    if db.get(Category, category_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )


def _apply_list_filters(stmt: Any, params: ProductListParams) -> Any:
    if not params.include_deleted:
        stmt = stmt.where(_active_product_filter())
    if params.category_id is not None:
        stmt = stmt.where(Product.category_id == params.category_id)
    if params.status is not None:
        stmt = stmt.where(Product.status == params.status)
    if params.min_price is not None:
        stmt = stmt.where(Product.price >= params.min_price)
    if params.max_price is not None:
        stmt = stmt.where(Product.price <= params.max_price)
    if params.search:
        stmt = stmt.where(
            or_(
                Product.title.contains(params.search),
                Product.description.contains(params.search),
            )
        )
    return stmt


def _list_params(
    category_id: int | None = None,
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    status_filter: ProductStatus | None = Query(default=None, alias="status"),
    search: str | None = None,
    sort_by: ProductSortBy = ProductSortBy.CREATED_AT,
    order: SortOrder = SortOrder.DESC,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    include_deleted: bool = False,
) -> ProductListParams:
    try:
        return ProductListParams(
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            status=status_filter,
            search=search,
            sort_by=sort_by,
            order=order,
            page=page,
            page_size=page_size,
            include_deleted=include_deleted,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.errors()
        ) from exc


@router.get("", response_model=ProductListResponse)
def list_products(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    params: Annotated[ProductListParams, Depends(_list_params)],
) -> ProductListResponse:
    count_stmt = _apply_list_filters(select(func.count()).select_from(Product), params)
    total = db.scalar(count_stmt) or 0

    sort_column = SORT_COLUMNS[params.sort_by]
    order_clause = (
        desc(sort_column) if params.order == SortOrder.DESC else asc(sort_column)
    )

    offset = (params.page - 1) * params.page_size
    stmt = (
        _apply_list_filters(select(Product), params)
        .order_by(order_clause)
        .offset(offset)
        .limit(params.page_size)
    )
    items = list(db.scalars(stmt).all())

    return ProductListResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        has_next=params.page * params.page_size < total,
    )


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Product:
    product = _get_active_product(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return product


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Product:
    _ensure_category_exists(db, payload.category_id)

    product = Product(
        category_id=payload.category_id,
        title=payload.title,
        description=payload.description,
        price=payload.price,
        stock_quantity=payload.stock_quantity,
        status=payload.status,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Product:
    product = _get_active_product(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    if payload.category_id is not None:
        _ensure_category_exists(db, payload.category_id)
        product.category_id = payload.category_id
    if payload.title is not None:
        product.title = payload.title
    if payload.description is not None:
        product.description = payload.description
    if payload.price is not None:
        product.price = payload.price
    if payload.stock_quantity is not None:
        product.stock_quantity = payload.stock_quantity
    if payload.status is not None:
        product.status = payload.status

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> None:
    product = _get_active_product(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    product.deleted_at = datetime.now(UTC)
    db.commit()


@router.post("products/bulk-generate")
def bulk_generate_products(
    payload: BulkGenerateProductsRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> None:

    # add function for celert
    print(f"Generating {payload.count} products for category {payload.category_id}")
    task = bulk_generate_products_task.delay(payload.category_id, payload.count)
    return {
        "task_id": task.id,
    }


@router.get("/tasks/{task_id}")
def get_task_status(task_id: str) -> dict[str, Any]:
    task = bulk_generate_products_task.AsyncResult(task_id)
    response = {
        "status": task.status,
        "task_id": task_id,
    }
    return response


@router.get("products/export")
def export_products(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    params: Annotated[ProductListParams, Depends(_list_params)],
    format: str = Query(default="xlsx", enum=["xlsx", "csv"]),
) -> None:
    count_stmt = _apply_list_filters(select(func.count()).select_from(Product), params)
    total = db.scalar(count_stmt) or 0

    sort_column = SORT_COLUMNS[params.sort_by]
    order_clause = (
        desc(sort_column) if params.order == SortOrder.DESC else asc(sort_column)
    )

    offset = (params.page - 1) * params.page_size
    stmt = (
        _apply_list_filters(select(Product), params)
        .order_by(order_clause)
        .offset(offset)
        .limit(params.page_size)
    )
    items = list(db.scalars(stmt).all())

    if format == "xlsx":
        file = generate_xlsx_file(items)
        return FileResponse(
            path=file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    if format == "csv":

        file = generate_csv_file(items)
        return StreamingResponse(
            content=file,
            media_type="text/csv",
        )
