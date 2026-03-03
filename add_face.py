import cv2
import os
import time

# --- CẤU HÌNH ---
# Tên thư mục chứa ảnh
DATA_DIR = "known_faces"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 1. Khởi động Camera (Nhớ số 1 cho Webcam rời trên VMware)
cam = cv2.VideoCapture(0)

# Fix lỗi màn hình xanh & tối ưu tốc độ
cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Nhập tên người cần đăng ký
name = input("Nhập tên người dùng (VD: TienTho): ")
print(f"[INFO] Đang mở Camera... Hãy nhìn thẳng vào ống kính và cười tươi lên!")
print("[HƯỚNG DẪN] Nhấn phím 's' để LƯU ảnh. Nhấn 'q' để THOÁT.")

while True:
    ret, frame = cam.read()
    if not ret:
        print("Lỗi Camera!")
        break

    # Vẽ khung hướng dẫn ảo để căn mặt
    height, width, _ = frame.shape
    center_x, center_y = width // 2, height // 2
    # Vẽ hình chữ nhật màu xanh dương ở giữa màn hình
    cv2.rectangle(frame, (center_x - 100, center_y - 120), (center_x + 100, center_y + 120), (255, 0, 0), 2)
    
    cv2.putText(frame, "Nhan 's' de LUU", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.imshow("Dang ky khuon mat", frame)

    key = cv2.waitKey(1) & 0xFF

    # Nếu nhấn 's' -> Lưu ảnh
    if key == ord('s'):
        img_name = f"{DATA_DIR}/{name}.jpg"
        cv2.imwrite(img_name, frame)
        print(f"✅ Đã lưu thành công: {img_name}")
        print("Bạn có thể đăng ký tiếp hoặc nhấn 'q' để thoát.")
        # Dừng 1 giây để người dùng biết đã chụp
        time.sleep(1)
        break # Thoát luôn sau khi chụp 1 tấm (hoặc bỏ dòng này nếu muốn chụp nhiều tấm)

    # Nếu nhấn 'q' -> Thoát
    elif key == ord('q'):
        print("Đã hủy đăng ký.")
        break

cam.release()
cv2.destroyAllWindows()
