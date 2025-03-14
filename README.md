# 25ss-lab1
# login_module
- 启动服务器:
    export PYTHONPATH=.
uvicorn login.main:app --reload
- 测试登陆：
    curl -X 'POST' \
  'http://127.0.0.1:8000/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "Ada",
  "password": "111"
}'
