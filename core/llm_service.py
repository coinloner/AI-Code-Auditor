import os
import asyncio

from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)

async def ask_kimi_to_review(diff_content: str, context_code: str) -> str:
    system_prompt = f"""
你是一个极其严苛的高级后端架构师。现在有人正在提交一段代码修改。

    【项目历史相关背景代码 (供你参考全局逻辑)】：
    {context_code}

【你的任务】：
1. 结合历史背景，审查本次修改是否合理。
2. 是否会破坏原有的逻辑流？有没有忘记修改关联变量？
3. 如果有致命错误，请用强烈的语气指出。如果没有问题，请简单回复“LGTM (Looks Good To Me)”。
"""
    try:
        completion = await client.chat.completions.create(
            model="moonshot-v1-128k",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"【本次 Git 提交的修改内容 (Diff)】：\n{diff_content}"},
            ],
            temperature=0.3,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"连接失败，{e}")
        return f"代码审查失败，原因: {e}"


if __name__ == "__main__":
    # 测试数据
    test_diff = """
    + def divide(a, b):
    +     return a / b
    """
    test_context = "无相关历史上下文"

    print("🚀 正在单独测试 LLM 服务...")
    result = asyncio.run(ask_kimi_to_review(test_diff, test_context))
    print(result)



