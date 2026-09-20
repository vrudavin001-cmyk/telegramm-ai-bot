import os

from openai import OpenAI


HF_TOKEN = os.environ.get(
    "HF_TOKEN"
)


MODEL = "openai/gpt-oss-120b:fastest"


client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)


STYLES = {

    "normal":
        "Дружелюбный, спокойный и полезный.",

    "friend":
        "Общайся как близкий друг.",

    "troll":
        "Общайся весело, с подколами и сарказмом.",

    "rude":
        "Дерзкий разговорный стиль, но без угроз.",

    "serious":
        "Строго, кратко и по делу.",

    "expert":
        "Отвечай как эксперт, структурировано.",

    "sigma":
        "Коротко, уверенно, мемно и дерзко."
}


memory = {}


def ask(
    chat_id,
    text,
    style="normal"
):

    if chat_id not in memory:

        memory[chat_id] = []

    history = memory[
        chat_id
    ]

    history.append({
        "role": "user",
        "content": text
    })

    history = history[-10:]

    memory[
        chat_id
    ] = history

    system = f"""
Ты Telegram AI-бот.

Твой стиль:
{STYLES.get(style, STYLES["normal"])}

Отвечай на языке пользователя.

Будь естественным.

Не говори, что ты выполняешь действия,
которые на самом деле не выполнял.

Если не знаешь ответ — скажи об этом.
"""

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=[
                {
                    "role": "system",
                    "content": system
                }
            ] + history,

            max_tokens=700,

            temperature=0.8
        )

        answer = (
            response
            .choices[0]
            .message
            .content
        )

        memory[
            chat_id
        ].append({
            "role": "assistant",
            "content": answer
        })

        memory[
            chat_id
        ] = memory[
            chat_id
        ][-10:]

        return answer

    except Exception as e:

        print(
            "AI ERROR:",
            e
        )

        return (
            "⚠️ AI временно недоступен."
        )


def summarize(text):

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=[

                {
                    "role": "system",
                    "content":
                        "Кратко анализируй переписку Telegram."
                },

                {
                    "role": "user",
                    "content":
                        f"""
Сделай краткую сводку:

{text}

Выдели главные темы,
важные события и решения.
"""
                }
            ],

            max_tokens=700,

            temperature=0.3
        )

        return (
            response
            .choices[0]
            .message
            .content
        )

    except Exception as e:

        print(
            "SUMMARY ERROR:",
            e
        )

        return "Не удалось сделать сводку."
