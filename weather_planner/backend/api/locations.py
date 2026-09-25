from fastapi import APIRouter
from ..services.location_service import get_enabled_locations, get_regions

router = APIRouter(prefix="/api", tags=["locations"])


@router.get("/locations")
async def list_locations():
    return get_enabled_locations()


@router.get("/regions")
async def list_regions():
    return get_regions()
