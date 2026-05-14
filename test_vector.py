import chromadb

print("🚀 正在启动本地 ChromaDB 向量引擎...")

# 1. 实例化客户端 (Client)：这里我们用内存模式，极度轻量，每次重启会清空
client = chromadb.Client()

# 2. 创建集合 (Collection)：类似于 MySQL 里的 Table
collection = client.create_collection(name="code_rag_demo")

# 3. 数据持久化与向量化 (Embedding)
# 注意看！下面这三个函数，字面上没有任何相同的单词！
print("⏳ 正在将代码文本转化为高维向量 (如果是第一次运行，后台会自动下载一个几十MB的开源 Embedding 模型)...")
collection.add(
    documents=[
        "def calculate_discount(price, rate): return price * rate",  # 打折逻辑
        "class UserAuth: def login(username, password): pass",  # 登录逻辑
        "def checkout(cart_total, user_id): pass"  # 结账逻辑
    ],
    metadatas=[{"file": "discount.py"}, {"file": "auth.py"}, {"file": "cart.py"}],
    ids=["id1", "id2", "id3"]
)

print("✅ 向量化完成！数据已入库。\n" + "=" * 40)

# 4. 见证奇迹的时刻：语义检索 (Semantic Search)
# 假设大模型在看你的 PR，它想找“钱”相关的代码，但它不知道函数名叫什么
query_text = "How to handle the final price and payment?"

print(f"🔍 正在检索与 '{query_text}' 语义最相关的代码...")

# 发起查询，召回 (Recall) 最相关的 2 条数据
results = collection.query(
    query_texts=[query_text],
    n_results=2
)

# 5. 打印召回结果
print("\n🎉 检索结果如下：")
for index, doc in enumerate(results['documents'][0]):
    file_name = results['metadatas'][0][index]['file']
    distance = results['distances'][0][index]  # 余弦距离，越小越相关

    print(f"🏆 Top {index + 1} (距离: {distance:.4f}):")
    print(f"   📂 来源: {file_name}")
    print(f"   💻 代码: {doc}\n")