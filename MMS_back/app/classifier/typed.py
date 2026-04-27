"""Team Member B's multi-class harm-type classifier hook-in point."""

from __future__ import annotations

import contextlib
import os
from pathlib import Path
from typing import Any

from app.config import model_dir
from app.schemas.classification import HarmType, TypeLabel
from app.schemas.post import Post


DEVICE_ENV = "MMS_TYPED_DEVICE"

FALLBACK_HARMFUL_COLS = ["toxic", "obscene", "threat", "insult", "identity_hate"]
FALLBACK_MORAL_ID2LABEL = {
    0: "harm",
    1: "disrespect",
    2: "discrimination",
}
FALLBACK_SEVERITY_ID2LABEL = {
    0: "low",
    1: "medium",
    2: "high",
}


def _normalize_id2label(mapping: dict[Any, str]) -> dict[int, str]:
    """Convert checkpoint label keys back to integer ids."""
    return {int(k): v for k, v in mapping.items()}


def _strategy_hint(harm_type: HarmType) -> str | None:
    """Return the responder strategy key for a predicted harm type."""
    hints = {
        HarmType.HATE: "persuade/hate",
        HarmType.CYBERBULLYING: "persuade/cyberbullying",
        HarmType.MISINFORMATION: "persuade/misinfo",
        HarmType.DEPRESSIVE: "counsel/system",
        HarmType.SELF_HARM: "counsel/system",
    }
    return hints.get(harm_type)


def _load_torch_runtime() -> tuple[Any, Any, Any, Any]:
    """Import heavy ML dependencies only when the team implementation is used."""
    try:
        import torch
        import torch.nn as nn
        from transformers import AutoModel, AutoTokenizer
        from transformers.utils import logging as transformers_logging
    except ImportError as exc:
        raise RuntimeError(
            "TeamTypedClassifier requires torch and transformers. "
            "Install them in the backend environment or run with MMS_C2_IMPL=dummy."
        ) from exc

    transformers_logging.set_verbosity_error()
    return torch, nn, AutoModel, AutoTokenizer


def _build_model_class(nn: Any, AutoModel: Any):
    """Build the checkpoint-compatible PyTorch model class."""

    class MLPHead(nn.Module):
        """Small MLP classification head used by the training script."""

        def __init__(self, input_dim: int, output_dim: int, dropout: float):
            """Create one task head."""
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_dim, input_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(input_dim, output_dim),
            )

        def forward(self, x):
            """Run the head on pooled encoder features."""
            return self.net(x)

    class MultiTaskBERT(nn.Module):
        """Checkpoint-compatible multi-task text classifier."""

        def __init__(
            self,
            model_name: str,
            num_harmful_labels: int,
            num_moral_labels: int,
            num_severity_labels: int,
            dropout: float = 0.3,
        ):
            """Create the encoder and three task heads."""
            super().__init__()
            with open(os.devnull, "w", encoding="utf-8") as devnull:
                with contextlib.redirect_stderr(devnull):
                    self.encoder = AutoModel.from_pretrained(model_name)
            hidden_size = self.encoder.config.hidden_size

            self.dropout = nn.Dropout(dropout)
            self.harmful_head = MLPHead(hidden_size, num_harmful_labels, dropout)
            self.moral_head = MLPHead(hidden_size, num_moral_labels, dropout)
            self.severity_head = MLPHead(hidden_size, num_severity_labels, dropout)

        @staticmethod
        def mean_pooling(last_hidden_state, attention_mask):
            """Mean-pool token embeddings with the attention mask."""
            mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
            masked_hidden = last_hidden_state * mask
            summed = masked_hidden.sum(dim=1)
            counts = mask.sum(dim=1).clamp(min=1e-9)
            return summed / counts

        def forward(self, input_ids, attention_mask, token_type_ids=None):
            """Return logits for harmful, moral, and severity tasks."""
            if token_type_ids is not None:
                outputs = self.encoder(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    token_type_ids=token_type_ids,
                )
            else:
                outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)

            pooled = self.mean_pooling(outputs.last_hidden_state, attention_mask)
            pooled = self.dropout(pooled)
            return (
                self.harmful_head(pooled),
                self.moral_head(pooled),
                self.severity_head(pooled),
            )

    return MultiTaskBERT


class TeamTypedClassifier:
    """RoBERTa-based implementation of the Member B typed classifier."""

    version = "team-typed-roberta-v1"

    def __init__(self) -> None:
        """Load the saved checkpoint, tokenizer, thresholds, and label mapping."""
        self.torch, nn, AutoModel, AutoTokenizer = _load_torch_runtime()
        self.device = self.torch.device(
            os.getenv(
                DEVICE_ENV,
                "cuda" if self.torch.cuda.is_available() else "cpu",
            )
        )
        self.model_dir = model_dir("classifier_typed").resolve()
        checkpoint_path = self.model_dir / "best_model.pt"
        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"Cannot find typed classifier checkpoint: {checkpoint_path}. "
                f"Default path is models/classifier_typed/ at the repo root. "
                f"Set MMS_CLASSIFIER_TYPED_DIR only if the model directory is elsewhere."
            )

        checkpoint = self._load_checkpoint(checkpoint_path)
        self.model_name = checkpoint.get("model_name", "roberta-base")
        self.max_len = int(checkpoint.get("max_len", 256))
        self.harmful_cols = checkpoint.get("harmful_cols", FALLBACK_HARMFUL_COLS)
        self.moral_id2label = _normalize_id2label(
            checkpoint.get("moral_id2label", FALLBACK_MORAL_ID2LABEL)
        )
        self.severity_id2label = _normalize_id2label(
            checkpoint.get("severity_id2label", FALLBACK_SEVERITY_ID2LABEL)
        )
        self.harmful_thresholds = [
            float(x) for x in checkpoint.get("harmful_thresholds", [0.5] * len(self.harmful_cols))
        ]

        MultiTaskBERT = _build_model_class(nn, AutoModel)
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
        self.model = MultiTaskBERT(
            model_name=self.model_name,
            num_harmful_labels=len(self.harmful_cols),
            num_moral_labels=len(self.moral_id2label),
            num_severity_labels=len(self.severity_id2label),
        )
        self.model.load_state_dict(checkpoint.get("model_state_dict", checkpoint))
        self.model.to(self.device)
        self.model.eval()

    def _load_checkpoint(self, checkpoint_path: Path) -> dict[str, Any]:
        """Load a checkpoint across PyTorch versions."""
        try:
            return self.torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        except TypeError:
            return self.torch.load(checkpoint_path, map_location=self.device)

    def categorize(self, post: Post) -> TypeLabel:
        """Return the most suitable downstream HarmType for a post."""
        prediction = self._predict(post.text)
        harm_type, score = self._map_prediction_to_harm_type(prediction)
        return TypeLabel(
            harm_type=harm_type,
            score=score,
            strategy_hint=_strategy_hint(harm_type),
            model_details=prediction,
            model_version=self.version,
        )

    def _predict(self, text: str) -> dict[str, Any]:
        """Run the saved multi-task model on one text string."""
        encoding = self.tokenizer(
            [text],
            truncation=True,
            padding=True,
            max_length=self.max_len,
            return_tensors="pt",
        )
        encoding = {key: value.to(self.device) for key, value in encoding.items()}

        with self.torch.no_grad():
            harmful_logits, moral_logits, severity_logits = self.model(**encoding)
            harmful_probs_tensor = self.torch.sigmoid(harmful_logits)
            thresholds = self.torch.tensor(
                self.harmful_thresholds,
                device=self.device,
            ).view(1, -1)
            harmful_preds = (harmful_probs_tensor >= thresholds).long()
            harmful_probs = harmful_probs_tensor[0].detach().cpu().tolist()
            harmful_predictions = harmful_preds[0].detach().cpu().tolist()
            moral_probs = self.torch.softmax(moral_logits, dim=1)[0].detach().cpu().tolist()
            severity_probs = self.torch.softmax(severity_logits, dim=1)[0].detach().cpu().tolist()
            moral_id = int(self.torch.argmax(moral_logits, dim=1).item())
            severity_id = int(self.torch.argmax(severity_logits, dim=1).item())

        return {
            "harmful": {
                label: {
                    "probability": float(harmful_probs[i]),
                    "prediction": int(harmful_predictions[i]),
                    "threshold": float(self.harmful_thresholds[i]),
                }
                for i, label in enumerate(self.harmful_cols)
            },
            "moral": {
                "label": self.moral_id2label[moral_id],
                "probabilities": {
                    self.moral_id2label[i]: float(prob) for i, prob in enumerate(moral_probs)
                },
            },
            "severity": {
                "label": self.severity_id2label[severity_id],
                "probabilities": {
                    self.severity_id2label[i]: float(prob)
                    for i, prob in enumerate(severity_probs)
                },
            },
        }

    def _map_prediction_to_harm_type(self, prediction: dict[str, Any]) -> tuple[HarmType, float]:
        """Map model-specific labels to the MMS harm taxonomy."""
        harmful_probs = {
            label: details["probability"]
            for label, details in prediction["harmful"].items()
        }
        moral_probs = prediction["moral"]["probabilities"]

        discrimination = moral_probs.get("discrimination", 0.0)
        identity_hate = harmful_probs.get("identity_hate", 0.0)
        if discrimination >= 0.5 or identity_hate >= self._threshold_for("identity_hate"):
            return HarmType.HATE, min(1.0, max(discrimination, identity_hate))

        threat = harmful_probs.get("threat", 0.0)
        if threat >= self._threshold_for("threat"):
            return HarmType.OTHER, min(1.0, threat)

        bullying_scores = [
            moral_probs.get("disrespect", 0.0),
            harmful_probs.get("toxic", 0.0),
            harmful_probs.get("obscene", 0.0),
            harmful_probs.get("insult", 0.0),
        ]
        bullying_score = max(bullying_scores)
        if bullying_score >= 0.5:
            return HarmType.CYBERBULLYING, min(1.0, bullying_score)

        generic_harm = moral_probs.get("harm", 0.0)
        if generic_harm >= 0.5:
            return HarmType.OTHER, min(1.0, generic_harm)

        return HarmType.OTHER, min(1.0, max(harmful_probs.values(), default=0.0))

    def _threshold_for(self, label: str) -> float:
        """Return the validation-tuned threshold for one harmful label."""
        if label not in self.harmful_cols:
            return 0.5
        return self.harmful_thresholds[self.harmful_cols.index(label)]
