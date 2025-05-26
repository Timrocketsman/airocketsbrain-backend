from fastapi import FastAPI, Request, HTTPException from fastapi.middleware.cors import CORSMiddleware import openai import os import time

Проверка обязательных переменных окружения

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") ASSISTANT_ID = os.getenv("ASSISTANT_ID") if not OPENAI_API_KEY or not ASSISTANT_ID: raise RuntimeError("Необходимы переменные окружения OPENAI_API_KEY и ASSISTANT_ID")

Настройка ключа OpenAI

openai.api_key = OPENAI_API_KEY

app = FastAPI( title="AiRocketsBrain API", description="API для взаимодействия Telegram Mini App с OpenAI Assistants API", version="1.0.0" )

Настройки CORS

app.add_middleware( CORSMiddleware, allow_origins=[""],  # В проде указать конкретные домены allow_credentials=True, allow_methods=[""], allow_headers=["*"], )

@app.get("/", tags=["Health"]) def read_root(): return {"status": "ok", "message": "AiRocketsBrain API running"}

@app.post("/api/chat", tags=["Chat"]) async def chat(request: Request): data = await request.json() user_input = data.get("message") if not user_input: raise HTTPException(status_code=400, detail="Поле 'message' не может быть пустым")

try:
    # Создание нового потока диалога
    thread = openai.beta.threads.create()

    # Отправка пользовательского запроса в поток
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

    # Запуск ассистента для ответа
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    # Ожидание завершения run
    while True:
        run_check = openai.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_check.status == "completed":
            break
        if run_check.status == "failed":
            raise HTTPException(status_code=500, detail="Сбой при выполнении ассистента")
        time.sleep(1)

    # Получение ответного сообщения от ассистента
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    # Берем последнее сообщение
    assistant_message = messages.data[-1].content[0].text.value
    return {"reply": assistant_message}
except openai.error.OpenAIError as e:
    raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

