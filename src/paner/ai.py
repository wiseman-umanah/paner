from groq import Groq
from pathlib import Path

_client: Groq | None = None 

def init_client(api_key: str) -> None:
    """
    Initialize the Groq client
    """
    global _client
    _client = Groq(api_key=api_key)


def get_client() -> Groq:
    """
    Get the existing client instance
    """
    if _client is None:
        raise RuntimeError("Groq client not initialized. Call init_client() first.")
    return _client


def load_prompt(context: str, question: str) -> str:
    """
    Loads the system prompt from prompt file
    """
    prompt_path = Path(__file__).with_name("prompt.txt")
    with prompt_path.open("r", encoding="utf-8") as file:
        base_prompt = file.read()
        prompt = f"""
        {base_prompt}
        CONTEXT:
        {context}

        QUESTION:
        {question}
        """
        return prompt


def answer_question(prompt: str) -> str:
    """
    Answers the user based on the prompt sent
    """
    response = _client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content":  prompt}
            ]
        )
    reply = response.choices[0].message.content

    return reply

