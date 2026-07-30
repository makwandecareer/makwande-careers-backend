"""Reference FastAPI implementation for CV PDF and DOCX downloads.

Adapt imports and service names to the Makwande Careers backend structure.
"""

from io import BytesIO
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict

router = APIRouter(prefix="/api/ai-cv/export", tags=["AI CV export"])

PDF_MEDIA_TYPE = "application/pdf"
DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


class CvExportRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    filename: str = "makwande-cv"


def sanitise_filename(value: str, extension: str) -> str:
    safe = "".join(character for character in value if character.isalnum() or character in "-_ ")
    safe = "-".join(safe.strip().split()) or "makwande-cv"
    return f"{safe}.{extension}"


def ensure_binary_file(content: bytes, format_name: Literal["PDF", "DOCX"]) -> bytes:
    if not content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{format_name} generation returned an empty file.",
        )
    return content


def attachment_response(content: bytes, filename: str, media_type: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/pdf")
async def export_pdf(
    payload: CvExportRequest,
    current_user=Depends(...),  # Replace with get_current_user
) -> Response:
    # Replace with the real service call.
    # pdf_bytes = await cv_export_service.generate_pdf(payload.model_dump(), current_user)
    pdf_bytes = b""
    pdf_bytes = ensure_binary_file(pdf_bytes, "PDF")

    return attachment_response(
        pdf_bytes,
        sanitise_filename(payload.filename, "pdf"),
        PDF_MEDIA_TYPE,
    )


@router.post("/docx")
async def export_docx(
    payload: CvExportRequest,
    current_user=Depends(...),  # Replace with get_current_user
) -> Response:
    # Replace with the real service call.
    # docx_bytes = await cv_export_service.generate_docx(payload.model_dump(), current_user)
    docx_bytes = b""
    docx_bytes = ensure_binary_file(docx_bytes, "DOCX")

    return attachment_response(
        docx_bytes,
        sanitise_filename(payload.filename, "docx"),
        DOCX_MEDIA_TYPE,
    )
