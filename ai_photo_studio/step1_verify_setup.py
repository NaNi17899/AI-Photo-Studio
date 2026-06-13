import sys

print("=" * 50)
print("AI Photo Studio - Setup Verification")
print("=" * 50)

print(f"\n Python version: {sys.version}")

try:
    import torch

    print(f" PyTorch: {torch.__version__}")
    print(f" CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f" GPU: {torch.cuda.get_device_name(0)}")
        mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f" VRAM: {mem:.1f} GB")
    else:
        print(" WARNING: CUDA not detected - check your drivers")
except ImportError:
    print(" PyTorch not installed - will be installed in next step")

print("\n" + "=" * 50)
print("Verification complete")
print("=" * 50)
