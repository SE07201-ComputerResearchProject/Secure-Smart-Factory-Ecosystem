import cv2
import face_recognition
import os
import sys
import numpy as np

# --- 0. FIX LỖI ĐƯỜNG DẪN TỰ ĐỘNG ---
# Giúp code tự tìm thấy model mà không cần gõ lệnh PYTHONPATH
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.append(cwd)

# --- 1. CẤU HÌNH HỆ THỐNG ---
DATA_DIR = "known_faces"
print("[INFO] Đang khởi động hệ thống an ninh Smart Factory...")

# Kiểm tra thư mục dữ liệu
if not os.path.exists(DATA_DIR):
    print(f"[ERROR] Không thấy thư mục '{DATA_DIR}'. Bạn đã chạy 'add_face.py' chưa?")
    exit()

# --- 2. HỌC DỮ LIỆU (TRAINING) ---
print("[INFO] Đang nạp dữ liệu khuôn mặt...")
known_face_encodings = []
known_face_names = []

files = os.listdir(DATA_DIR)
if len(files) == 0:
    print("[ERROR] Thư mục rỗng! Hãy chạy 'add_face.py' để đăng ký khuôn mặt trước.")
    exit()

for filename in files:
    if filename.endswith(".jpg") or filename.endswith(".png"):
        filepath = os.path.join(DATA_DIR, filename)
        name = os.path.splitext(filename)[0] # Lấy tên file làm tên người
        
        try:
            # Load ảnh
            image = face_recognition.load_image_file(filepath)
            
            # Tìm khuôn mặt trong ảnh mẫu
            encodings = face_recognition.face_encodings(image)
            
            if len(encodings) > 0:
                known_face_encodings.append(encodings[0])
                known_face_names.append(name)
                print(f"  + Đã học: {name}")
            else:
                print(f"  ⚠️ Cảnh báo: Ảnh {filename} không rõ mặt. Bỏ qua.")
        except Exception as e:
            print(f"  ❌ Lỗi khi đọc file {filename}: {e}")

print(f"[OK] Đã học xong {len(known_face_names)} người. Bắt đầu giám sát!")

# --- 3. KHỞI ĐỘNG CAMERA ---
# Số 0 hoặc 1 tùy vào việc bạn cắm mấy cam. Thường cam rời sau khi ngắt cam laptop sẽ là 0.
cam = cv2.VideoCapture(0)

# Cấu hình chống xanh màn hình trên VMware
cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cam.isOpened():
    print("[ERROR] Không mở được Camera. Thử đổi cv2.VideoCapture(0) thành 1 xem sao.")
    exit()

process_this_frame = True

print("[INFO] Hệ thống đang chạy! Nhấn 'q' để thoát.")

while True:
    ret, frame = cam.read()
    if not ret:
        print("Lỗi đọc Camera!")
        break

    # Giảm kích thước ảnh xuống 1/4 để xử lý nhanh hơn
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # --- ĐÂY LÀ CHỖ ĐÃ FIX LỖI MEMORY LAYOUT ---
    # Chuyển BGR sang RGB bằng OpenCV để đảm bảo dữ liệu liền mạch trong RAM
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Chỉ xử lý khung hình cách nhật (tiết kiệm CPU)
    if process_this_frame:
        # Tìm vị trí khuôn mặt
        face_locations = face_recognition.face_locations(rgb_small_frame)
        
        # Mã hóa khuôn mặt (Giờ sẽ không còn lỗi TypeError nữa)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # So sánh
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
            name = "XAM NHAP" # Mặc định là kẻ lạ
            color = (0, 0, 255) # Đỏ

            # Tìm người giống nhất
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    color = (0, 255, 0) # Xanh lá

            face_names.append((name, color))

    process_this_frame = not process_this_frame

    # Hiển thị kết quả
    for (top, right, bottom, left), (name, color) in zip(face_locations, face_names):
        # Nhân 4 toạ độ lên vì nãy thu nhỏ
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Vẽ khung
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        
        # Vẽ tên
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

    cv2.imshow('Smart Factory Security Gate', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
