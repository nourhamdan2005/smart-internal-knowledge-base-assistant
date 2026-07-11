from ollama import AsyncClient

from app.core.config import settings


client = AsyncClient(host=settings.ollama_base_url)


async def generate_answer(question: str, context: str) -> str:
    response = await client.chat(
        model=settings.ollama_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a company internal knowledge assistant. "
                    "Answer only using the supplied company documents. "
                    "If the answer is not present, say: "
                    "\"I couldn't find this information in the available documents.\""
                ),
            },
            {
                "role": "user",
                "content": f"""
Company documents:

{context}

Question:
{question}
""",
            },
        ],
        options={
            "temperature": 0.2,
        },
    )

    return response["message"]["content"]