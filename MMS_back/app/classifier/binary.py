"""Team Member A — RoBERTa-base binary toxicity classifier."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

from app.schemas.classification import BinaryLabel
from app.schemas.post import Post

logger = logging.getLogger(__name__)

# Model artifacts dir: defaults to model_assets/ next to this file.
# Override with MMS_BINARY_MODEL_DIR env var when artifacts live elsewhere.
_MODEL_DIR = Path(
    os.environ.get("MMS_BINARY_MODEL_DIR", Path(__file__).parent / "model_assets")
)

_MAX_LEN = 96  # must match config.MAX_LEN used during training


def _clean_text(text: str) -> str:
    """Mirrors model/dataset.py:clean_text exactly."""
    text = str(text)
    text = re.sub(r"http\S+", "[URL]", text)
    text = re.sub(r"@\w+", "[USER]", text)
    text = re.sub(r"&amp;|&lt;|&gt;|&quot;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class TeamBinaryClassifier:
    """RoBERTa-base fine-tuned on Hatebase + Jigsaw; stage-1 gate."""

    version = "team-binary-v1"

    def __init__(self) -> None:
        """Load tokenizer, model weights, and the val-calibrated decision threshold."""
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self._torch = torch
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.threshold = float(
            json.loads((_MODEL_DIR / "results.json").read_text())["threshold"]
        )

        self.tokenizer = AutoTokenizer.from_pretrained(str(_MODEL_DIR / "tokenizer"))

        # Load roberta-base architecture, then overwrite with fine-tuned weights.
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "roberta-base", num_labels=1
        )
        state = torch.load(_MODEL_DIR / "best_model.pt", map_location=self.device)
        # best_model.pt is saved in fp16; restore to fp32 for inference.
        state = {k: v.float() if v.is_floating_point() else v for k, v in state.items()}
        self.model.load_state_dict(state)
        self.model.to(self.device)
        self.model.eval()
        logger.info("TeamBinaryClassifier loaded | device=%s | threshold=%.2f", self.device, self.threshold)

    def classify(self, post: Post) -> BinaryLabel:
        """Return a BinaryLabel for the post."""
        with self._torch.no_grad():
            cleaned = _clean_text(post.text)
            enc = self.tokenizer(
                cleaned,
                max_length=_MAX_LEN,
                padding=True,
                truncation=True,
                return_tensors="pt",
            )
            inputs = {k: v.to(self.device) for k, v in enc.items()}
            logit = self.model(**inputs).logits.squeeze(-1)
            score = float(self._torch.sigmoid(logit).cpu())
        label = BinaryLabel(
            is_harmful=score >= self.threshold,
            score=round(score, 4),
            model_version=self.version,
        )
        logger.info("classify | post_id=%s | score=%.4f | is_harmful=%s", post.id, score, label.is_harmful)
        return label
