import redis.asyncio as redis
import asyncio
import os
import datetime
from core.llm_service import ask_kimi_to_review
from Database.vector_db import CodeKnowledgeBase

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

kb = CodeKnowledgeBase()

def save_review_report_to_md(diff_content: str, relate_chunks: list, review_result: str):
    report_dir = "review_reports"
    os.makedirs(report_dir, exist_ok=True)

    now = datetime.datetime.now()
    time_str = now.strftime("%Y%m%d%H%M%S")
    file_name = now.strftime("Review_%Y%m%d_%H%M%S.md")
    file_path = os.path.join(report_dir, file_name)

    md_content = f"# AI 代码审查报告\n\n"
    md_content += f"**生成时间：** {time_str}\n\n"
    md_content += "---\n\n"

    md_content += f"## 本次提交的变更 (Git Diff)\n```diff\n{diff_content}\n```\n\n"

    md_content += f"## 大模型审查意见\n{review_result}\n\n"
    md_content += "---\n\n"

    md_content += f"## 🔍 RAG 检索诊断 (作为上下文发给 AI 的老代码)\n"
    md_content += f"*共检索出 {len(relate_chunks)} 块相关代码，供你验证相关性：*\n\n"

    if not relate_chunks:
        md_content += "> 未检索到任何相关历史代码。\n"
    else:
        for i, chunk in enumerate(relate_chunks):
            md_content += f"### 关联代码块 {i + 1}\n```python\n{chunk}\n```\n\n"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"审查报告已生成并保存至: {file_path}")




async def process_code_review_task(diff_content:str):
    relate_chunks = kb.search_similar_code(query_text=diff_content,n_results=5)

    if relate_chunks:
        context_code = "\n\n".join(relate_chunks)
        print(f"识别出{len(relate_chunks)}块相关代码")
    else:
        context_code = "无相关历史代码上下文。"
        print("未检索到强相关历史代码，将仅基于本次增量进行审查。")


    review_result = await ask_kimi_to_review(diff_content=diff_content, context_code=context_code)

    save_review_report_to_md(diff_content, relate_chunks, review_result)

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







