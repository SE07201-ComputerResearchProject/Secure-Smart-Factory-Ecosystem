import cv2
import face_recognition
import os
import sys
import numpy as np
import time
import random

# --- 1. FIX ĐƯỜNG DẪN TỰ ĐỘNG ---
# Giúp tìm thấy thư viện mà không cần gõ PYTHONPATH
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.append(cwd)

# --- 2. CẤU HÌNH TRÒ CHƠI ---
CHALLENGE_TIME = 5.0 # Thời gian thực hiện (giây)
ACTIONS = ["QUAY TRAI", "QUAY PHAI", "CUOI TUOI"]
DATA_DIR = "known_faces"

# --- 3. CÁC HÀM XỬ LÝ HÌNH HỌC (AI) ---
def get_face_direction(landmarks):
    # Lấy các điểm mốc trên mặt
    nose_tip = np.array(landmarks['nose_tip'][2])
    # Dlib trả về danh sách điểm cằm, điểm 0 là trái (trong ảnh), điểm 16 là phải
    left_jaw = np.array(landmarks['chin'][0])
    right_jaw = np.array(landmarks['chin'][16])

    # Tính khoảng cách từ mũi đến 2 bên má
    dist_left = np.linalg.norm(nose_tip - left_jaw)
    dist_right = np.linalg.norm(nose_tip - right_jaw)
    
    # Tính tỷ lệ chênh lệch
    ratio = dist_left / (dist_right + 1e-6)
    
    # Logic xác định hướng quay
    if ratio < 0.5: return "RIGHT" # Quay phải (theo hướng người dùng)
    if ratio > 1.5: return "LEFT"  # Quay trái
    return "CENTER"

def is_smiling(landmarks):
    # Tính độ mở rộng của miệng
    left_corner = np.array(landmarks['top_lip'][0])
    right_corner = np.array(landmarks['top_lip'][6])
    top_lip = np.array(landmarks['top_lip'][3])
    bottom_lip = np.array(landmarks['bottom_lip'][3])

    width = np.linalg.norm(left_corner - right_corner)
    height = np.linalg.norm(top_lip - bottom_lip)
    
    # Nếu chiều ngang lớn gấp 2.5 lần chiều dọc -> Đang cười
    if width > 2.5 * height: return True
    return False

# --- 4. NẠP DỮ LIỆU ---
print("[INFO] Đang nạp dữ liệu khuôn mặt...")
known_encodings = []
known_names = []

if not os.path.exists(DATA_DIR):
    print(f"[LỖI] Không tìm thấy thư mục {DATA_DIR}. Hãy chạy add_face.py trước!")
    sys.exit()

for f in os.listdir(DATA_DIR):
    if f.endswith(('.jpg', '.png')):
        path = os.path.join(DATA_DIR, f)
        try:
            img = face_recognition.load_image_file(path)
            encs = face_recognition.face_encodings(img)
            if encs:
                known_encodings.append(encs[0])
                known_names.append(os.path.splitext(f)[0])
                print(f"  + Đã học: {f}")
        except Exception as e:
            print(f"  - Lỗi file {f}: {e}")

if not known_encodings:
    print("[CẢNH BÁO] Chưa có dữ liệu khuôn mặt nào!")

# --- 5. KHỞI ĐỘNG CAMERA (CÓ FIX LỖI) ---
print("[INFO] Đang mở Camera... (Chờ 2s khởi động)")
# THỬ CAMERA SỐ 0 (Thông thường Webcam rời sẽ là 0 nếu đã ngắt cam laptop)
cam = cv2.VideoCapture(0)

# Cấu hình giảm tải cho VMware (Chống màn hình xanh)
cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Chờ 2 giây cho Camera ổn định (Fix lỗi thoát đột ngột)
time.sleep(2.0)

if not cam.isOpened():
    print("[LỖI] Không thể mở Camera!")
    print("👉 GỢI Ý: Thử đổi cv2.VideoCapture(0) thành số 1 trong code.")
    sys.exit()

# --- 6. VÒNG LẶP CHÍNH ---
game_state = "IDLE"
current_challenge = None
challenge_start = 0
unlock_timer = 0


print("[SẴN SÀNG] Hệ thống Anti-Hack Video đã chạy. Nhấn 'q' để thoát.")


# --- THÊM ĐOẠN NÀY ĐỂ MÀN HÌNH TO HƠN ---
cv2.namedWindow("Security Challenge", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Security Challenge", 1280, 960) # Phóng to gấp đôi (HD)
# ----------------------------------------
while True:
    ret, frame = cam.read()
    
    # Báo lỗi chi tiết nếu mất kết nối
    if not ret:
        print("\n[LỖI NGHIÊM TRỌNG] Mất tín hiệu Camera!")
        print("  1. Vào menu VM > Removable Devices > Kiểm tra Webcam đã Connect chưa.")
        print("  2. Rút dây Webcam ra cắm lại.")
        break

    # Xử lý ảnh (Resize và chuyển màu)
    small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    locs = face_recognition.face_locations(rgb)
    
    # Nếu không thấy ai -> Reset trạng thái
    if not locs:
        game_state = "IDLE"
    else:
        # Có người -> Phân tích
        lmarks_list = face_recognition.face_landmarks(rgb, locs)
        encs = face_recognition.face_encodings(rgb, locs)

        for (top, right, bottom, left), lmarks, enc in zip(locs, lmarks_list, encs):
            # A. Nhận diện danh tính
            matches = face_recognition.compare_faces(known_encodings, enc, 0.5)
            name = "KHACH"
            color = (0, 0, 255) # Đỏ

            dists = face_recognition.face_distance(known_encodings, enc)
            if len(dists) > 0:
                best_idx = np.argmin(dists)
                if matches[best_idx]:
                    name = known_names[best_idx]

            # B. Logic Trò Chơi Bảo Mật
            status = "Dang cho..."
            
            if name == "KHACH":
                status = "KHONG XAC DINH"
            else:
                # Trạng thái 1: Bắt đầu thử thách
                if game_state == "IDLE":
                    game_state = "CHALLENGE"
                    current_challenge = random.choice(ACTIONS)
                    challenge_start = time.time()
                
                # Trạng thái 2: Đang kiểm tra
                elif game_state == "CHALLENGE":
                    time_left = CHALLENGE_TIME - (time.time() - challenge_start)
                    color = (0, 255, 255) # Vàng
                    status = f"Yeu cau: {current_challenge} ({int(time_left)}s)"

                    # Kiểm tra hành động hiện tại của người dùng
                    direction = get_face_direction(lmarks)
                    smile = is_smiling(lmarks)
                    
                    act = "NONE"
                    if direction == "LEFT": act = "QUAY TRAI"
                    elif direction == "RIGHT": act = "QUAY PHAI"
                    elif smile: act = "CUOI TUOI"

                    # So khớp
                    if act == current_challenge:
                        game_state = "PASSED"
                        unlock_timer = time.time()
                    
                    # Hết giờ
                    if time_left <= 0:
                        game_state = "FAILED"
                        challenge_start = time.time()

                # Trạng thái 3: Thành công
                elif game_state == "PASSED":
                    color = (0, 255, 0) # Xanh lá
                    status = "MO CUA THANH CONG"
                    if time.time() - unlock_timer > 3.0:
                        game_state = "IDLE"

                # Trạng thái 4: Thất bại
                elif game_state == "FAILED":
                    color = (0, 0, 255)
                    status = "THAT BAI - THU LAI SAU 2s"
                    if time.time() - challenge_start > 2.0:
                        game_state = "IDLE"

            # Vẽ khung và chữ
            top*=2; right*=2; bottom*=2; left*=2
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Vẽ nền đen phía trên để hiển thị trạng thái rõ hơn
            cv2.rectangle(frame, (0,0), (640, 50), (0,0,0), -1)
            cv2.putText(frame, f"{name}: {status}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow("Security Challenge", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
