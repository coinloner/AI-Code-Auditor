import os
import ast
import chromadb
from sympy.multipledispatch.dispatcher import source

client = chromadb.PersistentClient(path="./.chroma_db")
collection = client.get_or_create_collection(name="project_codebase")


class CodeKnowledgeBase:
    def __init__(self,db_path = "./.chroma_db", collection_name = "project_codebase"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.ignore_dirs = {".git", ".venv", "__pycache__", "node_modules", ".chroma_db"}

    def extract_chunks_from_file(self,filepath):
        with open(filepath, "r", encoding='utf-8') as f:
            source_code = f.read()

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            print(f"文件出现错误{filepath}")
            return [], [], []

        docs, metas, ids = [], [], []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                chunk_code = ast.get_source_segment(source_code, node)
                if not chunk_code:
                    continue

                node_type = "Class" if isinstance(node, ast.ClassDef) else "Function"
                meta = {
                    "file_path": filepath,
                    "node_type": node_type,
                    "node_name": node.name,
                    "start_line": node.lineno,
                }

                chunk_id = f"{filepath}::{node.name}::{node.lineno}"

                docs.append(chunk_code)
                metas.append(meta)
                ids.append(chunk_id)

        return docs, metas, ids

    def build_full_knowledge_base(self):
        all_docs, all_metas, all_ids = [], [], []

        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]

            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    docs, metas, ids = self.extract_chunks_from_file(filepath)

                    all_docs.extend(docs)
                    all_metas.extend(metas)
                    all_ids.extend(ids)

        if all_docs:
            print(f"共提取出 {len(all_docs)} 个逻辑代码块，准备打入向量数据库...")
            if collection.count() > 0:
                collection.delete(where={"file_path": {"$ne": ""}})

            collection.add(
                documents=all_docs,
                metadatas=all_metas,
                ids=all_ids
            )
            print("知识库构建完成")
        else:
            print("未找到合法类或函数")


    def add_file(self, filepath):
        docs, metas, ids = self.extract_chunks_from_file(filepath)
        if docs:
            self.collection.add(documents=docs, metadatas=metas, ids=ids)
            return len(docs)
        return 0

    def search_similar_code(self,query_text,n_results=5):
        docs, metas, ids = [], [], []

        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=query_text,
            n_results=n_results
        )

        return results['documents'][0] if results['documents'] else []

