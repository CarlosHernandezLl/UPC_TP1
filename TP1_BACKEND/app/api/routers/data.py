from fastapi import APIRouter, HTTPException
from fastapi import UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from app.models.hvac_model import DataIngestionLog
from app.core.database import get_db
from app.services.data_service import DataService
from app.api.deps import check_role



router = APIRouter(prefix="/data", tags=["Carga de Datos"])

@router.post("/upload")
async def upload_hvac_data(
    file_plc: UploadFile = File(...),
    file_log: UploadFile = File(...),
    file_ext: UploadFile = File(...),
    start_date: str = Form(None),
    end_date: str = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(check_role(["ADMIN"]))
):
    service = DataService(db)
    total = await service.upload_and_sync(file_plc, file_log, file_ext, start_date, end_date)
    return total


@router.get("/ingestion/history")
def get_ingestion_history(
    db: Session = Depends(get_db),
    current_user = Depends(check_role(["ADMIN", "USER"])) # Permite que usuarios comunes también lo vean
):
    """
    Retorna el historial completo de las cargas y sincronizaciones climáticas.
    """
    try:
        history = db.query(DataIngestionLog).order_by(DataIngestionLog.fecha_carga.desc()).all()
        return history
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al obtener el historial del Gemelo Digital: {str(e)}"
        )