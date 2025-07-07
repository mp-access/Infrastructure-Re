import torch
from transformers import AutoTokenizer, AutoModel

# Global variables for model and tokenizer to be loaded once
tokenizer = None
model = None
device = None


def load_model_and_tokenizer():

    global tokenizer, model, device
    if model is None:
        print("Loading GraphCodeBERT model and tokenizer...")
        model_link = "microsoft/graphcodebert-base"
        tokenizer = AutoTokenizer.from_pretrained(model_link, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_link, trust_remote_code=True)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()
        print(f"Model loaded successfully on device: {device}")


def calculate_code_embedding(code: str) -> list:

    if model is None or tokenizer is None:
        raise RuntimeError("Model and tokenizer not loaded. Call load_model_and_tokenizer() first.")

    inputs = tokenizer(code, padding=True, truncation=True, return_tensors="pt")
    inputs = {key: value.to(device) for key, value in inputs.items()}  # Move inputs to the correct device

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

    return code_embedding.squeeze().cpu().numpy().tolist()


# if __name__ == '__main__':
    # Example usage for testing purposes
    # load_model_and_tokenizer()
    # code_snippet = "def factorial(n):\n    if n == 0:\n        return 1\n    else:\n        return n * factorial(n-1)"
    # embedding = calculate_code_embedding(code_snippet)
    # print("Code Snippet:", code_snippet)
    # print("Embedding (first 5 elements):", embedding[:5])
    # print("Embedding length:", len(embedding))