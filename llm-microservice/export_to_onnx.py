# export_to_onnx.py
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
from onnxruntime.quantization import quantize_dynamic, QuantType

class GraphCodeBERTEmbedder(nn.Module):
    def __init__(self, model_link="microsoft/graphcodebert-base"):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_link, trust_remote_code=True)

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden_states = outputs.last_hidden_state
        # mean pooling to get a single embedding vector
        mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_states.size()).float()
        sum_embeddings = torch.sum(last_hidden_states * mask_expanded, 1)
        sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
        mean_pooled_embedding = sum_embeddings / sum_mask
        # normalize the embedding
        normed_embedding = torch.nn.functional.normalize(mean_pooled_embedding, p=2, dim=1)
        return normed_embedding

def export_model_and_quantize():
    model_link = "microsoft/graphcodebert-base"
    tokenizer = AutoTokenizer.from_pretrained(model_link, trust_remote_code=True)
    model = GraphCodeBERTEmbedder(model_link)
    model.eval()

    dummy_text = "def hello():\n    print('hello world')"
    inputs = tokenizer(dummy_text, return_tensors="pt")

    opset_version = 17
    input_names = ["input_ids", "attention_mask"]
    output_names = ["embedding"]

    model_fp32_path = "graphcodebert_embedder.onnx"
    model_quantized_path = "graphcodebert_embedder_quantized.onnx"

    # export the full-precision (FP32) ONNX model
    torch.onnx.export(
        model,
        (inputs["input_ids"], inputs["attention_mask"]),
        model_fp32_path,
        input_names=input_names,
        output_names=output_names,
        opset_version=opset_version,
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
        }
    )
    print(f"Exported full-precision model to {model_fp32_path}")

    # quantize the exported ONNX model
    quantize_dynamic(
        model_fp32_path,
        model_quantized_path,
        weight_type=QuantType.QInt8,
    )
    print(f"Quantized model saved to {model_quantized_path}")

if __name__ == "__main__":
    export_model_and_quantize()