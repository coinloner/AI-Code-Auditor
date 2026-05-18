import subprocess
import json
import urllib.request
import sys

diff_process = subprocess.run(
    ["git", "diff", "HEAD~1", "HEAD", "-U5"],
    capture_output=True,
    text=True,
)
diff_content = diff_process.stdout.strip()

if not diff_content:
    sys.exit(0)

url = "http://127.0.0.1:8000/submit_review"
data = json.dumps({"diff_content": diff_content}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

try:
    response = urllib.request.urlopen(req, timeout=5)
    result = json.loads(response.read().decode('utf-8'))
    print(f"✅ 发送成功: {result['message']}")
except Exception as e:
    print(f"无法连接 AI 审查微服务，请检查服务是否开启: {e}")
