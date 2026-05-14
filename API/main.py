import uvicorn
import json
from fastapi import FastAPI
import redis.asyncio as redis

app=FastAPI()

redis_client=redis.Redis(host='127.0.0.1',port=6379,db=0,decode_responses=True)


@app.get("/ping")
async def status():
    return {"status": "ok"}


@app.post("/webhook")
async def receive_github_webhook(payload: dict):
    print("收到 Webhook 数据啦：", payload)

    payload_str = json.dumps(payload)

    await redis_client.lpush("webhook", payload_str)
    return {"message": "Webhook received successfully"}


if __name__=="__main__":
    uvicorn.run("main:app",host="127.0.0.1",port=8000,reload=True)
