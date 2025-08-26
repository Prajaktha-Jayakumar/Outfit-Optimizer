"""CLIP-based zero-shot clothing classifier returning both label and embedding."""

import os
import torch
import numpy as np
from transformers import CLIPModel, CLIPProcessor
from PIL import Image
from typing import Tuple, Dict

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

CLASS_PROMPTS = {
    "top": [
        "a photo of a t-shirt",
        "a photo of a shirt",
        "a photo of a blouse",
        "a photo of a sweater",
        "a photo of a hoodie",
    ],
    "bottom": [
        "a photo of jeans",
        "a photo of trousers",
        "a photo of pants",
        "a photo of a skirt",
        "a photo of shorts",
    ],
    "shoes": [
        "a pair of sneakers",
        "a pair of shoes",
        "a pair of boots",
        "a pair of loafers",
    ],
    "jacket": [
        "a photo of a jacket",
        "a photo of a coat",
        "a photo of a blazer",
        "a photo of a cardigan",
    ],
}

_model = None
_processor = None
_text_embeds = None
_label_index = None


def _ensure_loaded():
    global _model, _processor, _text_embeds, _label_index
    if _model is not None:
        return
    
    model_name = os.environ.get("CLIP_MODEL", "openai/clip-vit-base-patch32")
    _model = CLIPModel.from_pretrained(model_name).to(DEVICE)
    _processor = CLIPProcessor.from_pretrained(model_name)
    
    prompts, label_index = [], []
    for label, variants in CLASS_PROMPTS.items():
        for v in variants:
            prompts.append(v)
            label_index.append(label)
    
    inputs = _processor(text=prompts, images=None, return_tensors="pt", padding=True)
    with torch.no_grad():
        text_features = _model.get_text_features(**{k: v.to(DEVICE) for k, v in inputs.items()})
        text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
    
    _text_embeds = text_features
    _label_index = label_index


def classify_image(image_path: str) -> Tuple[str, "np.ndarray"]:
    """Return (best_label, 512-dim CLIP image embedding as np.ndarray)."""
    _ensure_loaded()
    global _model, _processor, _text_embeds, _label_index
    
    image = Image.open(image_path).convert("RGB")
    inputs = _processor(images=image, return_tensors="pt")
    
    with torch.no_grad():
        image_features = _model.get_image_features(**{k: v.to(DEVICE) for k, v in inputs.items()})
        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
    
    sims = image_features @ _text_embeds.T
    sims = sims.squeeze(0).float().cpu()
    
    # Aggregate per canonical label
    scores = {}
    for score, label in zip(sims.tolist(), _label_index):
        scores[label] = max(scores.get(label, float("-inf")), score)
    
    best_label = max(scores.items(), key=lambda x: x[1])[0]
    embedding = image_features.squeeze(0).cpu().numpy().astype("float32")
    
    return best_label, embedding