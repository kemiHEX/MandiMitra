FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/services/api
WORKDIR /app
COPY services/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && useradd --create-home --uid 10001 appuser
COPY services/api services/api
COPY data data
RUN mkdir -p /app/runtime && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","1","--no-access-log"]
