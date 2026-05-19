import os
import ast
import chromadb
import subprocess




def find_project_root(starting_path=None):
    # 如果没指定，默认从执行命令的当前目录开始找
    if starting_path is None:
        starting_path = os.getcwd()

    current_dir = os.path.abspath(starting_path)

    # 工业界公认的项目根目录特征标志物
    # .git 是最权威的，其次是各种包管理配置文件
    root_markers = ['.git', 'requirements.txt', 'pyproject.toml', 'setup.py', '.venv']

    while current_dir != os.path.dirname(current_dir):  # 一直往上找，直到系统根目录 (如 /)
        for marker in root_markers:
            if os.path.exists(os.path.join(current_dir, marker)):
                return current_dir
        # 如果没找到，往上退一层继续找
        current_dir = os.path.dirname(current_dir)

    # 如果实在找不到任何特征，兜底方案：使用 Git 原生命令去问 (适用于隐藏得很深的子模块)
    try:
        git_root = subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=starting_path,
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        return git_root
    except Exception:
        pass

    # 如果上面所有方案全挂了，退化为最初始的运行目录
    return os.path.abspath(starting_path)


class CodeKnowledgeBase:
    def __init__(self,target_path=None,collection_name = "project_codebase"):
        self.project_root = target_path if target_path else find_project_root()

        self.data_dir = os.path.join(self.project_root, ".data")
        os.makedirs(self.data_dir, exist_ok=True)

        db_path = os.path.join(self.data_dir, "chroma_db")

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
            return [],[],[]

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

        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]

            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    docs, metas, ids = self.extract_chunks_from_file(filepath)

                    all_docs.extend(docs)
                    all_metas.extend(metas)
                    all_ids.extend(ids)

        if all_docs:
            print(f"共提取出 {len(all_docs)} 个逻辑代码块，分别是{all_docs}，准备打入向量数据库...")
            if self.collection.count() > 0:
                self.collection.delete(where={"file_path": {"$ne": ""}})

            self.collection.add(
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

