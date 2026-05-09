from fastapi import APIRouter
from app.services.optimization_service import OptimizationService
from app.schemas.optimization_schema import OptimizationInput

router = APIRouter(prefix="/optimization", tags=["optimization"])

@router.post("/calculate-optimal")
async def calculate_optimal(data: OptimizationInput):
    service = OptimizationService()
    result = await service.run_optimization(data)
    return result