import json
import os
from typing import LiteralString

from fastapi import APIRouter, Depends, HTTPException

from app.controllers.documents import DocumentController
from app.core.factory import Factory
from app.schemas.responses.document import DocumentSchema

router = APIRouter()


@router.post("/documents")
async def load_documents(
    document_controller: DocumentController = Depends(
        Factory().get_document_controller
    ),
) -> dict[str, str]:
    data_path: LiteralString = os.path.join("app", "data", "Dataset.json")

    if not os.path.exists(data_path):
        raise HTTPException(status_code=404, detail="Data file not found.")

    try:
        with open(data_path, "r") as file:
            raw_data = json.load(file)

        processed_data = await document_controller.clean_and_preprocess_data(raw_data)
        enriched_data = document_controller.add_metrics_to_documents(processed_data)
        for item in enriched_data:
            await document_controller.create(item)

        return {"status": "Documents loaded successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading documents: {e}")


@router.get("/documents/{document_id}", response_model=DocumentSchema)
async def get_document(
    document_id: str,
    document_controller: DocumentController = Depends(
        Factory().get_document_controller
    ),
):
    document = await document_controller.get_by_column(
        column="document_id", value=document_id, unique=True
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


@router.get("/documents", response_model=list[DocumentSchema])
async def get_all_documents(
    skip: int = 0,
    limit: int = 100,
    document_controller: DocumentController = Depends(
        Factory().get_document_controller
    ),
):
    documents = await document_controller.get_all(skip=skip, limit=limit)
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found.")

    return documents
