"""
Product API Endpoints
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[ProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db),
) -> list[ProductResponse]:
    result = await db.execute(
        select(Product)
        .where(Product.active.is_(True))
        .order_by(Product.created_at.desc())
    )
    products = result.scalars().all()
    return [ProductResponse.model_validate(product) for product in products]


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar produto",
)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    product = Product(
        name=payload.name.strip(),
        base_value_cent=payload.base_value_cent,
        installments=payload.installments,
        payment_methods=payload.payment_methods,
        active=True,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return ProductResponse.model_validate(product)
