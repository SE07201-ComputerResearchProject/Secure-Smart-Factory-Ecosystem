try:
    import face_recognition
    print("Ngon rồi Thọ ơi! Thư viện đã nhận diện được bộ não.")
    # Thử chạy một lệnh test nhỏ
    locations = face_recognition.face_locations([[0]*100]*100) 
    print("Test thành công!")
except Exception as e:
    print(f"Vẫn lỗi rồi: {e}")
