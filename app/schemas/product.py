from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.product import ProductStatus
from app.schemas.common import PaginatedResponse


class ProductSortBy(str, Enum):
    ID = "id"
    TITLE = "title"
    PRICE = "price"
    STOCK_QUANTITY = "stock_quantity"
    CREATED_AT = "created_at"
    STATUS = "status"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class ProductCreate(BaseModel):
    category_id: int
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    price: Decimal = Field(gt=0, decimal_places=2, max_digits=12)
    stock_quantity: int = Field(default=0, ge=0)
    status: ProductStatus = ProductStatus.ACTIVE


class ProductUpdate(BaseModel):
    category_id: int | None = None
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2, max_digits=12)
    stock_quantity: int | None = Field(default=None, ge=0)
    status: ProductStatus | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    title: str
    description: str | None
    price: Decimal
    stock_quantity: int
    status: ProductStatus
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProductListResponse(PaginatedResponse[ProductRead]):
    pass


class ProductListParams(BaseModel):
    category_id: int | None = None
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    status: ProductStatus | None = None
    search: str | None = None
    sort_by: ProductSortBy = ProductSortBy.CREATED_AT
    order: SortOrder = SortOrder.DESC
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    include_deleted: bool = False

    @model_validator(mode="after")
    def validate_price_range(self) -> "ProductListParams":
        if self.min_price is not None and self.max_price is not None and self.min_price > self.max_price:
            raise ValueError("min_price cannot be greater than max_price")
        return self
