from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.data_service import DataService
from app.api.deps import check_role
from app.repositories.data_ingestion_repository import DataIngestionRepository
from app.repositories.hvac_repository import HvacRepository

router = APIRouter(prefix="/data", tags=["Carga de Datos"])


def get_ingestion_repository(db: Session = Depends(get_db)) -> DataIngestionRepository:
    return DataIngestionRepository(db)


def get_hvac_repository(db: Session = Depends(get_db)) -> HvacRepository:
    return HvacRepository(db)


def get_data_service(
    ingestion_repo: DataIngestionRepository = Depends(get_ingestion_repository),
    hvac_repo: HvacRepository = Depends(get_hvac_repository),
) -> DataService:
    return DataService(hvac_repo=hvac_repo, ingestion_repo=ingestion_repo)


@router.post("/upload", dependencies=[Depends(check_role(["SUPERVISOR", "ADMIN"]))])
async def upload_hvac_data(
    file_plc: UploadFile = File(...),
    file_log: UploadFile = File(...),
    file_ext: UploadFile = File(...),
    start_date: str = Form(None),
    end_date: str = Form(None),
    service: DataService = Depends(get_data_service),
):
    return await service.upload_and_sync(
        file_plc, file_log, file_ext, start_date, end_date
    )


@router.get(
    "/ingestion/history", dependencies=[Depends(check_role(["SUPERVISOR", "ADMIN"]))]
)
def get_ingestion_history(service: DataService = Depends(get_data_service)):
    """Retorna el historial completo de las cargas y sincronizaciones climáticas."""
    try:
        return service.get_ingestion_history()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al obtener el historial del Gemelo Digital: {str(e)}",
        )
