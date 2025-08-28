FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY services/enricher/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY data/weapon_list.txt /app/data
COPY services/enricher/ /app/services/enricher/
COPY shared/kafka_utils.py /app/shared/
COPY shared/text_processing.py /app/shared/
COPY shared/sentiment_analyzer.py /app/shared/
COPY shared/weapon_detector.py /app/shared/
COPY shared/timestamp_extractor.py /app/shared/
RUN chown -R appuser:appuser /app
USER appuser
CMD ["python", "services/enricher/app.py"]