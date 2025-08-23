# llm.py
import time
import logging
import onnxruntime as ort
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)

tokenizer = None
onnx_session = None

def load_model_and_tokenizer():
    global tokenizer, onnx_session

    model_link = "microsoft/graphcodebert-base"
    tokenizer = AutoTokenizer.from_pretrained(model_link, trust_remote_code=True)

    onnx_session = ort.InferenceSession(
        "graphcodebert_embedder_quantized.onnx",
        providers=["CPUExecutionProvider"]  # can add CUDAExecutionProvider if GPU available
    )
    logger.info("ONNX Runtime session initialized successfully.")

def calculate_code_embedding(code: str) -> list:
    global tokenizer, onnx_session

    if onnx_session is None or tokenizer is None:
        raise RuntimeError("Model and tokenizer not loaded. Call load_model_and_tokenizer() first.")

    start_time = time.time()

    inputs = tokenizer(code, return_tensors="np", padding=True, truncation=True)
    ort_inputs = {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"]
    }
    ort_outs = onnx_session.run(None, ort_inputs)
    embedding = ort_outs[0][0]  # shape [hidden_size]

    elapsed = (time.time() - start_time) * 1000
    logger.info(f"ONNX Inference time: {elapsed:.2f} ms")

    return embedding.tolist()
