import redis.asyncio as redis
import json
import httpx
import asyncio
from core.llm_service import ask_kimi_to_review

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def split_diff_by_file(raw_diff_text):
    file_chunks = raw_diff_text.split("diff --git")

    clean_files = []
    for chunk in file_chunks:
        if not chunk.strip():
            continue

        complete_chunk = "diff --git " + chunk
        clean_files.append(complete_chunk)

    print(f"切出了{len(clean_files)}块")
    return clean_files




async def process_single_task(payload_str):
    try:
        payload = json.loads(payload_str)
        diff_url = payload.get("pull_request",{}).get("diff_url")

        if not diff_url:
            return

        print(f"开始拉取raw:{diff_url}")

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(diff_url)
            raw_diff_text = response.text

        file_diff_list = split_diff_by_file(raw_diff_text)

        for index, file_chunk in enumerate(file_diff_list):
            if len(file_diff_list[index]) > 30000:
                print(f"文件过大")

            print(f"正在处理第{index+1}块切块")
            opinion = await ask_kimi_to_review(file_chunk)

            print(opinion)


    except Exception as e:
        print(f"{e}")


async def main_loop():
    while True:
        task_data = await redis_client.brpop("webhook", 0)

        if task_data:
            _, task_data = task_data

            asyncio.create_task(process_single_task(task_data))

if __name__ == "__main__":
    # 启动 Python 的异步事件循环
    asyncio.run(main_loop())




