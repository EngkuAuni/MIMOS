## Handles prompt sending via Groq

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "Streamlit_env", ".env"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_llm(prompt, model="deepseek-r1-distill-llama-70b"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content
