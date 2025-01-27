FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server_deepseek/ ./mcp_server_deepseek/

EXPOSE 3000

CMD ["python", "-m", "mcp_server_deepseek.server"]