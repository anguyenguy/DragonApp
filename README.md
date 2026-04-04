## DragonApp

## 1. Chuẩn bị môi trường Python
# Tạo virtual env
python3 -m venv clip_env
# Kích hoạt env
# macOS / Linux
source clip_env/bin/activate
# Windows
clip_env\Scripts\activate

## 2. Cài các thư viện cần thiết
# PyTorch (phiên bản CPU hoặc GPU tùy máy bạn)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
# CLIP
pip install git+https://github.com/openai/CLIP.git
# GUI + xử lý ảnh
pip install pillow numpy opencv-python