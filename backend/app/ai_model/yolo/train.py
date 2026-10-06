import torch
if not torch.cuda.is_available():
    print('CUDA unavailable. Validate pipeline, config, report GPU unavailable.')
