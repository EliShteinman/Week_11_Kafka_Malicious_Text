FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY services/retriever/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/retriever/ /app/services/retriever/
COPY shared/kafka_utils.py /app/shared/
COPY shared/mongo_utils.py /app/shared/
RUN chown -R appuser:appuser /app
USER appuser
CMD ["python", "services/retriever/app.py"]