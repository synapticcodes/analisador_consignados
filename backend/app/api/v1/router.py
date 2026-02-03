"""
API v1 Router
~~~~~~~~~~~~~

Agrega todos os routers da API v1.
"""

from fastapi import APIRouter

from app.api.v1 import analysis, products

# Router principal da API v1
api_router = APIRouter()

# Incluir routers de cada módulo
api_router.include_router(analysis.router)
api_router.include_router(products.router)

# TODO: Adicionar outros routers conforme necessário:
# api_router.include_router(auth.router)
# api_router.include_router(users.router)
# etc.
