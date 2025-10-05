# ---------- Stage 1: Build & export ONNX model ----------
FROM python:3.10-slim-bullseye AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        libgl1 \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --upgrade pip

WORKDIR /app

COPY ./llm-microservice/requirements-build.txt .
RUN pip install --no-cache-dir -r requirements-build.txt

COPY ./llm-microservice/ .
RUN python3 export_to_onnx.py

# ---------- Stage 2: Lightweight runtime ----------
FROM python:3.10-slim-bullseye

WORKDIR /app

COPY ./llm-microservice/requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt

COPY --from=builder /app/graphcodebert_embedder_quantized.onnx .
COPY ./llm-microservice/api.py ./llm-microservice/llm.py ./

EXPOSE 4000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "4000"]
