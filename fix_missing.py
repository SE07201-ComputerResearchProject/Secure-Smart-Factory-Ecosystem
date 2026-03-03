import os

# Đường dẫn file thư viện trong venv của bạn
target_file = '/home/thotien426/SmartFactory_Dev/venv/lib/python3.12/site-packages/face_recognition/__init__.py'

# Nội dung đầy đủ (Đã bổ sung face_distance)
new_content = """# --- FIX FULL BY TIEN THO ---
import sys
import os

# 1. Ép tìm model ở thư mục hiện tại
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.append(cwd)

# 2. Import model
try:
    import face_recognition_models
except ImportError:
    pass 

# 3. Import đầy đủ các hàm API (Đã thêm face_distance)
from .api import load_image_file, face_locations, batch_face_locations, face_landmarks, face_encodings, compare_faces, face_distance

__version__ = '1.2.3'
"""

try:
    with open(target_file, 'w') as f:
        f.write(new_content)
    print("✅ Đã cập nhật thư viện thành công! Đã có hàm face_distance.")
except Exception as e:
    print(f"❌ Lỗi: {e}")

