FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1\
    PYTHONPATH=/app
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY services/data_retrieval/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/__init__.py /app/services/
COPY services/data_retrieval/ /app/services/data_retrieval/
COPY shared/mongo_utils.py /app/shared/
COPY shared/__init__.py /app/shared/
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8082
CMD ["uvicorn", "services.data_retrieval.app:app","--reload", "--host", "0.0.0.0", "--port", "8082"]