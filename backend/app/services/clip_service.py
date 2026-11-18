from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import List, Optional, Union
import urllib.error
import urllib.request

try:
    import torch
    import torch.nn.functional as F
    from PIL import Image, UnidentifiedImageError
    from transformers import CLIPModel, CLIPProcessor
    _ML_DEPS_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]
    UnidentifiedImageError = ValueError  # type: ignore[assignment,misc]
    CLIPModel = None  # type: ignore[assignment,misc]
    CLIPProcessor = None  # type: ignore[assignment,misc]
    _ML_DEPS_AVAILABLE = False

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "openai/clip-vit-base-patch32"
_clip_service_instance: Optional["CLIPService"] = None


def _extract_feature_tensor(features: Union[torch.Tensor, object]) -> torch.Tensor:
    """Extract a 2D feature tensor whether returned as a raw Tensor or BaseModelOutputWithPooling."""
    if hasattr(features, "pooler_output") and features.pooler_output is not None:
        return features.pooler_output
    if hasattr(features, "last_hidden_state") and features.last_hidden_state is not None:
        return features.last_hidden_state[:, 0, :]
    if torch is not None and isinstance(features, torch.Tensor):
        return features
    if isinstance(features, (tuple, list)):
        return features[0]
    return features


class CLIPService:
    """Standalone service for semantic image-text relevance verification using CLIP."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        device: Optional[str] = None,
        lazy_load: bool = True,
    ):
        self.model_name = model_name
        if device is not None:
            self.device = device
        elif torch is not None and torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        self._model: Optional[CLIPModel] = None
        self._processor: Optional[CLIPProcessor] = None

        if not lazy_load:
            self._ensure_model_loaded()

    @property
    def is_available(self) -> bool:
        """Whether optional ML dependencies required for CLIP scoring are available."""
        return bool(
            _ML_DEPS_AVAILABLE
            and torch is not None
            and F is not None
            and Image is not None
            and CLIPModel is not None
            and CLIPProcessor is not None
        )

    def _ensure_model_loaded(self) -> bool:
        """Load the CLIP model and processor if not already loaded into memory."""
        if self._model is not None and self._processor is not None:
            return True

        if not self.is_available:
            logger.warning(
                "Optional ML dependencies (torch, transformers, pillow) are unavailable; skipping CLIP loading."
            )
            return False

        try:
            logger.info(f"Loading CLIP model and processor: '{self.model_name}' on {self.device}...")
            self._processor = CLIPProcessor.from_pretrained(self.model_name)
            self._model = CLIPModel.from_pretrained(self.model_name).to(self.device)
            self._model.eval()
            logger.info("CLIP model and processor loaded successfully.")
            return True
        except Exception as exc:
            logger.error(f"Failed to load CLIP model '{self.model_name}': {exc}")
            self._model = None
            self._processor = None
            return False

    def load_image(
        self,
        image_input: Union[Image.Image, str, Path, bytes],
        timeout: int = 10,
    ) -> Optional[Image.Image]:
        """Convert various image inputs (PIL Image, path, bytes, or HTTP URL) into an RGB PIL Image."""
        if image_input is None or Image is None:
            return None

        try:
            # 1. Already a PIL Image
            if isinstance(image_input, Image.Image):
                return image_input.convert("RGB") if image_input.mode != "RGB" else image_input

            # 2. Raw bytes
            if isinstance(image_input, (bytes, bytearray)):
                img = Image.open(io.BytesIO(image_input))
                return img.convert("RGB")

            # 3. Path or URL string
            if isinstance(image_input, (str, Path)):
                str_path = str(image_input).strip()
                if not str_path:
                    return None

                # Remote HTTP/HTTPS URL
                if str_path.lower().startswith(("http://", "https://")):
                    req = urllib.request.Request(
                        str_path,
                        headers={
                            "User-Agent": "VirtualTravelAgent/1.0 (https://github.com/travel-agentic; contact: admin@travelagentic.local)"
                        },
                    )
                    with urllib.request.urlopen(req, timeout=timeout) as response:
                        img_bytes = response.read()
                    img = Image.open(io.BytesIO(img_bytes))
                    return img.convert("RGB")

                # Local filesystem path
                local_path = Path(str_path)
                if local_path.is_file():
                    img = Image.open(local_path)
                    return img.convert("RGB")
                else:
                    logger.warning(f"Image file not found at path: {str_path}")
                    return None

        except (UnidentifiedImageError, ValueError) as exc:
            logger.warning(f"Unidentified or corrupted image input: {exc}")
            return None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            logger.warning(f"Network error fetching image from URL: {exc}")
            return None
        except Exception as exc:
            logger.error(f"Unexpected error loading image: {exc}")
            return None

        return None

    def compute_batch_similarity(
        self,
        images: List[Union[Image.Image, str, Path, bytes]],
        text: str,
        timeout: int = 10,
        batch_size: int = 16,
    ) -> List[Optional[float]]:
        """Compute cosine similarity scores between multiple images and a shared text description.

        Args:
            images: List of PIL Images, local file paths, raw bytes, or HTTP URLs.
            text: Shared text prompt or place description.
            timeout: Network timeout for downloading remote images.
            batch_size: Maximum number of images to process in a single model forward pass.

        Returns:
            List of float scores (between -1.0 and 1.0) or None for invalid images,
            preserving the exact input order.
        """
        if not images:
            return []

        results: list = [None] * len(images)

        if not text or not text.strip():
            logger.warning("Empty text description provided for CLIP batch similarity.")
            return results

        if not self._ensure_model_loaded() or torch is None or F is None:
            logger.error("CLIP model is not available for batch computation.")
            return results

        # 1. Load images while tracking their original indices
        valid_indices = []
        valid_pil_images = []

        for idx, img_input in enumerate(images):
            pil_img = self.load_image(img_input, timeout=timeout)
            if pil_img is not None:
                valid_indices.append(idx)
                valid_pil_images.append(pil_img)

        if not valid_pil_images:
            logger.warning("No valid images could be loaded for CLIP batch similarity.")
            return results

        try:
            with torch.inference_mode():
                # 2. Encode shared text prompt once
                text_inputs = self._processor(
                    text=[text.strip()],
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                )
                text_inputs = {k: v.to(self.device) for k, v in text_inputs.items()}

                raw_text_features = self._model.get_text_features(
                    input_ids=text_inputs["input_ids"],
                    attention_mask=text_inputs.get("attention_mask"),
                )
                text_features = _extract_feature_tensor(raw_text_features)
                text_features = F.normalize(text_features, p=2, dim=-1)  # Shape: (1, 512)

                # 3. Process valid images in batches of batch_size
                step = max(1, batch_size)
                for start in range(0, len(valid_pil_images), step):
                    end = start + step
                    batch_imgs = valid_pil_images[start:end]
                    batch_idxs = valid_indices[start:end]

                    image_inputs = self._processor(
                        images=batch_imgs,
                        return_tensors="pt",
                    )
                    image_inputs = {k: v.to(self.device) for k, v in image_inputs.items()}

                    raw_image_features = self._model.get_image_features(
                        pixel_values=image_inputs["pixel_values"]
                    )
                    image_features = _extract_feature_tensor(raw_image_features)
                    image_features = F.normalize(image_features, p=2, dim=-1)  # Shape: (B, 512)

                    # Matrix multiplication gives (B, 1) dot products
                    sims = torch.matmul(image_features, text_features.t()).view(-1)

                    for orig_idx, sim_val in zip(batch_idxs, sims.tolist()):
                        results[orig_idx] = round(float(sim_val), 4)

            return results

        except Exception as exc:
            logger.error(f"Error computing CLIP batch similarity: {exc}")
            return results

    def compute_similarity(
        self,
        image: Union[Image.Image, str, Path, bytes],
        text: str,
        timeout: int = 10,
    ) -> Optional[float]:
        """Compute the cosine similarity score between an image and a text description.

        Args:
            image: PIL Image, local file path, raw bytes, or image URL.
            text: Text prompt or place description.
            timeout: Network timeout for downloading remote image.

        Returns:
            Cosine similarity score as float (between -1.0 and 1.0), or None on failure.
        """
        results = self.compute_batch_similarity([image], text, timeout=timeout, batch_size=1)
        return results[0] if results else None


def get_clip_service() -> CLIPService:
    """Singleton provider for CLIPService."""
    global _clip_service_instance
    if _clip_service_instance is None:
        _clip_service_instance = CLIPService()
    return _clip_service_instance

