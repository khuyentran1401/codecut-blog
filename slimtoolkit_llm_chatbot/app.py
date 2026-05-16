import os
import chainlit as cl
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


@cl.on_chat_start
async def start():
    cl.user_session.set("messages", [])


@cl.on_message
async def main(message: cl.Message):
    messages = cl.user_session.get("messages")
    messages.append({"role": "user", "content": message.content})

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    reply = response.choices[0].message.content

    messages.append({"role": "assistant", "content": reply})
    cl.user_session.set("messages", messages)

    await cl.Message(content=reply).send()
