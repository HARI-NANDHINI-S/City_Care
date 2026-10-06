from ultralytics import YOLO

print("SANITY CHECK TRAINING START")
model = YOLO('yolo11n.pt') # Lightweight pretrained model

results = model.train(
    data=r'E:\City_Care\datasets\RDD2020\data.yaml',
    epochs=1,
    imgsz=160, # small for quick sanity check
    batch=8,
    project=r'E:\City_Care\runs\detect',
    name='sanity_check',
    seed=42,
    device='cpu',
    plots=False,
    val=True
)
print("SANITY CHECK TRAINING COMPLETE")
