from typing import Optional

import openai

from app.core.config import config

openai.api_key = config.OPEN_AI_KEY


def generate_llm_response(context: str, query: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert assistant summarizing data and answering queries.",
                },
                {"role": "user", "content": f"Context:\n{context}\n\nQuery:\n{query}"},
            ],
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"Error generating LLM response: {e}")


def compute_numerical_score(
    document: dict, query_params: dict, weights: dict = None
) -> float:
    """
    Compute a numerical score for a document based on query parameters and weights.
    Handles missing values gracefully.
    """
    weights = weights or {
        "revenue": 1.0,
        "net_profit": 1.0,
        "revenue_growth_rate": 1.0,
        "operational_cost_reduction": 1.0,
    }

    score = 0.0
    for key, weight in weights.items():
        target = query_params.get(key)
        actual = document.get(key)
        if (
            target is not None and actual is not None
        ):  # Only compute when both are present
            score += weight / (1 + abs(actual - target))

    return score


def parse_kpis_from_response(response: str) -> dict:
    """
    Parse KPIs from the LLM response.
    - Extract numeric fields like revenue, net profit, etc., from the response string.
    - Handle variations in formatting and missing data gracefully.
    """
    kpis = {
        "revenue": None,
        "net_profit": None,
        "revenue_growth_rate": None,
        "operational_cost_reduction": None,
    }

    lines = response.split("\n")
    for line in lines:
        line_lower = line.lower()

        if "revenue:" in line_lower:
            try:
                kpis["revenue"] = float(
                    line.split(":")[-1].strip().replace("$", "").replace(",", "")
                )
            except ValueError:
                continue

        elif "net profit:" in line_lower:
            try:
                kpis["net_profit"] = float(
                    line.split(":")[-1].strip().replace("$", "").replace(",", "")
                )
            except ValueError:
                continue

        elif "revenue growth rate:" in line_lower:
            try:
                kpis["revenue_growth_rate"] = float(
                    line.split(":")[-1].strip().replace("%", "")
                )
            except ValueError:
                continue

        elif "operational cost reduction:" in line_lower:
            try:
                kpis["operational_cost_reduction"] = float(
                    line.split(":")[-1].strip().replace("%", "")
                )
            except ValueError:
                continue

    return kpis


def extract_and_enrich_documents(documents: list) -> list:
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
            llm_response = generate_llm_response(context=content, query=kpi_prompt)
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


def apply_numeric_filters(
    ranked_documents: list,
    min_revenue: Optional[float],
    max_revenue: Optional[float],
    min_net_profit: Optional[float],
    max_net_profit: Optional[float],
    min_revenue_growth_rate: Optional[float],
    max_revenue_growth_rate: Optional[float],
    min_operational_cost_reduction: Optional[float],
    max_operational_cost_reduction: Optional[float],
) -> list:
    """
    Apply numeric filters to a list of ranked documents.
    """
    return [
        (final_score, relevance_score, numerical_score, doc)
        for final_score, relevance_score, numerical_score, doc in ranked_documents
        if (not min_revenue or doc["revenue"] >= min_revenue)
        and (not max_revenue or doc["revenue"] <= max_revenue)
        and (not min_net_profit or doc["net_profit"] >= min_net_profit)
        and (not max_net_profit or doc["net_profit"] <= max_net_profit)
        and (
            not min_revenue_growth_rate
            or doc["revenue_growth_rate"] >= min_revenue_growth_rate
        )
        and (
            not max_revenue_growth_rate
            or doc["revenue_growth_rate"] <= max_revenue_growth_rate
        )
        and (
            not min_operational_cost_reduction
            or doc["operational_cost_reduction"] >= min_operational_cost_reduction
        )
        and (
            not max_operational_cost_reduction
            or doc["operational_cost_reduction"] <= max_operational_cost_reduction
        )
    ]
