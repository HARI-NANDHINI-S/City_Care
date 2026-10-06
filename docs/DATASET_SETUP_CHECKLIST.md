# Dataset Setup Manual Checklist

Follow these steps manually to acquire and prepare the real datasets for CivicVision. Automated scripts are provided to handle the rest.

### YOLO Dataset (RDD2020 India)
- [ ] **Download RDD2020 (India subset):** 
  - Go to [Mendeley](https://data.mendeley.com/datasets/5ty2wb6gvg/1) or [GitHub](https://github.com/sekilab/RoadDamageDetector).
  - Download the dataset archive.
- [ ] **Extract to Project:**
  - Extract the downloaded archive into `e:\City_Care\datasets\RDD2020\`.
  - Ensure you have the images folder (e.g., `India/images/`) and annotation folder (`India/annotations/`).
- [ ] **Run Format Conversion:**
  - The dataset provides PASCAL VOC XML files. Convert it:
    `python backend/app/ml/convert_rdd_to_yolo.py --xml_dir datasets/RDD2020/India/annotations --img_dir datasets/RDD2020/India/images --out_dir datasets/RDD2020`
- [ ] **Validate Dataset:**
  - Run `python backend/app/ml/validate_yolo_dataset.py --data datasets/RDD2020/data.yaml`

### Priority Dataset
- [ ] **Download Municipal CSV:**
  - Locate a municipal road service request dataset (e.g., from San Diego Open Data or Open Data NI).
  - Download the CSV file.
- [ ] **Place CSV in Project:**
  - Save the file as `e:\City_Care\datasets\priority\actual_dataset.csv`.
- [ ] **Clean and Map Columns:**
  - Ensure the columns match the schema defined in `datasets/priority/priority_dataset_template.csv`.
- [ ] **Validate Priority Data:**
  - Run `python backend/app/ml/validate_priority_dataset.py --data datasets/priority/actual_dataset.csv`

### Final Readiness
- [ ] **Check Overall Readiness:**
  - Run `python backend/app/ml/check_training_readiness.py`
  - Ensure the status says "READY".
