import torch

if torch.cuda.is_available():
    print("CUDA is available.")
    current_device = torch.cuda.current_device()
    for i in range(torch.cuda.device_count()):
        print(f" {'>' if current_device == i else ' '} {i}: {torch.cuda.get_device_name(i)}")
else:
    print("CUDA is not available.")
