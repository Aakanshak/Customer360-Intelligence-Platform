from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import DataValidationError
from app.db.session import get_db
from app.services.ingestion import checksum_bytes, ingest_dataframe, load_bytes

router = APIRouter(prefix="/ingestion", tags=["Data ingestion"])


@router.post("/files")
async def upload_file(
    dataset_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit.")
    try:
        frame = load_bytes(content, file.filename or "upload.csv")
        return ingest_dataframe(db, frame, dataset_type, file.filename or "upload.csv", checksum_bytes(content))
    except DataValidationError as exc:
        raise HTTPException(422, str(exc)) from exc
