from functools import partial

from fastapi import Depends

from app.controllers import DocumentController
from app.core.database.session import get_session
from app.models.documents import Documents
from app.repositories import DocumentRepository


class Factory:
    document_repository = partial(DocumentRepository, Documents)

    def get_document_controller(
        self, db_session=Depends(get_session)
    ) -> DocumentController:
        return DocumentController(
            document_repository=self.document_repository(db_session=db_session),
        )
