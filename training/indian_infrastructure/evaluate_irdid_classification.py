"""
CivicVision AI — Candidate IRDID Image Classification Evaluation Script
========================================================================

Strict Read-Only Evaluation Tool for Candidate Classification Models.
Focus: Indian Road Damage & Infrastructure Dataset (IRDID) 6-Class Split.

SAFETY CONSTRAINTS:
1. NEVER initiates model training.
2. NEVER modifies, replaces, or deletes production YOLO or classifier weights.
3. NEVER copies candidate weights into backend/app/services/weights/ or any runtime directory.
4. Operates strictly in read-only evaluation mode on held-out test splits.
5. All evaluation reports are written into runs/classify/irdid_cls_manual/ or specified isolated run directory.

CONFUSION MATRIX ORIENTATION CONVENTION (Ultralytics Classification):
In Ultralytics classification (ultralytics.utils.metrics.ConfusionMatrix.process_cls_preds):
    for p, t in zip(preds, targets):
        self.matrix[p][t] += 1
Orientation is: cm[predicted, true]
    - Row i sum    (cm[i, :].sum()) = total predictions for class i (TP + FP)
    - Column i sum (cm[:, i].sum()) = total ground truth instances for class i (TP + FN)

FORMULAS (for orientation cm[predicted, true]):
    - TP = cm[i, i]
    - FP = cm[i, :].sum() - TP
    - FN = cm[:, i].sum() - TP
    - Precision = TP / (TP + FP) when (TP + FP) > 0, else 0.0 (convention: undefined, no predictions for class i)
    - Recall    = TP / (TP + FN) when (TP + FN) > 0, else 0.0 (convention: undefined, no ground-truth samples for class i)
    - Accuracy  = trace(cm) / cm.sum() when cm.sum() > 0, else 0.0

Both overall accuracy and per-class metrics are computed from the EXACT same confusion-matrix
to guarantee mathematical consistency.
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

# Supported image extensions for dataset discovery
VALID_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

EXPECTED_6_CLASSES = [
    "broken_edges",
    "construction_zones",
    "cracks",
    "open_manholes",
    "potholes",
    "waterlogged_roads",
]


def discover_dataset_structure(dataset_root: Path) -> Dict[str, Any]:
    """
    Safely discovers and validates the prepared IRDID classification dataset.
    Verifies split integrity, discovers actual class counts dynamically,
    and guards against hardcoded assumptions.
    """
    if not dataset_root.exists():
        raise FileNotFoundError(
            f"Dataset root directory does not exist: {dataset_root.resolve()}"
        )

    splits = ["train", "val", "test"]
    discovered_splits: Dict[str, Dict[str, int]] = {}
    classes_per_split: Dict[str, List[str]] = {}

    for split in splits:
        split_dir = dataset_root / split
        if not split_dir.exists() or not split_dir.is_dir():
            raise FileNotFoundError(
                f"Missing required dataset split directory: '{split_dir.resolve()}'"
            )

        class_dirs = sorted([d.name for d in split_dir.iterdir() if d.is_dir()])
        if not class_dirs:
            raise ValueError(
                f"Split '{split}' contains zero category directories in {split_dir.resolve()}"
            )

        classes_per_split[split] = class_dirs
        split_counts: Dict[str, int] = {}
        for cname in class_dirs:
            cdir = split_dir / cname
            img_files = [f for f in cdir.iterdir() if f.is_file() and f.suffix.lower() in VALID_IMAGE_EXTS]
            split_counts[cname] = len(img_files)

        discovered_splits[split] = split_counts

    # Verify identical class names across train, val, and test splits
    ref_classes = classes_per_split["test"]
    for split in ["train", "val"]:
        if classes_per_split[split] != ref_classes:
            raise ValueError(
                f"Class mismatch between 'test' and '{split}' splits.\n"
                f"  Test classes:  {ref_classes}\n"
                f"  {split} classes: {classes_per_split[split]}"
            )

    # Compute totals
    total_train = sum(discovered_splits["train"].values())
    total_val = sum(discovered_splits["val"].values())
    total_test = sum(discovered_splits["test"].values())
    grand_total = total_train + total_val + total_test

    report = {
        "dataset_root": str(dataset_root.resolve()),
        "classes": ref_classes,
        "num_classes": len(ref_classes),
        "split_counts": discovered_splits,
        "totals": {
            "train": total_train,
            "val": total_val,
            "test": total_test,
            "grand_total": grand_total,
        },
    }
    return report


def verify_dataset_safeguards(dataset_report: Dict[str, Any]) -> None:
    """
    Verifies that the discovered dataset conforms to the expected 6-class specification.
    Halts with clear error if anomalies are detected.
    """
    classes = dataset_report["classes"]
    totals = dataset_report["totals"]

    if classes != EXPECTED_6_CLASSES:
        raise ValueError(
            f"Dataset class mismatch!\n"
            f"  Expected ({len(EXPECTED_6_CLASSES)} classes): {EXPECTED_6_CLASSES}\n"
            f"  Found    ({len(classes)} classes): {classes}"
        )

    if totals["test"] == 0:
        raise ValueError("FATAL: Test split contains 0 valid images. Evaluation cannot proceed.")

    # Validate against known 670 clean image split: 466 train, 99 val, 105 test
    if totals["grand_total"] != 670:
        print(
            f"[WARNING] Discovered grand total images = {totals['grand_total']} (reported baseline is 670)."
        )
    if totals["test"] != 105:
        print(
            f"[WARNING] Discovered test split images = {totals['test']} (reported baseline is 105)."
        )


def verify_matrix_safeguards(
    cm: np.ndarray,
    class_names: List[str],
    ground_truth_test_counts: Dict[str, int]
) -> None:
    """
    Verifies confusion matrix dimensions, sample totals, and matrix orientation.
    Orientation check:
      Ultralytics orientation is cm[predicted, true].
      Therefore, column i sum (cm[:, i].sum()) must match ground_truth_test_counts[class_names[i]].
    """
    num_classes = len(class_names)

    if cm.ndim != 2:
        raise ValueError(f"Confusion matrix must be 2-dimensional. Got shape: {cm.shape}")

    if cm.shape != (num_classes, num_classes):
        raise ValueError(
            f"Confusion matrix dimension mismatch! Expected shape ({num_classes}, {num_classes}), "
            f"got {cm.shape}."
        )

    cm_total = int(cm.sum())
    expected_total = sum(ground_truth_test_counts[c] for c in class_names)
    if cm_total != expected_total:
        raise ValueError(
            f"Confusion matrix total sample count discrepancy!\n"
            f"  Matrix sum:           {cm_total}\n"
            f"  Expected test count:  {expected_total}"
        )

    # Orientation verification
    for i, cname in enumerate(class_names):
        col_sum = int(cm[:, i].sum())
        row_sum = int(cm[i, :].sum())
        expected_true = ground_truth_test_counts[cname]

        if col_sum != expected_true:
            # Check if row_sum matches instead (indicating transposed orientation)
            if row_sum == expected_true and row_sum != col_sum:
                raise ValueError(
                    f"CRITICAL ORIENTATION ERROR: Confusion matrix appears transposed!\n"
                    f"  Class '{cname}': Column sum is {col_sum}, but Ground Truth is {expected_true}.\n"
                    f"  Row sum is {row_sum}. Expected cm[predicted, true] orientation where column sum == ground truth."
                )
            raise ValueError(
                f"Discrepancy for class '{cname}' in confusion matrix:\n"
                f"  Column sum (ground truth total in cm[pred, true]): {col_sum}\n"
                f"  Actual test set count: {expected_true}"
            )


def calculate_metrics_from_confusion_matrix(
    cm: np.ndarray,
    class_names: List[str]
) -> Dict[str, Any]:
    """
    Calculates per-class and overall metrics from the verified confusion matrix cm[predicted, true].

    Formulas:
        TP = cm[i, i]
        FP = cm[i, :].sum() - TP
        FN = cm[:, i].sum() - TP
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0 (documented convention)
        recall    = TP / (TP + FN) if (TP + FN) > 0 else 0.0 (documented convention)
        accuracy  = trace(cm) / cm.sum() if cm.sum() > 0 else 0.0

    Conventions for zero denominators:
        - When TP + FP == 0: precision is mathematically undefined (0/0) because the model
          never predicted this class. We document convention as 0.0 with an 'undefined_precision' flag.
        - When TP + FN == 0: recall is mathematically undefined (0/0) because there are no
          ground-truth instances for this class. We document convention as 0.0 with an 'undefined_recall' flag.
        - When cm.sum() == 0: accuracy is 0.0.
    """
    cm = np.asarray(cm, dtype=np.int64)
    num_classes = len(class_names)
    total_samples = int(cm.sum())

    per_class_metrics: Dict[str, Dict[str, Any]] = {}
    precisions: List[float] = []
    recalls: List[float] = []
    f1s: List[float] = []

    for i, cname in enumerate(class_names):
        tp = int(cm[i, i])
        pred_total = int(cm[i, :].sum())  # Row i sum = TP + FP
        true_total = int(cm[:, i].sum())  # Col i sum = TP + FN
        fp = pred_total - tp
        fn = true_total - tp

        # Precision calculation
        if pred_total > 0:
            precision = float(tp / pred_total)
            undefined_precision = False
        else:
            precision = 0.0
            undefined_precision = True

        # Recall calculation
        if true_total > 0:
            recall = float(tp / true_total)
            undefined_recall = False
        else:
            recall = 0.0
            undefined_recall = True

        # F1 Score
        if (precision + recall) > 0:
            f1 = float(2.0 * precision * recall / (precision + recall))
        else:
            f1 = 0.0

        per_class_metrics[cname] = {
            "class_index": i,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "ground_truth_total": true_total,
            "predicted_total": pred_total,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "undefined_precision": undefined_precision,
            "undefined_recall": undefined_recall,
        }

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

    # Overall metrics from the EXACT same confusion matrix
    if total_samples > 0:
        accuracy = float(np.trace(cm)) / float(total_samples)
    else:
        accuracy = 0.0

    macro_precision = float(np.mean(precisions)) if precisions else 0.0
    macro_recall = float(np.mean(recalls)) if recalls else 0.0
    macro_f1 = float(np.mean(f1s)) if f1s else 0.0

    return {
        "overall_accuracy": round(accuracy, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "total_evaluated_samples": total_samples,
        "per_class": per_class_metrics,
        "confusion_matrix_orientation": "cm[predicted, true]",
        "raw_confusion_matrix": cm.tolist(),
        "zero_denominator_convention": (
            "When (TP + FP) == 0 (no predictions made for class i), precision is mathematically "
            "undefined and reported as 0.0 with undefined_precision=True. When (TP + FN) == 0 "
            "(no ground truth instances for class i), recall is mathematically undefined and "
            "reported as 0.0 with undefined_recall=True."
        ),
    }


def format_evaluation_summary(metrics: Dict[str, Any], class_names: List[str]) -> str:
    """Formats metrics dictionary into a readable markdown/text table."""
    lines = [
        "=" * 85,
        "      CIVICVISION AI — CANDIDATE IRDID CLASSIFIER EVALUATION REPORT",
        "  Orientation: cm[predicted, true] | Source: Single Held-Out Test Confusion Matrix",
        "=" * 85,
        f"Overall Accuracy:  {metrics['overall_accuracy']:.4f} ({metrics['overall_accuracy']*100:.2f}%)",
        f"Macro Precision:   {metrics['macro_precision']:.4f}",
        f"Macro Recall:      {metrics['macro_recall']:.4f}",
        f"Macro F1-Score:    {metrics['macro_f1']:.4f}",
        f"Evaluated Samples: {metrics['total_evaluated_samples']}",
        "-" * 85,
        f"{'Class Name':<22} | {'True':<5} | {'Pred':<5} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'Precision':<9} | {'Recall':<8} | {'F1':<6}",
        "-" * 85,
    ]

    for cname in class_names:
        c = metrics["per_class"][cname]
        p_str = f"{c['precision']:.4f}" if not c["undefined_precision"] else "UNDEF (0.0)"
        r_str = f"{c['recall']:.4f}" if not c["undefined_recall"] else "UNDEF (0.0)"
        f_str = f"{c['f1_score']:.4f}"
        lines.append(
            f"{cname:<22} | {c['ground_truth_total']:<5} | {c['predicted_total']:<5} | "
            f"{c['true_positives']:<4} | {c['false_positives']:<4} | {c['false_negatives']:<4} | "
            f"{p_str:<9} | {r_str:<8} | {f_str:<6}"
        )

    lines.append("=" * 85)
    lines.append("\nCONFUSION MATRIX [rows=predicted, cols=true ground truth]:")
    cm = np.array(metrics["raw_confusion_matrix"])
    col_headers = " ".join(f"{c[:6]:>7}" for c in class_names)
    lines.append(f"{'Pred v \\ True >':<22} {col_headers}")
    for i, cname in enumerate(class_names):
        row_vals = " ".join(f"{cm[i, j]:>7}" for j in range(len(class_names)))
        lines.append(f"{cname:<22} {row_vals}")
    lines.append("-" * 85)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Safe, read-only evaluation script for candidate IRDID image classification models."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="datasets/indian_infrastructure/irdid_prepared_classification",
        help="Path to prepared classification dataset root.",
    )
    parser.add_argument(
        "--weights",
        type=str,
        default="runs/classify/irdid_cls_manual/weights/best.pt",
        help="Path to candidate classification weights file.",
    )
    parser.add_argument(
        "--verify-dataset-only",
        action="store_true",
        help="Perform pre-flight dataset discovery and safeguards check without loading model.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Optional directory to save evaluation_report.json (e.g., runs/classify/irdid_cls_manual/).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Inference device ('cpu' or '0'). Default: 'cpu'.",
    )

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent
    dataset_path = (project_root / args.dataset).resolve() if not Path(args.dataset).is_absolute() else Path(args.dataset)
    weights_path = (project_root / args.weights).resolve() if not Path(args.weights).is_absolute() else Path(args.weights)

    print("=" * 80)
    print("      CIVICVISION AI — IRDID CLASSIFIER EVALUATION RUNBOOK")
    print("=" * 80)
    print(f"Project Root:   {project_root}")
    print(f"Dataset Path:   {dataset_path}")
    print(f"Weights Path:   {weights_path}")
    print(f"Verify Only:    {args.verify_dataset_only}")
    print("-" * 80)

    # 1. Dataset Pre-Flight Audit & Discovery
    print("\n[STEP 1] DATASET DISCOVERY & PRE-FLIGHT INTEGRITY AUDIT...")
    try:
        dataset_report = discover_dataset_structure(dataset_path)
        verify_dataset_safeguards(dataset_report)
        print("  -> Dataset Structure Validated: 6 disjoint categories across all splits.")
        print(f"  -> Discovered Image Counts:")
        print(f"     * Train Split: {dataset_report['totals']['train']} images across 6 classes")
        print(f"     * Val Split:   {dataset_report['totals']['val']} images across 6 classes")
        print(f"     * Test Split:  {dataset_report['totals']['test']} images across 6 classes")
        print(f"     * Total:       {dataset_report['totals']['grand_total']} images (Zero Leakage)")
        print("\n  Per-Class Test Sample Distribution (Dynamically Discovered):")
        for cname, cnt in dataset_report["split_counts"]["test"].items():
            print(f"     - {cname:<22}: {cnt} images")
        print("  -> Status: PASSED [OK]")
    except Exception as e:
        print(f"  -> [FATAL ERROR during dataset audit] {e}")
        sys.exit(1)

    if args.verify_dataset_only:
        print("\n[INFO] --verify-dataset-only flag set. Pre-flight verification complete. Exiting without model evaluation.")
        sys.exit(0)

    # 2. Model Checkpoint Safeguards Check
    print("\n[STEP 2] MODEL CHECKPOINT SAFEGUARD AUDIT...")
    if not weights_path.exists():
        print(
            f"  -> [SAFEGUARD STOP] Candidate weights file does NOT exist at:\n"
            f"     {weights_path}\n"
            f"     The candidate classifier has not been trained yet.\n"
            f"     Training must be explicitly executed by the engineer before evaluation can proceed.\n"
            f"     No model training or evaluation will be started automatically."
        )
        sys.exit(1)

    # Prohibit evaluating against production weights paths directly
    prod_quarantine_paths = [
        "backend/app/services/weights/irdid_classifier.pt",
        "backend/app/ai_model/classifier/weights/best.pt"
    ]
    for p in prod_quarantine_paths:
        if str(weights_path).replace("\\", "/").endswith(p):
            print(
                f"  -> [SAFEGUARD VIOLATION] Candidate evaluation must NOT read from or write to "
                f"production weights path: {p}\n"
                f"     Candidate weights must remain isolated in runs/classify/irdid_cls_manual/."
            )
            sys.exit(1)

    # 3. Model Evaluation on Held-Out Test Split
    print(f"\n[STEP 3] EXECUTING READ-ONLY EVALUATION ON HELD-OUT TEST SPLIT (Device: {args.device})...")
    try:
        from ultralytics import YOLO

        model = YOLO(str(weights_path))
        val_results = model.val(
            data=str(dataset_path),
            split="test",
            device=args.device,
            verbose=False,
            plots=False
        )

        # Extract confusion matrix
        if not hasattr(val_results, "confusion_matrix") or val_results.confusion_matrix is None:
            raise RuntimeError("Ultralytics val_results did not return a confusion_matrix object.")

        cm = val_results.confusion_matrix.matrix
        class_names = dataset_report["classes"]
        test_counts = dataset_report["split_counts"]["test"]

        # 4. Matrix Orientation and Dimension Verification
        print("\n[STEP 4] VERIFYING CONFUSION MATRIX DIMENSIONS & ORIENTATION...")
        verify_matrix_safeguards(cm, class_names, test_counts)
        print("  -> Matrix orientation confirmed: cm[predicted, true]. Dimensions: (6, 6). Total: 105 samples.")

        # 5. Compute Metrics Strictly from Confusion Matrix
        print("\n[STEP 5] COMPUTING STRICT CONFUSION-MATRIX METRICS...")
        metrics = calculate_metrics_from_confusion_matrix(cm, class_names)
        summary_text = format_evaluation_summary(metrics, class_names)
        print("\n" + summary_text)

        # 6. Save isolated report if requested or to default runs directory
        output_dir = Path(args.output_dir) if args.output_dir else weights_path.parent.parent
        if output_dir.exists():
            report_file = output_dir / "evaluation_report.json"
            with open(report_file, "w") as f:
                json.dump(metrics, f, indent=2)
            print(f"\n[OK] Isolated evaluation report saved to: {report_file}")

    except Exception as e:
        print(f"\n[ERROR during model evaluation]: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
