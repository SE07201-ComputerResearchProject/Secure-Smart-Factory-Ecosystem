import os
import sys

# Ép Python tìm đúng vào ổ chứa model trong môi trường ảo
site_packages = os.path.join(os.getcwd(), 'venv/lib/python3.12/site-packages')
if site_packages not in sys.path:
    sys.path.insert(0, site_packages)

import cv2
import face_recognition
import time

# Khởi động camera
video_capture = cv2.VideoCapture(0)
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

print("[INFO] He thong dang mo mat... doi xiu nhe!")
time.sleep(2.0)

if not video_capture.isOpened():
    print("[ERROR] Khong tim thay camera! Kiem tra VM -> Removable Devices.")
    exit()

print("[INFO] ĐANG CHAY! Nhan 'q' de thoat.")

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    # Nhan dien khuon mat
    face_locations = face_recognition.face_locations(frame)

    for (top, right, bottom, left) in face_locations:
        # Ve khung xanh quanh mat
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, "Human Detected", (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow("Smart Factory - Dev Mode", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
