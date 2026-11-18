import io
import urllib.error
from unittest.mock import MagicMock, patch
import pytest
import torch
from PIL import Image

from backend.app.services.clip_service import CLIPService, get_clip_service


def create_dummy_image(width: int = 32, height: int = 32, color: str = "red") -> Image.Image:
    """Helper to create an in-memory PIL image."""
    return Image.new("RGB", (width, height), color=color)


def create_dummy_image_bytes(format: str = "JPEG") -> bytes:
    """Helper to create dummy image bytes."""
    img = create_dummy_image()
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_clip_service_init_defaults():
    """Verify default initialization parameters and lazy loading behavior."""
    service = CLIPService()
    assert service.model_name == "openai/clip-vit-base-patch32"
    assert service.device in ("cpu", "cuda")
    assert service._model is None
    assert service._processor is None


def test_clip_service_custom_parameters():
    """Verify custom model name and device configuration."""
    service = CLIPService(model_name="custom/clip-model", device="cpu", lazy_load=True)
    assert service.model_name == "custom/clip-model"
    assert service.device == "cpu"
    assert service._model is None


def test_clip_service_ensure_model_loaded_success():
    """Verify model and processor are loaded via from_pretrained and put into eval mode."""
    service = CLIPService(lazy_load=True)

    mock_proc_cls = MagicMock()
    mock_model_cls = MagicMock()
    mock_model_instance = MagicMock()
    mock_model_instance.to.return_value = mock_model_instance
    mock_model_cls.from_pretrained.return_value = mock_model_instance

    with patch("backend.app.services.clip_service.CLIPProcessor", mock_proc_cls), \
         patch("backend.app.services.clip_service.CLIPModel", mock_model_cls):
        success = service._ensure_model_loaded()
        assert success is True
        assert service._model is mock_model_instance
        mock_model_cls.from_pretrained.assert_called_once_with(service.model_name)
        mock_model_instance.to.assert_called_once_with(service.device)
        mock_model_instance.eval.assert_called_once()


def test_clip_service_ensure_model_loaded_only_once():
    """Verify repeated calls reuse the existing model instance without reloading."""
    service = CLIPService(lazy_load=True)
    mock_proc_cls = MagicMock()
    mock_model_cls = MagicMock()
    mock_model_instance = MagicMock()
    mock_model_instance.to.return_value = mock_model_instance
    mock_model_cls.from_pretrained.return_value = mock_model_instance

    with patch("backend.app.services.clip_service.CLIPProcessor", mock_proc_cls), \
         patch("backend.app.services.clip_service.CLIPModel", mock_model_cls):
        assert service._ensure_model_loaded() is True
        assert service._ensure_model_loaded() is True
        # Model should only have been loaded once
        assert mock_model_cls.from_pretrained.call_count == 1


def test_clip_service_model_load_failure_handled_gracefully():
    """Verify graceful handling and False return when model weights fail to load."""
    service = CLIPService(lazy_load=True)

    with patch("backend.app.services.clip_service.CLIPProcessor.from_pretrained", side_effect=RuntimeError("Download failed")):
        success = service._ensure_model_loaded()
        assert success is False
        assert service._model is None
        assert service._processor is None


def test_load_image_from_pil_image():
    """Verify loading from an existing PIL Image converts RGBA to RGB."""
    service = CLIPService()
    rgba_image = Image.new("RGBA", (20, 20), color=(255, 0, 0, 128))
    loaded = service.load_image(rgba_image)
    assert loaded is not None
    assert loaded.mode == "RGB"
    assert loaded.size == (20, 20)


def test_load_image_from_bytes():
    """Verify loading image from raw bytes."""
    service = CLIPService()
    img_bytes = create_dummy_image_bytes(format="PNG")
    loaded = service.load_image(img_bytes)
    assert loaded is not None
    assert loaded.mode == "RGB"


def test_load_image_from_file_path(tmp_path):
    """Verify loading image from a local filesystem path."""
    service = CLIPService()
    img = create_dummy_image()
    file_path = tmp_path / "test_photo.jpg"
    img.save(file_path)

    loaded = service.load_image(str(file_path))
    assert loaded is not None
    assert loaded.mode == "RGB"


def test_load_image_file_not_found():
    """Verify non-existent file path safely returns None."""
    service = CLIPService()
    assert service.load_image("/path/to/nonexistent_file_12345.jpg") is None


def test_load_image_from_url_success():
    """Verify loading image from an HTTP/HTTPS URL."""
    service = CLIPService()
    img_bytes = create_dummy_image_bytes(format="JPEG")

    mock_resp = MagicMock()
    mock_resp.read.return_value = img_bytes
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        loaded = service.load_image("https://example.com/fort.jpg")
        assert loaded is not None
        assert loaded.mode == "RGB"


def test_load_image_from_url_failure():
    """Verify network failures downloading remote images return None safely."""
    service = CLIPService()
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        assert service.load_image("https://example.com/missing.jpg") is None


def test_load_image_corrupted_data():
    """Verify corrupted image bytes return None safely without raising exceptions."""
    service = CLIPService()
    assert service.load_image(b"not-a-valid-image-data-stream") is None


def test_load_image_none_or_empty():
    """Verify None or blank inputs return None safely."""
    service = CLIPService()
    assert service.load_image(None) is None
    assert service.load_image("") is None
    assert service.load_image("   ") is None


def test_compute_similarity_success():
    """Verify successful similarity calculation using mocked CLIP model and processor."""
    service = CLIPService(lazy_load=True)

    # Mock processor
    mock_proc = MagicMock()
    mock_proc.return_value = {
        "input_ids": torch.tensor([[101, 2023, 102]]),
        "pixel_values": torch.zeros((1, 3, 224, 224)),
        "attention_mask": torch.tensor([[1, 1, 1]]),
    }

    # Mock model features (normalized embeddings)
    mock_model = MagicMock()
    # Image vector: [1.0, 0.0], Text vector: [0.8, 0.6] -> dot product = 0.8
    mock_model.get_image_features.return_value = torch.tensor([[1.0, 0.0]])
    mock_model.get_text_features.return_value = torch.tensor([[0.8, 0.6]])

    service._processor = mock_proc
    service._model = mock_model

    dummy_img = create_dummy_image()
    score = service.compute_similarity(dummy_img, "A view of Aguada Fort in Goa")

    assert score is not None
    assert isinstance(score, float)
    assert pytest.approx(score, 0.001) == 0.8000


def test_compute_similarity_math_orthogonal_and_identical():
    """Verify mathematical correctness: identical vectors yield 1.0, orthogonal yield 0.0."""
    service = CLIPService(lazy_load=True)

    mock_proc = MagicMock()
    mock_proc.return_value = {
        "input_ids": torch.tensor([[101]]),
        "pixel_values": torch.zeros((1, 3, 224, 224)),
    }
    service._processor = mock_proc

    # Case A: Identical vectors
    mock_model_identical = MagicMock()
    mock_model_identical.get_image_features.return_value = torch.tensor([[3.0, 4.0]])
    mock_model_identical.get_text_features.return_value = torch.tensor([[3.0, 4.0]])
    service._model = mock_model_identical

    score_identical = service.compute_similarity(create_dummy_image(), "identical prompt")
    assert pytest.approx(score_identical, 0.0001) == 1.0000

    # Case B: Orthogonal vectors
    mock_model_orthogonal = MagicMock()
    mock_model_orthogonal.get_image_features.return_value = torch.tensor([[1.0, 0.0]])
    mock_model_orthogonal.get_text_features.return_value = torch.tensor([[0.0, 1.0]])
    service._model = mock_model_orthogonal

    score_orthogonal = service.compute_similarity(create_dummy_image(), "orthogonal prompt")
    assert pytest.approx(score_orthogonal, 0.0001) == 0.0000


def test_compute_similarity_empty_text():
    """Verify empty or whitespace-only text returns None."""
    service = CLIPService()
    dummy_img = create_dummy_image()
    assert service.compute_similarity(dummy_img, "") is None
    assert service.compute_similarity(dummy_img, "   ") is None


def test_compute_similarity_invalid_image():
    """Verify invalid image input returns None."""
    service = CLIPService()
    assert service.compute_similarity("invalid_image_path.jpg", "A fort") is None
    assert service.compute_similarity(None, "A fort") is None


def test_compute_similarity_model_load_failure():
    """Verify None is returned when the model cannot be loaded."""
    service = CLIPService(lazy_load=True)
    with patch.object(service, "_ensure_model_loaded", return_value=False):
        dummy_img = create_dummy_image()
        assert service.compute_similarity(dummy_img, "A fort") is None


def test_get_clip_service_singleton():
    """Verify get_clip_service provides a persistent singleton instance."""
    instance_1 = get_clip_service()
    instance_2 = get_clip_service()
    assert instance_1 is instance_2
    assert isinstance(instance_1, CLIPService)


def test_compute_batch_similarity_empty_list():
    """Verify empty image list immediately returns an empty list."""
    service = CLIPService()
    assert service.compute_batch_similarity([], "some place description") == []


def test_compute_batch_similarity_empty_text():
    """Verify empty or whitespace-only text returns a list of None preserving input length."""
    service = CLIPService()
    img1 = create_dummy_image()
    img2 = create_dummy_image()
    assert service.compute_batch_similarity([img1, img2], "") == [None, None]
    assert service.compute_batch_similarity([img1, img2], "   ") == [None, None]


def test_compute_batch_similarity_all_invalid_images():
    """Verify list of invalid images returns all None without crashing."""
    service = CLIPService()
    images = ["missing_1.jpg", None, b"invalid_bytes_data", "missing_2.png"]
    results = service.compute_batch_similarity(images, "A historical palace")
    assert results == [None, None, None, None]


def test_compute_batch_similarity_mixed_valid_and_invalid():
    """Verify batch processing preserves order and assigns scores to valid images while invalid stay None."""
    service = CLIPService(lazy_load=True)

    # 5 inputs: valid, None, valid, invalid path, valid
    valid_img_1 = create_dummy_image(color="red")
    valid_img_2 = create_dummy_image(color="green")
    valid_img_3 = create_dummy_image(color="blue")
    images = [valid_img_1, None, valid_img_2, "nonexistent_photo.jpg", valid_img_3]

    mock_proc = MagicMock()
    mock_proc.return_value = {
        "input_ids": torch.tensor([[101, 102]]),
        "pixel_values": torch.zeros((3, 3, 224, 224)),
    }

    mock_model = MagicMock()
    mock_model.get_text_features.return_value = torch.tensor([[1.0, 0.0]])
    # 3 valid images return 3 vectors: [1.0, 0.0] -> 1.0, [0.8, 0.6] -> 0.8, [0.0, 1.0] -> 0.0
    mock_model.get_image_features.return_value = torch.tensor([
        [1.0, 0.0],
        [0.8, 0.6],
        [0.0, 1.0],
    ])

    service._processor = mock_proc
    service._model = mock_model

    scores = service.compute_batch_similarity(images, "historical monument in Mumbai")

    assert len(scores) == 5
    assert pytest.approx(scores[0], 0.001) == 1.0000
    assert scores[1] is None
    assert pytest.approx(scores[2], 0.001) == 0.8000
    assert scores[3] is None
    assert pytest.approx(scores[4], 0.001) == 0.0000


def test_compute_batch_similarity_chunking_with_batch_size():
    """Verify batch_size correctly splits images into multiple forward passes."""
    service = CLIPService(lazy_load=True)

    # 5 valid images with batch_size=2 -> 3 chunks: [2, 2, 1]
    images = [create_dummy_image() for _ in range(5)]

    mock_proc = MagicMock()
    mock_proc.return_value = {
        "input_ids": torch.tensor([[101]]),
        "pixel_values": torch.zeros((2, 3, 224, 224)),
    }

    mock_model = MagicMock()
    mock_model.get_text_features.return_value = torch.tensor([[1.0, 0.0]])
    # Return 2 unit vectors for first 2 batches, 1 vector for last batch
    mock_model.get_image_features.side_effect = [
        torch.tensor([[1.0, 0.0], [0.6, 0.8]]),
        torch.tensor([[0.8, 0.6], [0.0, 1.0]]),
        torch.tensor([[-1.0, 0.0]]),
    ]

    service._processor = mock_proc
    service._model = mock_model

    scores = service.compute_batch_similarity(images, "heritage fort", batch_size=2)

    assert len(scores) == 5
    assert mock_model.get_image_features.call_count == 3
    assert pytest.approx(scores[0], 0.001) == 1.0000
    assert pytest.approx(scores[1], 0.001) == 0.6000
    assert pytest.approx(scores[2], 0.001) == 0.8000
    assert pytest.approx(scores[3], 0.001) == 0.0000
    assert pytest.approx(scores[4], 0.001) == -1.0000


def test_compute_batch_similarity_model_load_failure():
    """Verify batch processing returns all None when model fails to load."""
    service = CLIPService(lazy_load=True)
    with patch.object(service, "_ensure_model_loaded", return_value=False):
        images = [create_dummy_image(), create_dummy_image()]
        assert service.compute_batch_similarity(images, "museum") == [None, None]


def test_compute_batch_similarity_inference_error_handled_gracefully():
    """Verify unexpected forward pass errors return list of None rather than raising exceptions."""
    service = CLIPService(lazy_load=True)
    mock_proc = MagicMock()
    mock_proc.side_effect = RuntimeError("CUDA OOM or CPU tensor error")
    service._processor = mock_proc
    service._model = MagicMock()

    images = [create_dummy_image(), create_dummy_image()]
    scores = service.compute_batch_similarity(images, "scenic garden")
    assert scores == [None, None]

