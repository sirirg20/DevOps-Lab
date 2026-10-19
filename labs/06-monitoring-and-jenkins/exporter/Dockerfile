FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# `docker build --target test .` runs the unit tests; the pipeline uses this.
FROM base AS test
COPY simulator.py test_simulator.py ./
RUN python -m unittest -v

FROM base AS runtime
COPY simulator.py delivery_metrics.py ./
RUN useradd --no-create-home --uid 10001 appuser
USER appuser
EXPOSE 8000
CMD ["python", "delivery_metrics.py"]
