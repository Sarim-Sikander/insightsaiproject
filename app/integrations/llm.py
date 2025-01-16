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
    document: dict,
    query_params: dict,
    weights: dict = None
) -> float:
    weights = weights or {
        "revenue": 1.0,
        "net_profit": 1.0,
        "revenue_growth_rate": 1.0,
        "operational_cost_reduction": 1.0,
    }

    score = 0.0
    for key, weight in weights.items():
        if key in query_params and key in document:
            target = query_params[key]
            actual = document[key]
            score += weight / (1 + abs(actual - target))

    return score
