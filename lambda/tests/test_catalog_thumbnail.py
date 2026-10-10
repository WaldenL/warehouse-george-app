"""Offline contract tests for the generative catalog thumbnail stage."""
import base64
import importlib.util
import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

# Avoid loading the heavy segmentation runtime for a unit test of the image API.
sys.modules["rembg"] = types.SimpleNamespace(remove=None, new_session=None)
app_path = Path(__file__).resolve().parents[1] / "app.py"
spec = importlib.util.spec_from_file_location("warehouse_worker", app_path)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class CatalogThumbnailTests(unittest.TestCase):
    def setUp(self):
        self.cfg = {"OPENAI_API_KEY": "test-key"}
        self.run = {"id": "run-uuid", "bottle_id": "bottle-uuid"}
        self.photos = [
            Image.new("RGBA", (240, 400), (80, 50, 20, 255)),
            Image.new("RGBA", (250, 450), (90, 40, 30, 255)),
        ]
        self.brief = {
            "canonical_photo_numbers": [2, 1],
            "strategy": "balanced",
            "identity_anchors": ["Unusual violet closure", "Special neck label"],
        }

    @patch.object(worker, "storage")
    @patch.object(worker.requests, "post")
    def test_generates_from_references_and_archives_separately(self, post, storage):
        output = io.BytesIO()
        Image.new("RGB", (1024, 1536), (220, 215, 210)).save(output, "PNG")
        response = post.return_value
        response.ok = True
        response.json.return_value = {
            "data": [{"b64_json": base64.b64encode(output.getvalue()).decode()}],
            "usage": {"total_tokens": 100},
        }

        result = worker.generate_catalog_thumbnail(self.cfg, self.run, self.photos, self.brief)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["source_photo_numbers"], [2, 1])
        self.assertEqual(result["size"], [1024, 1536])
        self.assertEqual(result["usage"], {"total_tokens": 100})
        self.assertEqual(result["full_image_path"],
                         "bottles/bottle-uuid/generated/run-uuid/catalog.png")
        self.assertEqual(result["preview_path"],
                         "bottles/bottle-uuid/generated/run-uuid/preview.png")
        self.assertEqual(storage.call_count, 2)
        self.assertEqual(storage.call_args_list[0].args[2], "warehouse-media")
        self.assertEqual(storage.call_args_list[1].args[2], "warehouse-thumbnails")
        self.assertEqual(self.photos[0].size, (240, 400))
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["data"]["model"], worker.IMAGE_MODEL)
        self.assertEqual(len(kwargs["files"]), 2)
        self.assertIn("Unusual violet closure", kwargs["data"]["prompt"])
        self.assertNotIn("application/json", kwargs.get("headers", {}).values())

    @patch.object(worker.requests, "post")
    def test_invalid_reference_does_not_call_image_api(self, post):
        with self.assertRaises(ValueError):
            worker.generate_catalog_thumbnail(self.cfg, self.run, self.photos,
                                              {"canonical_photo_numbers": [3]})
        post.assert_not_called()

    @patch.object(worker, "storage")
    @patch.object(worker.requests, "post")
    def test_missing_image_fails_without_writing_storage(self, post, storage):
        response = post.return_value
        response.ok = True
        response.json.return_value = {"data": []}
        with self.assertRaises(ValueError):
            worker.generate_catalog_thumbnail(self.cfg, self.run, self.photos, self.brief)
        storage.assert_not_called()


if __name__ == "__main__":
    unittest.main()
