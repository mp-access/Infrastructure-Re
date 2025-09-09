FROM python:3.10-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        libgl1 \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --upgrade pip

WORKDIR /app

COPY ./llm-microservice/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./llm-microservice/ .

RUN python3 export_to_onnx.py && rm graphcodebert_embedder.onnx

# should be the same as LLM_MICROSERVICE_PORT in .env
EXPOSE 4000

# port should be the same as LLM_MICROSERVICE_PORT in .env
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "4000"]
