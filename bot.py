import os
import time
import requests
from openai import OpenAI

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

MODEL = "openai/gpt-oss-120b:fastest"

offset = 0

print("🤖 Бот запущен!")

while True:
    try:
        response = requests.get(
            f"{API}/getUpdates",
            params={"offset": offset, "timeout": 30},
            timeout=35
        )

        data = response.json()

        for update in data.get("result", []):
            offset = update["update_id"] + 1

            message = update.get("message")
            if not message:
                continue

            text = message.get("text", "")

            if not text.startswith("/ai"):
                continue

            question = text[3:].strip()

            if not question:
                answer = "Напиши вопрос после /ai 🙂"
            else:
                try:
                    result = client.chat.completions.create(
                        model=MODEL,
                        messages=[
                            {
                                "role": "system",
                                "content": "Ты дружелюбный помощник. Отвечай на русском языке."
                            },
                            {
                                "role": "user",
                                "content": question
                            }
                        ],
                        max_tokens=500
                    )

                    answer = result.choices[0].message.content

                except Exception as e:
                    print("AI error:", e)
                    answer = "⚠️ Ошибка нейросети."

            requests.post(
                f"{API}/sendMessage",
                json={
                    "chat_id": message["chat"]["id"],
                    "text": answer
                }
            )

    except Exception as e:
        print("Ошибка:", e)
        time.sleep(5)
