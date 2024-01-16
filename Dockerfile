# 使用 Python 官方的镜像作为基础镜像
FROM python:3.9

# 设置工作目录
WORKDIR /app

# 复制应用代码到容器中
COPY . /app

# 安装应用依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露应用端口
EXPOSE 5000

# 定义容器启动命令
CMD ["python", "app.py"]
