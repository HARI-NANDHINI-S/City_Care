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
        adapter = IRDIDClassificationAdapter(weights_path=Path(self.test_image_path), enabled=True)

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
        adapter = IRDIDClassificationAdapter(weights_path=Path(self.test_image_path), enabled=True)

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
        adapter = IRDIDClassificationAdapter(weights_path=Path(self.test_image_path), enabled=True)

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
        adapter = IRDIDClassificationAdapter(weights_path=Path(self.test_image_path), enabled=True)

        mock_faulty_model = MagicMock(side_effect=RuntimeError("Simulated inference engine fault"))
        adapter._model = mock_faulty_model
        adapter._is_loaded = True

        result = adapter.infer(self.test_image_path)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["model_id"], "irdid-classifier-candidate")
        self.assertEqual(result["raw_detections"], [])
        self.assertIn("Simulated inference engine fault", result["error_message"])
        self.assertGreaterEqual(result["execution_time_ms"], 0.0)

    # -------------------------------------------------------------
    # PHASE 1: FEATURE FLAG & AVAILABILITY GATING REGRESSION TESTS
    # -------------------------------------------------------------

    def test_07_feature_flag_defaults_to_disabled(self):
        """
        Requirement 1: Verify the feature flag defaults to False in settings.
        Adapter default instantiation must report is_enabled=False and is_available=False.
        """
        from app.core.config import settings
        self.assertFalse(settings.ENABLE_IRDID_CLASSIFIER, "Default ENABLE_IRDID_CLASSIFIER must be False")

        adapter = IRDIDClassificationAdapter()
        self.assertFalse(adapter.is_enabled, "Adapter must be disabled by default")
        self.assertFalse(adapter.is_available, "Adapter must be unavailable by default")

    def test_08_feature_flag_explicit_false_adapter_unavailable(self):
        """
        Requirement 2: When feature flag is explicitly False, adapter must report unavailable.
        """
        adapter = IRDIDClassificationAdapter(enabled=False)
        self.assertFalse(adapter.is_enabled)
        self.assertFalse(adapter.is_available)

        res = adapter.infer(self.test_image_path)
        self.assertEqual(res["status"], "unsupported")
        self.assertEqual(res["raw_detections"], [])
        self.assertIn("disabled by configuration", res["error_message"])

    def test_09_feature_flag_false_with_dummy_checkpoint_remains_unavailable(self):
        """
        Requirement 3: The classifier must NOT become available merely because
        a checkpoint file exists on disk. With flag=False and real file present,
        availability must remain False.
        """
        dummy_weights = Path(self.temp_dir) / "dummy_weights_file.pt"
        dummy_weights.write_bytes(b"dummy binary checkpoint data")
        self.assertTrue(dummy_weights.exists())

        # Gated test: weights exist, but enabled=False (or default)
        adapter = IRDIDClassificationAdapter(weights_path=dummy_weights, enabled=False)
        self.assertFalse(
            adapter.is_available,
            "CRITICAL HAZARD: Adapter became available merely because weights file exists!"
        )

        res = adapter.infer(self.test_image_path)
        self.assertEqual(res["status"], "unsupported")
        self.assertEqual(res["raw_detections"], [])

    def test_10_feature_flag_true_with_no_checkpoint_remains_unavailable(self):
        """
        Requirement 4a: When feature flag is True, but weights file is missing,
        adapter must safely report unavailable.
        """
        non_existent = Path(self.temp_dir) / "non_existent_model_weights.pt"
        self.assertFalse(non_existent.exists())

        adapter = IRDIDClassificationAdapter(weights_path=non_existent, enabled=True)
        self.assertTrue(adapter.is_enabled)
        self.assertFalse(adapter.is_available, "Must remain unavailable when weights are absent")

        res = adapter.infer(self.test_image_path)
        self.assertEqual(res["status"], "unsupported")
        self.assertIn("not found", res["error_message"])

    def test_11_feature_flag_true_with_valid_test_checkpoint_contract(self):
        """
        Requirement 4b & 5: When feature flag is True AND test checkpoint exists,
        adapter availability follows the model loading contract without production weights.
        """
        dummy_weights = Path(self.temp_dir) / "test_contract_weights.pt"
        dummy_weights.write_bytes(b"mock weights")

        adapter = IRDIDClassificationAdapter(weights_path=dummy_weights, enabled=True)
        self.assertTrue(adapter.is_enabled)

        # Mock successful model load in isolation
        adapter._model = MagicMock()
        adapter._is_loaded = True
        self.assertTrue(adapter.is_available)

    def test_12_malformed_config_values_fail_safely(self):
        """
        Requirement 6: Malformed, non-boolean, or invalid configuration values
        must fail safely to False without crashing settings instantiation.
        """
        from app.core.config import Settings

        # Valid truthy inputs
        s_true = Settings(ENABLE_IRDID_CLASSIFIER="true")
        self.assertTrue(s_true.ENABLE_IRDID_CLASSIFIER)
        s_yes = Settings(ENABLE_IRDID_CLASSIFIER="yes")
        self.assertTrue(s_yes.ENABLE_IRDID_CLASSIFIER)
        s_1 = Settings(ENABLE_IRDID_CLASSIFIER="1")
        self.assertTrue(s_1.ENABLE_IRDID_CLASSIFIER)

        # Valid falsy inputs
        s_false = Settings(ENABLE_IRDID_CLASSIFIER="false")
        self.assertFalse(s_false.ENABLE_IRDID_CLASSIFIER)
        s_no = Settings(ENABLE_IRDID_CLASSIFIER="no")
        self.assertFalse(s_no.ENABLE_IRDID_CLASSIFIER)
        s_0 = Settings(ENABLE_IRDID_CLASSIFIER="0")
        self.assertFalse(s_0.ENABLE_IRDID_CLASSIFIER)

        # Malformed / invalid inputs -> must fail-safe to False
        s_malformed1 = Settings(ENABLE_IRDID_CLASSIFIER="random_invalid_string")
        self.assertFalse(s_malformed1.ENABLE_IRDID_CLASSIFIER)

        s_malformed2 = Settings(ENABLE_IRDID_CLASSIFIER="enabled_maybe")
        self.assertFalse(s_malformed2.ENABLE_IRDID_CLASSIFIER)

    def test_13_classifier_disabled_preserves_registry_and_yolo_behavior(self):
        """
        Requirement 7 & 8: Verify model registry and existing YOLO behavior
        when IRDID classifier is disabled by default:
        - IRDID adapter is registered but unavailable.
        - Active adapters list contains YOLO and excludes IRDID classifier.
        """
        from app.services.models.registry import model_registry

        # Check adapter in registry
        candidate_adapter = model_registry.get_adapter("irdid-classifier-candidate")
        self.assertIsNotNone(candidate_adapter)
        self.assertFalse(candidate_adapter.is_available)

        # Active adapters list must NOT contain the candidate classifier
        active_ids = [a.model_id for a in model_registry.get_all_active_adapters()]
        self.assertNotIn("irdid-classifier-candidate", active_ids)

        # Active YOLO adapter must remain intact
        yolo_adapter = model_registry.get_adapter("yolov8-rdd2020-india-v1")
        self.assertIsNotNone(yolo_adapter)
        self.assertTrue(yolo_adapter.is_available)
        self.assertIn("yolov8-rdd2020-india-v1", active_ids)


if __name__ == "__main__":
    unittest.main()
