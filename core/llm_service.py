import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)

async def ask_kimi_to_review(code_chunk:str)->str:
    system_prompt="你是一个资深的 Python 架构师。请审查下面这段 Git Diff 代码变更。指出潜在的逻辑漏洞、性能隐患或不规范的地方。如果没有问题，请回复'代码看起来不错'。"

    try:
        completion = await client.chat.completions.create(
            model="moonshot-v1-128k",
            messages=[
                {"role":"system", "content":system_prompt},
                {"role":"user", "content":f"请审查以下代码：{code_chunk}"},
            ],
            temperature=0.3,
        )
        review_result=completion.choices[0].message.content
        return review_result
    except Exception as e:
        print(f"连接失败 {e}")
        return f"代码审查失败，原因: {e}"

if __name__ == "__main__":
    test_code = """
    + def divide(a, b):
    +     return a / b
    """
    print(ask_kimi_to_review(test_code))
