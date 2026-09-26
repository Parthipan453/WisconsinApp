import os
import uuid
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from ..models import Application, Document, DocumentRequirement


class DocumentService:
    """Handles file uploads, persistence, and document-requirement checks."""

    def __init__(self) -> None:
        self.upload_dir = Path(settings.MEDIA_ROOT) / "applicant_docs"

    def upload(
        self,
        application: Application,
        doc_type: str,
        uploaded_file: UploadedFile,
    ) -> Document:
        os.makedirs(self.upload_dir, exist_ok=True)
        ext = os.path.splitext(uploaded_file.name)[1]
        safe_name = f"{uuid.uuid4().hex}{ext}"
        rel_path = f"applicant_docs/{safe_name}"
        abs_path = self.upload_dir / safe_name

        with open(abs_path, "wb+") as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        return Document.objects.create(
            application=application,
            doc_type=doc_type,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
            file_path=rel_path,
        )

    def get_documents(self, application: Application) -> list[Document]:
        return list(Document.objects.filter(application=application))

    def verify_document(self, doc_id: int) -> Document:
        doc = Document.objects.get(pk=doc_id)
        doc.is_verified = True
        doc.save()
        return doc

    def delete_document(self, doc_id: int) -> None:
        doc = Document.objects.get(pk=doc_id)
        abs_path = self.upload_dir / os.path.basename(doc.file_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)
        doc.delete()

    def get_doc_type_choices(self) -> list[tuple[str, str]]:
        return Document.DOC_TYPES

    def get_required_documents(self, application: Application) -> list[DocumentRequirement]:
        if not application.university or not application.degree_level:
            return []
        return list(
            DocumentRequirement.objects.filter(
                university=application.university,
                degree_level=application.degree_level,
            )
        )

    def get_missing_documents(self, application: Application) -> list:
        required = self.get_required_documents(application)
        uploaded = set(
            self.get_documents(application).values_list("requirement__code", flat=True)
        )
        return [req for req in required if req.code not in uploaded]
