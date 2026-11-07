"""Optional local transformer rewriting. Models download on first use."""
import os
from functools import lru_cache

DEFAULT_MODEL = "vennify/t5-base-grammar-correction"

@lru_cache(maxsize=1)
def _pipeline():
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError("Install optional ML requirements: pip install -r requirements-ml.txt") from exc
    model_name = os.getenv("LEXIGUARD_ML_MODEL", DEFAULT_MODEL)
    try:
        return pipeline("text2text-generation", model=model_name, tokenizer=model_name, device=-1)
    except Exception as exc:
        raise RuntimeError(f"Unable to load {model_name}. Check model availability and internet connection: {exc}") from exc

def rewrite(text: str) -> str:
    if not text.strip():
        return text
    model = _pipeline()
    # Chunk input on approximate sentence boundaries; short contexts suit T5 best.
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 > 450 and current:
            chunks.append(current)
            current = ""
        current = (current + " " + sentence).strip()
    if current:
        chunks.append(current)
    outputs = []
    for chunk in chunks:
        if len(chunk) > 2000:
            raise ValueError("A single sentence is too long for the default local model. Split it into shorter sentences.")
        response = model("grammar: " + chunk, max_new_tokens=256, num_beams=4, do_sample=False, truncation=True)
        outputs.append(response[0]["generated_text"].strip())
    return " ".join(outputs)
