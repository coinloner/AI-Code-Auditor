# scripts/init_db.py
import sys
import os

# 这是一个工程小技巧：把项目的根目录强行加入系统路径
# 这样你在任何地方运行这个脚本，它都能顺利找到 Database 文件夹
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Database import vector_db


def main():
    print("=========================================")
    print("🚀 启动 [本地代码知识库] 全量构建程序...")
    print("=========================================")

    kb = vector_db.CodeKnowledgeBase()
    # 调用你之前封装好的全盘扫描黑盒方法
    kb.build_full_knowledge_base()

    print("=========================================")
    print("✅ 知识库构建完毕！现在 Worker 可以基于完整的上下文进行审查了。")
    print("=========================================")


if __name__ == "__main__":
    main()