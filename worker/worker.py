import redis.asyncio as redis
import asyncio
from core.llm_service import ask_kimi_to_review
from Database.vector_db import CodeKnowledgeBase

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

kb = CodeKnowledgeBase()

async def process_code_review_task(diff_content:str):
    relate_chunks = kb.search_similar_code(query_text=diff_content,n_results=5)

    if relate_chunks:
        context_code = "\n\n".join(relate_chunks)
        print(f"识别出{len(relate_chunks)}块相关代码")
    else:
        context_code = "无相关历史代码上下文。"
        print("未检索到强相关历史代码，将仅基于本次增量进行审查。")


    review_result = await ask_kimi_to_review(diff_content=diff_content, context_code=context_code)

    print(review_result)

async def main_worker_loop():
    while True:
        try:
            task = await redis_client.brpop("code_review_tasks", timeout=0)

            if task:
                queue_name, diff_content = task
                print("收到新的代码审查任务，分配线程处理...")
                asyncio.create_task(process_code_review_task(diff_content))


        except Exception as e:
            print(f"Redis 监听循环发生致命错误: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    # 启动异步事件循环
    try:
        asyncio.run(main_worker_loop())
    except KeyboardInterrupt:
        print("Worker 已手动停止。")







