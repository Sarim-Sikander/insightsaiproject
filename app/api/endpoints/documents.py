import json
import os
from typing import LiteralString

from fastapi import APIRouter, Depends, HTTPException

from app.controllers.documents import DocumentController
from app.core.factory import Factory
from app.schemas.responses.document import DocumentSchema

router = APIRouter()  # Initialize the API router for defining endpoints.


@router.post("/documents")
async def load_documents(
    document_controller: DocumentController = Depends(
        Factory().get_document_controller
    ),
) -> dict[str, str]:
    """
    Endpoint to load and process documents from a JSON dataset.
    - Reads data from a JSON file.
    - Cleans, preprocesses, and enriches the data using the document controller.
    - Creates documents in the database.
    """
    data_path: LiteralString = os.path.join("app", "data", "Dataset.json")  # Path to the dataset file.

    if not os.path.exists(data_path):  # Check if the file exists.
        raise HTTPException(status_code=404, detail="Data file not found.")

    try:
        # Open and load the dataset JSON file.
        with open(data_path, "r") as file:
            raw_data = json.load(file)

        # Clean and preprocess the data.
        processed_data = await document_controller.clean_and_preprocess_data(raw_data)
        
        # Add additional metrics to the processed data.
        enriched_data = document_controller.add_metrics_to_documents(processed_data)
        
        # Create each document in the database.
        for item in enriched_data:
            await document_controller.create(item)

        return {"status": "Documents loaded successfully"}  # Return success response.

    except Exception as e:  # Handle any exceptions that occur.
        raise HTTPException(status_code=500, detail=f"Error loading documents: {e}")


@router.get("/documents/{document_id}", response_model=DocumentSchema)
async def get_document(
    document_id: str,
    document_controller: DocumentController = Depends(
        Factory().get_document_controller
    ),
):
    """
    Endpoint to retrieve a specific document by its ID.
    - Checks if the document exists in the database.
    - Returns the document if found; raises an exception otherwise.
    """
    document = await document_controller.get_by_column(
        column="document_id", value=document_id, unique=True
    )  # Query the database for the document by its ID.
    if not document:  # If the document is not found, raise a 404 error.
        raise HTTPException(status_code=404, detail="Document not found.")
    return document  # Return the document if it exists.


@router.get("/documents", response_model=list[DocumentSchema])
async def get_all_documents(
    skip: int = 0,
    limit: int = 100,
    document_controller: DocumentController = Depends(
        Factory().get_document_controller
    ),
):
    """
    Endpoint to retrieve all documents with pagination.
    - Supports skipping a certain number of records and limiting the number of results.
    - Returns a list of documents or raises a 404 error if no documents are found.
    """
    documents = await document_controller.get_all(skip=skip, limit=limit)  # Retrieve all documents with pagination.
    if not documents:  # If no documents are found, raise a 404 error.
        raise HTTPException(status_code=404, detail="No documents found.")

    return documents  # Return the list of documents.
