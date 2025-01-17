import openai

from app.controllers.base import BaseController
from app.integrations.llm import parse_kpis_from_response
from app.models.documents import Documents
from app.repositories import DocumentRepository


class LLMDocumentController(BaseController[Documents]):
    def __init__(self, document_repository: DocumentRepository):
        super().__init__(model=Documents, repository=document_repository)
        self.document_repository = document_repository

    def generate_llm_response(self, context: str, query: str) -> str:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert assistant summarizing data and answering queries.",
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuery:\n{query}",
                    },
                ],
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Error generating LLM response: {e}")

    def extract_and_enrich_documents(self, documents: list) -> list:
        """
        Extract KPIs using LLM for a list of documents and enrich them with the extracted data.
        """
        enriched_documents = []
        for doc in documents:
            content = doc.get("content", "")
            if not content:
                continue

            try:
                kpi_prompt = (
                    "Extract the following KPIs from the content: revenue, net profit, "
                    "revenue growth rate, and operational cost reduction.\n"
                    f"Content:\n{content}"
                )
                llm_response = self.generate_llm_response(
                    context=content, query=kpi_prompt
                )
                extracted_kpis = parse_kpis_from_response(llm_response)
            except Exception:
                extracted_kpis = {
                    "revenue": None,
                    "net_profit": None,
                    "revenue_growth_rate": None,
                    "operational_cost_reduction": None,
                }

            enriched_documents.append(
                {
                    "title": doc.get("title"),
                    "content": content,
                    "revenue": extracted_kpis.get("revenue"),
                    "net_profit": extracted_kpis.get("net_profit"),
                    "revenue_growth_rate": extracted_kpis.get("revenue_growth_rate"),
                    "operational_cost_reduction": extracted_kpis.get(
                        "operational_cost_reduction"
                    ),
                }
            )

        return enriched_documents
