import re
from datetime import datetime
from typing import List

from app.controllers.base import BaseController
from app.models.documents import Documents
from app.repositories import DocumentRepository


class DocumentController(BaseController[Documents]):
    def __init__(self, document_repository: DocumentRepository):
        super().__init__(model=Documents, repository=document_repository)
        self.document_repository = document_repository

    async def clean_and_preprocess_data(self, raw_data: List[dict]) -> List[dict]:
        processed_data = []
        for item in raw_data:
            try:
                document_data = {
                    "document_id": item.get("document_id"),
                    "title": item.get("title", "").strip(),
                    "company": item.get("company", "").strip(),
                    "date": (
                        datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                        if item.get("date")
                        else None
                    ),
                    "topics": ",".join(item.get("topics", [])),
                    "content": item.get("content", "").strip(),
                    "conclusion": item.get("conclusion", "").strip(),
                }
                processed_data.append(document_data)
            except Exception as e:
                raise ValueError(f"Error processing document: {item}. Error: {e}")
        return processed_data

    def extract_metrics(self, content: str) -> dict:
        metrics = {
            "revenue": None,
            "net_profit": None,
            "revenue_growth_rate": None,
            "operational_cost_reduction": None,
        }
        try:
            # Extract revenue
            revenue_match = re.search(r"Revenue[:\s]+\$([\d,\.]+)", content)
            if revenue_match:
                metrics["revenue"] = float(revenue_match.group(1).replace(",", ""))

            # Extract net profit
            net_profit_match = re.search(r"Net Profit[:\s]+\$([\d,\.]+)", content)
            if net_profit_match:
                metrics["net_profit"] = float(
                    net_profit_match.group(1).replace(",", "")
                )

            # Extract revenue growth rate
            growth_rate_match = re.search(
                r"Revenue Growth Rate[:\s]+([\d\.]+)%", content
            )
            if growth_rate_match:
                metrics["revenue_growth_rate"] = float(growth_rate_match.group(1))

            # Extract operational cost reduction
            cost_reduction_match = re.search(
                r"Operational Cost Reduction[:\s]+([\d\.]+)%", content
            )
            if cost_reduction_match:
                metrics["operational_cost_reduction"] = float(
                    cost_reduction_match.group(1)
                )

        except Exception as e:
            print(f"Error extracting metrics: {e}")

        return metrics

    def add_metrics_to_documents(self, documents: list[dict]) -> list[dict]:
        for doc in documents:
            if "content" in doc:
                metrics = self.extract_metrics(doc["content"])
                doc.update(metrics)

        return documents
