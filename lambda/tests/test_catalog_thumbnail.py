"""Offline contracts: photographed front/back, archival separation, and run costs."""
import base64
import importlib.util
import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

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
            Image.new("RGBA", (240, 400), (90, 70, 30, 255)),
        ]
        self.brief = {
            "strategy": "label_forward",
            "canonical_photo_numbers": [1, 3],
            "front_photo_numbers": [1, 3],
            "back_photo_numbers": [2],
            "identity_anchors": ["Unusual violet closure"],
            "front_identity_anchors": ["Private-selection front label"],
            "back_identity_anchors": ["Barrel information on back"],
            "optional_anchors": [],
            "simplifications_allowed": ["Microscopic legal print"],
            "front_notes": None,
            "back_notes": "Keep the rear label on the rear only.",
            "notes": None,
        }

    def image_response(self, post):
        output = io.BytesIO()
        Image.new("RGB", (1024, 1536), (220, 215, 210)).save(output, "PNG")
        response = post.return_value
        response.ok = True
        response.json.return_value = {
            "data": [{"b64_json": base64.b64encode(output.getvalue()).decode()}],
            "usage": {
                "input_tokens_details": {"text_tokens": 600, "image_tokens": 1600},
                "output_tokens_details": {"image_tokens": 1372},
            },
        }

    @patch.object(worker, "storage")
    @patch.object(worker.requests, "post")
    def test_front_and_back_use_only_their_own_photos(self, post, storage):
        self.image_response(post)
        front = worker.generate_catalog_thumbnail(self.cfg, self.run, self.photos,
                                                  self.brief, "front")
        front_request = post.call_args.kwargs
        back = worker.generate_catalog_thumbnail(self.cfg, self.run, self.photos,
                                                 self.brief, "back")
        back_request = post.call_args.kwargs
        self.assertEqual(front["source_photo_numbers"], [1, 3])
        self.assertEqual(back["source_photo_numbers"], [2])
        self.assertEqual(len(front_request["files"]), 2)
        self.assertEqual(len(back_request["files"]), 1)
        self.assertIn("Private-selection front label", front_request["data"]["prompt"])
        self.assertNotIn("Barrel information on back", front_request["data"]["prompt"])
        self.assertIn("Barrel information on back", back_request["data"]["prompt"])
        self.assertNotIn("Private-selection front label", back_request["data"]["prompt"])
        self.assertIn("/front.png", front["full_image_path"])
        self.assertIn("/back.png", back["full_image_path"])
        self.assertIn("/front-preview.png", front["preview_path"])
        self.assertIn("/back-preview.png", back["preview_path"])
        self.assertEqual(storage.call_count, 4)
        self.assertEqual([call.args[2] for call in storage.call_args_list],
                         ["warehouse-media", "warehouse-thumbnails"]*2)
        self.assertEqual(self.photos[0].size, (240, 400))
        self.assertEqual(front["cost_json"]["estimated_total_usd"], 0.05704)

    @patch.object(worker, "storage")
    @patch.object(worker.requests, "post")
    def test_no_back_photo_means_no_back_generation(self, post, storage):
        self.brief["back_photo_numbers"] = []
        result = worker.generate_catalog_thumbnail(self.cfg, self.run, self.photos,
                                                   self.brief, "back")
        self.assertEqual(result["status"], "not_available")
        post.assert_not_called()
        storage.assert_not_called()

    @patch.object(worker.requests, "post")
    def test_invalid_reference_does_not_call_api(self, post):
        self.brief["front_photo_numbers"] = [4]
        with self.assertRaises(ValueError):
            worker.generate_catalog_thumbnail(self.cfg, self.run, self.photos,
                                              self.brief, "front")
        post.assert_not_called()

    @patch.object(worker, "storage")
    @patch.object(worker.requests, "post")
    def test_missing_image_fails_without_writing_storage(self, post, storage):
        response = post.return_value
        response.ok = True
        response.json.return_value = {"data": []}
        with self.assertRaises(ValueError):
            worker.generate_catalog_thumbnail(self.cfg, self.run, self.photos,
                                              self.brief, "front")
        storage.assert_not_called()

    @patch.object(worker, "generate_catalog_thumbnail")
    def test_missing_back_is_not_a_failure_and_cost_is_per_view(self, generate):
        def fake(cfg, run, photos, brief, view):
            if view == "front":
                return {"status": "completed", "view": "front",
                        "cost_json": {"estimated_total_usd": 0.05704}}
            return {"status": "not_available", "view": "back",
                    "reason": "No photograph of the back face was provided"}
        generate.side_effect = fake
        result = worker.generate_catalog_views(self.cfg, self.run, self.photos, self.brief)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["back"]["status"], "not_available")
        self.assertEqual(result["cost_json"]["estimated_total_usd"], 0.05704)

    @patch.object(worker, "generate_catalog_thumbnail")
    def test_failed_second_view_preserves_first_and_flags_unknown_cost(self, generate):
        def fake(cfg, run, photos, brief, view):
            if view == "front":
                return {"status": "completed", "view": "front",
                        "cost_json": {"estimated_total_usd": 0.05704}}
            raise RuntimeError("API unavailable")
        generate.side_effect = fake
        result = worker.generate_catalog_views(self.cfg, self.run, self.photos, self.brief)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["front"]["status"], "completed")
        self.assertEqual(result["back"]["status"], "failed")
        self.assertIsNone(result["cost_json"]["estimated_total_usd"])
        self.assertEqual(result["cost_json"]["known_estimated_usd"], 0.05704)

    def test_image_pricing_snapshot(self):
        cost = worker.image_generation_cost({
            "input_tokens_details": {"text_tokens": 600, "image_tokens": 1600},
            "output_tokens_details": {"image_tokens": 1372},
        })
        self.assertEqual(cost["estimated_total_usd"], 0.05704)
        self.assertEqual(cost["rates_usd_per_million_tokens"]["image_output"], 30.0)
        self.assertIsNone(worker.image_generation_cost({})["estimated_total_usd"])


if __name__ == "__main__":
    unittest.main()
