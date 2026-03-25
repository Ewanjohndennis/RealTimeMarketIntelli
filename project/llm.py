from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

load_dotenv()

client = InferenceClient(
    model="openai/gpt-oss-20b",
    token=os.getenv("HF_TOKEN")
)

def ask_llm(system_prompt, user_prompt):

    response = client.chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=3000,
        temperature=0.4
    )

    return response.choices[0].message.content