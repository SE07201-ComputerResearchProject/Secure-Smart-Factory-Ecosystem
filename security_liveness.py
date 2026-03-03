import cv2
import face_recognition
import os
import sys
import numpy as np
import time

# --- CẤU HÌNH HỆ THỐNG ---
# Ngưỡng để xác định mắt nhắm (thường là 0.2 đến 0.3)
EYE_AR_THRESH = 0.25
# Số frame liên tiếp mắt phải nhắm thì mới tính là 1 lần chớp
EYE_AR_CONSEC_FRAMES = 2

# Biến đếm
COUNTER = 0
TOTAL_BLINKS = 0
IS_REAL_PERSON = False
UNLOCK_TIMER = 0

# --- HÀM TÍNH TỶ LỆ MỞ MẮT (EAR) ---
def eye_aspect_ratio(eye):
    # Tính khoảng cách giữa các điểm chiều dọc mắt (p2-p6, p3-p5)
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    # Tính khoảng cách chiều ngang (p1-p4)
    C = np.linalg.norm(eye[0] - eye[3])
    # Công thức EAR
    ear = (A + B) / (2.0 * C)
    return ear

# --- FIX LỖI ĐƯỜNG DẪN TỰ ĐỘNG ---
cwd = os.getcwd()
if cwd not in sys.path: sys.path.append(cwd)

try:
    # Import thêm thư viện model landmarks
    import face_recognition_models
except ImportError:
    pass

# --- NẠP DỮ LIỆU ---
DATA_DIR = "known_faces"
print("[INFO] Đang nạp dữ liệu khuôn mặt...")
known_face_encodings = []
known_face_names = []

if not os.path.exists(DATA_DIR):
    print("CHƯA CÓ DỮ LIỆU! Chạy add_face.py trước.")
    exit()

for filename in os.listdir(DATA_DIR):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        filepath = os.path.join(DATA_DIR, filename)
        image = face_recognition.load_image_file(filepath)
        encodings = face_recognition.face_encodings(image)
        if len(encodings) > 0:
            known_face_encodings.append(encodings[0])
            known_face_names.append(os.path.splitext(filename)[0])
            print(f"  + Đã học: {filename}")

print("[OK] Sẵn sàng! Hãy CHỚP MẮT để mở cửa.")

# --- KHỞI ĐỘNG CAMERA ---
cam = cv2.VideoCapture(0) # Đổi thành 1 nếu cần
cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    ret, frame = cam.read()
    if not ret: break

    # Resize để xử lý nhanh
    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # 1. Phát hiện vị trí khuôn mặt
    face_locations = face_recognition.face_locations(rgb_small_frame)
    
    # 2. Phát hiện các điểm đặc trưng (Mắt, mũi, miệng...)
    face_landmarks_list = face_recognition.face_landmarks(rgb_small_frame, face_locations)

    face_names = []
    
    # Nếu không có mặt -> Reset bộ đếm liveness
    if len(face_locations) == 0:
        COUNTER = 0
        IS_REAL_PERSON = False

    for (top, right, bottom, left), landmarks in zip(face_locations, face_landmarks_list):
        # --- NHẬN DIỆN NGƯỜI DÙNG ---
        face_encoding = face_recognition.face_encodings(rgb_small_frame, [(top, right, bottom, left)])[0]
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
        name = "KHACH"
        color = (0, 0, 255) # Đỏ mặc định

        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

        # --- KIỂM TRA LIVENESS (CHỚP MẮT) ---
        # Lấy toạ độ mắt trái và phải
        leftEye = np.array(landmarks['left_eye'])
        rightEye = np.array(landmarks['right_eye'])

        # Tính EAR trung bình
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        avgEAR = (leftEAR + rightEAR) / 2.0

        # Logic phát hiện chớp mắt
        if avgEAR < EYE_AR_THRESH:
            COUNTER += 1
        else:
            if COUNTER >= EYE_AR_CONSEC_FRAMES:
                TOTAL_BLINKS += 1
                UNLOCK_TIMER = time.time() # Ghi lại thời điểm chớp mắt
                IS_REAL_PERSON = True
            COUNTER = 0

        # --- LOGIC MỞ CỬA ---
        # Nếu đã chớp mắt trong vòng 3 giây gần đây VÀ nhận đúng người
        if IS_REAL_PERSON and (time.time() - UNLOCK_TIMER < 3) and name != "KHACH":
            status = "MO CUA (REAL)"
            color = (0, 255, 0) # Xanh lá
        elif name != "KHACH":
            status = "HAY CHOP MAT!"
            color = (0, 255, 255) # Vàng (Chờ xác nhận)
        else:
            status = "XAM NHAP"
            IS_REAL_PERSON = False # Người lạ chớp mắt cũng vô dụng

        # --- VẼ LÊN MÀN HÌNH ---
        # Scale toạ độ về lại kích thước gốc (vì nãy resize 0.5)
        top *= 2; right *= 2; bottom *= 2; left *= 2
        
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, f"{name} - {status}", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Hiển thị số lần chớp mắt góc màn hình
        cv2.putText(frame, f"Blinks: {TOTAL_BLINKS} | EAR: {avgEAR:.2f}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow('Smart Factory Liveness Check', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
