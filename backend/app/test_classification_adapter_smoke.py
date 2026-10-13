"""
CivicVision AI — Candidate IRDID Classification Adapter Smoke Test
===================================================================

Smoke test validating the contract and return schema of IRDIDClassificationAdapter:
- Verifies behavior when weights are missing (status="unsupported").
- Verifies behavior for valid classifier predictions and mapped supported categories.
- Verifies behavior for unsupported classes (filtered out, raw_detections=[]).
- Confirms classification outputs do not contain fabricated bounding boxes (bounding_box is None).
- Tests exception handling (status="error").
- Runs strictly in an isolated environment without connecting to production databases,
  without modifying production configuration or settings, and without altering the global registry.
"""

import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from PIL import Image

# Ensure backend directory is in sys.path for proper app.* import resolution
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.models.classification_adapter import IRDIDClassificationAdapter


class TestIRDIDClassificationAdapterSmoke(unittest.TestCase):
    """
    Isolated smoke test suite for IRDIDClassificationAdapter conforming to its actual return schema.
    """

    @classmethod
    def setUpClass(cls):
        # Create an ephemeral temporary directory for test fixtures
        cls.temp_dir = tempfile.mkdtemp(prefix="civicvision_adapter_smoke_")
        cls.test_image_path = os.path.join(cls.temp_dir, "smoke_dummy.jpg")
        # Create a lightweight dummy image
        img = Image.new("RGB", (128, 128), color=(120, 150, 180))
        img.save(cls.test_image_path)

    @classmethod
    def tearDownClass(cls):
        # Clean up temporary fixtures
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_01_actual_return_schema_unsupported_when_missing_weights(self):
        """
        Verify the actual return schema when classifier weights are missing.
        Must return status='unsupported' with empty raw_detections and informative error message.
        """
        non_existent_weights = Path(self.temp_dir) / "non_existent_classifier.pt"
        adapter = IRDIDClassificationAdapter(weights_path=non_existent_weights)

        # 1. Adapter readiness properties
        self.assertEqual(adapter.model_id, "irdid-classifier-candidate")
        self.assertEqual(adapter.supported_categories, ["Damaged Road Surface", "Waterlogging"])
        self.assertFalse(adapter.is_available)

        # 2. Invoke infer()
        result = adapter.infer(self.test_image_path)

        # 3. Assert EXACT top-level schema keys returned by the adapter
        expected_keys = {"status", "model_id", "raw_detections", "execution_time_ms", "error_message"}
        self.assertEqual(set(result.keys()), expected_keys, "Return schema does not match actual adapter keys")

        # 4. Assert values conform to unsupported state
        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(result["model_id"], "irdid-classifier-candidate")
        self.assertIsInstance(result["raw_detections"], list)
        self.assertEqual(len(result["raw_detections"]), 0)
        self.assertEqual(result["execution_time_ms"], 0.0)
        self.assertIsInstance(result["error_message"], str)
        self.assertIn("not found", result["error_message"])

        # 5. Guard against fabricated detection fields
        self.assertNotIn("bounding_boxes", result)
        self.assertNotIn("detected_defects", result)
        self.assertNotIn("issue_type", result)

    def test_02_default_constructor_points_to_isolated_weights_path(self):
        """
        Verify default constructor path resolves under backend weights directory
        and safely reports unavailable when the candidate file is not deployed.
        """
        adapter = IRDIDClassificationAdapter()
        self.assertEqual(adapter.model_id, "irdid-classifier-candidate")
        self.assertFalse(adapter.is_available)
        expected_weights_name = "irdid_classifier.pt"
        self.assertEqual(adapter._weights_path.name, expected_weights_name)

    def test_03_valid_prediction_broken_edges_mapped_with_no_fabricated_boxes(self):
        """
        Verify valid classifier prediction for 'broken_edges':
        - Maps raw_class 'broken_edges' to standard category 'Damaged Road Surface'.
        - Confirms bounding_box is None (strict check: NO synthetic/fabricated bounding boxes).
        """
        adapter = IRDIDClassificationAdapter(weights_path=Path(self.test_image_path))

        # Build mock YOLO classification result object
        mock_probs = MagicMock()
        mock_probs.top1 = 0
        mock_probs.top1conf = MagicMock()
        mock_probs.top1conf.item.return_value = 0.92

        mock_result = MagicMock()
        mock_result.probs = mock_probs
        mock_result.names = {
            0: "broken_edges",
            1: "waterlogged_roads",
            2: "potholes",
            3: "cracks"
        }

        mock_yolo_model = MagicMock(return_value=[mock_result])

        # Attach mock model to adapter instance in isolation
        adapter._model = mock_yolo_model
        adapter._is_loaded = True

        result = adapter.infer(self.test_image_path)

        # Verify schema
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model_id"], "irdid-classifier-candidate")
        self.assertIsNone(result["error_message"])
        self.assertGreaterEqual(result["execution_time_ms"], 0.0)

        # Verify raw_detections content
        self.assertEqual(len(result["raw_detections"]), 1)
        detection = result["raw_detections"][0]

        expected_det_keys = {"class", "raw_class", "confidence", "bounding_box"}
        self.assertEqual(set(detection.keys()), expected_det_keys)

        self.assertEqual(detection["class"], "Damaged Road Surface")
        self.assertEqual(detection["raw_class"], "broken_edges")
        self.assertAlmostEqual(detection["confidence"], 0.92, places=2)

        # STRICT ASSERTION: Classification must NEVER contain fabricated bounding boxes
        self.assertIsNone(
            detection["bounding_box"],
            "FATAL: Classification output contains fabricated bounding box! Must be None."
        )

    def test_04_valid_prediction_waterlogged_roads_mapped_with_no_fabricated_boxes(self):
        """
        Verify valid classifier prediction for 'waterlogged_roads':
        - Maps raw_class 'waterlogged_roads' to standard category 'Waterlogging'.
        - Confirms bounding_box is None.
        """
        adapter = IRDIDClassificationAdapter(weights_path=Path(self.test_image_path))

        mock_probs = MagicMock()
        mock_probs.top1 = 1
        mock_probs.top1conf = MagicMock()
        mock_probs.top1conf.item.return_value = 0.88

        mock_result = MagicMock()
        mock_result.probs = mock_probs
        mock_result.names = {
            0: "broken_edges",
            1: "waterlogged_roads"
        }

        adapter._model = MagicMock(return_value=[mock_result])
        adapter._is_loaded = True

        result = adapter.infer(self.test_image_path)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["raw_detections"]), 1)

        det = result["raw_detections"][0]
        self.assertEqual(det["class"], "Waterlogging")
        self.assertEqual(det["raw_class"], "waterlogged_roads")
        self.assertAlmostEqual(det["confidence"], 0.88, places=2)
        self.assertIsNone(det["bounding_box"])

    def test_05_unsupported_classes_safely_filtered_out(self):
        """
        Verify that predictions outside supported_categories ('potholes', 'cracks',
        'open_manholes', 'construction_zones') do NOT generate detections.
        The adapter must return status='success' with raw_detections=[] because
        the candidate classifier is only authorized for Damaged Road Surface and Waterlogging.
        """
        adapter = IRDIDClassificationAdapter(weights_path=Path(self.test_image_path))

        unsupported_classes = ["potholes", "cracks", "open_manholes", "construction_zones", "other_class"]

        for idx, unsupp in enumerate(unsupported_classes):
            mock_probs = MagicMock()
            mock_probs.top1 = idx
            mock_probs.top1conf = MagicMock()
            mock_probs.top1conf.item.return_value = 0.95

            mock_result = MagicMock()
            mock_result.probs = mock_probs
            mock_result.names = {idx: unsupp}

            adapter._model = MagicMock(return_value=[mock_result])
            adapter._is_loaded = True

            result = adapter.infer(self.test_image_path)
            self.assertEqual(result["status"], "success")
            self.assertEqual(
                result["raw_detections"],
                [],
                f"Unsupported class '{unsupp}' must not produce raw_detections in IRDID adapter!"
            )
            self.assertIsNone(result["error_message"])

    def test_06_inference_exception_handled_safely(self):
        """
        Verify that unexpected inference exceptions are trapped and returned
        with status='error' and error_message populated, without crashing the process.
        """
        adapter = IRDIDClassificationAdapter(weights_path=Path(self.test_image_path))

        mock_faulty_model = MagicMock(side_effect=RuntimeError("Simulated inference engine fault"))
        adapter._model = mock_faulty_model
        adapter._is_loaded = True

        result = adapter.infer(self.test_image_path)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["model_id"], "irdid-classifier-candidate")
        self.assertEqual(result["raw_detections"], [])
        self.assertIn("Simulated inference engine fault", result["error_message"])
        self.assertGreaterEqual(result["execution_time_ms"], 0.0)


if __name__ == "__main__":
    unittest.main()
