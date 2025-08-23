import time
import logging

import torch
from transformers import AutoTokenizer, AutoModel

# Global variables for model and tokenizer to be loaded once
tokenizer = None
model = None
device = None

logger = logging.getLogger(__name__)

def load_model_and_tokenizer():

    global tokenizer, model, device
    if model is None:
        logger.info("Loading GraphCodeBERT model and tokenizer...")
        model_link = "microsoft/graphcodebert-base"
        tokenizer = AutoTokenizer.from_pretrained(model_link, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_link, trust_remote_code=True)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)

        if (torch.device == "cpu"):
            torch.backends.quantized.engine = "qnnpack" # "fbgemm" for x86 (Intel/AMD CPUs), "qnnpack" for ARM/Apple M-Chips
            model_quantized = torch.quantization.quantize_dynamic(
                model,
                {torch.nn.Linear},
                dtype=torch.qint8
            )
            model = model_quantized
            logger.info("Model quantized successfully.")

        model.eval()
        logger.info(f"Model loaded successfully on device: {device}")


def calculate_code_embedding(code: str) -> list:

    start_embedding_calculation = time.time()
    logger.info(f"Starting embedding calculation: {start_embedding_calculation}")

    if model is None or tokenizer is None:
        raise RuntimeError("Model and tokenizer not loaded. Call load_model_and_tokenizer() first.")

    inputs = tokenizer(code, padding=True, truncation=True, return_tensors="pt")
    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)  # contains an embedding vector for each token, including other additional information (such as the attention mask)
    last_hidden_states = outputs.last_hidden_state
    attention_mask = inputs['attention_mask']
    mask_expanded = attention_mask.unsqueeze(-1).expand(
        last_hidden_states.size()).float()  # expand attention mask to not use padded tokens for pooling
    sum_embeddings = torch.sum(last_hidden_states * mask_expanded, 1)  # by multiplying with the expanded mask (which is zero for padding tokens), we ignore the padding.
    sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)  # counts the number of real tokens in each sequence, replicated across the hidden size dimension. set minimum to prevent division by 0 error.
    mean_pooled_embedding = sum_embeddings / sum_mask  # computes the average of the non-padding token embeddings for each dimension and each sequence
    code_embedding = mean_pooled_embedding
    code_embedding = torch.nn.functional.normalize(code_embedding, p=2, dim=1)

    result = code_embedding.squeeze().cpu().numpy().tolist()

    end_embedding_calculation = time.time()
    logger.info(f"Ending embedding calculation: {end_embedding_calculation}")
    logger.info(f"RES: Time required: {(end_embedding_calculation - start_embedding_calculation) * 1000}ms")

    return result