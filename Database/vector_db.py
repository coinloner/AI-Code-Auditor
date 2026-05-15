import os
import ast
import chromadb
from sympy.multipledispatch.dispatcher import source

IGNORE_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".chroma_db"}

def extract_chunks_from_file(filepath):
    with open(filepath,"r",encoding='utf-8') as f:
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
