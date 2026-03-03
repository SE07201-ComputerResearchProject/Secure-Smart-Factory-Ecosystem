import os

# Đường dẫn đến file bị lỗi trong venv
target_file = 'venv/lib/python3.12/site-packages/face_recognition/__init__.py'

# Nội dung mới: Đơn giản, gọn nhẹ, bỏ qua kiểm tra lỗi
new_content = """
# --- FIX AUTO BY TIEN THO ---
import sys
import os
sys.path.append(os.getcwd()) # Trỏ đường dẫn vào thư mục hiện tại
# ---------------------------

# Import API chính
from .api import load_image_file, face_locations, batch_face_locations, face_landmarks, face_encodings, compare_faces

__version__ = '1.2.3'
"""

try:
    with open(target_file, 'w') as f:
        f.write(new_content)
    print("✅ Đã sửa file thư viện thành công! Giờ chạy test_cam.py là ngon.")
except FileNotFoundError:
    print("❌ Không tìm thấy file thư viện. Bạn có đang ở đúng thư mục SmartFactory_Dev không?")
