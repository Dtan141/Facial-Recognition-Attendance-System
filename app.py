# import cv2
# import time
# import torch
# import gc
# import pickle
# import base64
# import faiss
# import torch.nn.functional as F
# from flask import Flask, render_template, Response, jsonify, request
# from PIL import Image
# import numpy as np
# from flask_socketio import SocketIO
# from torchvision import transforms
# from blazeface.blazeface import BlazeFace
# import csv
# import io

# app = Flask(__name__, static_folder='static')
# socketio = SocketIO(app)

# # Load models
# device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# blazeface = BlazeFace().to(device)
# blazeface.load_weights("models/blazeface.pth")
# blazeface.load_anchors("models/anchors.npy")
# blazeface.min_score_thresh = 0.7
# blazeface.min_suppression_threshold = 0.3
# blazeface.eval()

# facenet = torch.jit.load("models/mobilefacenet_scripted.pt", map_location=device)
# facenet.eval()

# face_transform = transforms.Compose([
#     transforms.ToPILImage(),
#     transforms.Resize((160, 160)),
#     transforms.ToTensor(),
#     transforms.Normalize([0.5], [0.5])
# ])

# index_path = 'database/face_index.faiss'
# id_mapping_path = 'database/face_ids.pkl'

# faiss_index = faiss.read_index(index_path)

# attendance_records = []

# with open(id_mapping_path, 'rb') as f:
#     face_ids = pickle.load(f)
    
# remaining_people = set(face_ids)

# streaming = False

# def encode_frame(frame):
#     ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
#     return base64.b64encode(buffer).decode('utf-8')

# @socketio.on('start_stream')
# def start_stream_handler():
#     global streaming
#     streaming = True
#     socketio.start_background_task(target=stream_video)

# @socketio.on('stop_stream')
# def stop_stream_handler():
#     global streaming
#     streaming = False
#     print("🛑 Streaming stopped by client.")

# def stream_video(threshold=0.38):
#     global streaming
#     global remaining_people

#     cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
#     frame_id = 0

#     try:
#         while streaming:
#             success, frame = cap.read()
#             if not success:
#                 break

#             frame_id += 1

#             if frame_id % 3 != 0:
#                 continue

#             h, w = frame.shape[:2]
#             frame = frame[0:h, 80:w - 80]

#             frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             frame_rgb = cv2.resize(frame_rgb, (128, 128))

#             with torch.no_grad():
#                 detections = blazeface.predict_on_image(frame_rgb)

#             if len(detections) == 0:
#                 frame = encode_frame(frame)
#                 socketio.emit('video_frame', {'image': frame})
#                 socketio.sleep(0.01)
#                 continue

#             h, w = frame.shape[:2]
#             for det in detections:
#                 y1, x1, y2, x2 = det[:4]
#                 x1, y1, x2, y2 = map(lambda v: int(v * w if v in [x1, x2] else v * h), [x1, y1, x2, y2])
#                 face_crop = frame[y1:y2, x1:x2]
#                 if face_crop.size == 0:
#                     continue

#                 face_tensor = face_transform(face_crop).unsqueeze(0).to(device)
#                 with torch.no_grad():
#                     embedding = facenet(face_tensor)
#                     embedding = F.normalize(embedding.cpu())

#                 embedding_np = embedding.numpy().astype('float32')
#                 D, I = faiss_index.search(embedding_np, k=1)
#                 min_distance = D[0][0]

#                 if min_distance < threshold:
#                     recognized_person = face_ids[I[0][0]]
#                     if recognized_person in remaining_people:
#                         remaining_people.remove(recognized_person)           
#                         status = "Đã điểm danh"
#                         attendance_records.append({
#                             'name': recognized_person,
#                             'time': time.strftime("%H:%M:%S"),
#                             'status': status
#                         })
#                         # Emit dữ liệu nhận diện về client
#                         socketio.emit('recognition_result', {
#                             'name': recognized_person,
#                             'time': time.strftime("%H:%M:%S"),
#                             'status': status
#                         })

#                 else:
#                     recognized_person = "Unknown"
#                     status = "Không nhận diện được"
                
#                 cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#                 text = f"{recognized_person} ({min_distance:.2f})"
#                 cv2.putText(frame, text, (x1, y1 - 10),
#                             cv2.FONT_HERSHEY_SIMPLEX, 0.6,
#                             (0, 255, 0), 2, cv2.LINE_AA)

#             frame = encode_frame(frame)
#             socketio.emit('video_frame', {'image': frame})
#             socketio.sleep(0.07)

#             if frame_id % 15 == 0:
#                 del face_tensor, embedding
#                 gc.collect()
#     finally:
#         cap.release()

# @app.route('/')
# def index():
#     return render_template('video.html')

# @app.route('/export_csv')
# def export_csv():
#     if not attendance_records:
#         return Response("Không có dữ liệu để xuất!", mimetype='text/plain')
    
#     output = io.StringIO()
#     writer = csv.DictWriter(output, fieldnames=['STT', 'Tên', 'Thời gian', 'Trạng thái'])
#     writer.writeheader()
#     for i, row in enumerate(attendance_records, start=1):
#         writer.writerow({
#             'STT': i,
#             'Tên': row['name'],
#             'Thời gian': row['time'],
#             'Trạng thái': row['status']
#         })

#     response = Response(output.getvalue(), mimetype='text/csv')
#     response.headers['Content-Disposition'] = 'attachment; filename=attendance.csv'
#     return response

# @app.route('/reset_attendance', methods=['POST'])
# def reset_attendance():
#     global attendance_records
#     attendance_records = []
#     global remaining_people
#     remaining_people = set(face_ids)
#     print("✅ Attendance records cleared.")
#     return jsonify({'message': 'Danh sách điểm danh đã được xóa'})

# @app.route('/register', methods=['POST'])
# def register_user():
#     name = request.form['name']
#     image_file = request.files['image']

#     save_path = f"static/faces/{name}.jpg"
#     image_file.save(save_path)

#     img = cv2.imread(save_path)
#     img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#     img = cv2.resize(img, (128, 128))

#     with torch.no_grad():
#         detections = blazeface.predict_on_image(img)

#     if len(detections) == 1:
#         y1, x1, y2, x2 = detections[0][:4]  # Lấy bounding box đầu tiên
#         h, w = img.shape[:2]
#         x1, y1, x2, y2 = map(int, [x1 * w, y1 * h, x2 * w, y2 * h])  # Quy đổi toạ độ về pixel
#         face_crop = img[y1:y2, x1:x2]

#         if face_crop.size == 0:
#             return jsonify({"error": "Không thể cắt khuôn mặt từ ảnh!"}), 400

#         # Áp dụng transform lên ảnh khuôn mặt
#         face_img = face_transform(face_crop).unsqueeze(0).to(device)
#         with torch.no_grad():
#             embedding = facenet(face_img)
#             embedding = F.normalize(embedding.cpu()).numpy().astype('float32')
#         faiss_index.add(embedding)
#         face_ids.append(name)
#         remaining_people.add(name)
#     else:
#         return jsonify({"error": "Vui lòng cung cấp ảnh có đúng 1 khuôn mặt!"}), 400

#     return jsonify({"message": f"Đăng ký thành công cho {name}!"})


# if __name__ == '__main__':
#     socketio.run(app, debug=False)
from flask import Flask
from flask_socketio import SocketIO
from services import FaceDetector, FaceRecognizer, DatabaseManager, VideoStream
from routes.main import main_bp, init_main_routes
from routes.register import register_bp, init_register_routes

# Initialize Flask app
app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)

# Initialize services (chỉ một instance duy nhất)
face_detector = FaceDetector()
face_recognizer = FaceRecognizer()
db_manager = DatabaseManager()
video_stream = VideoStream(face_detector, face_recognizer, db_manager, socketio)

# Khởi tạo routes với dependencies
init_main_routes(db_manager)
init_register_routes(face_detector, face_recognizer, db_manager)

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(register_bp)

# SocketIO events
@socketio.on('start_stream')
def start_stream_handler():
    video_stream.streaming = True
    socketio.start_background_task(target=video_stream.start_stream)

@socketio.on('stop_stream')
def stop_stream_handler():
    video_stream.stop_stream()
    print("🛑 Streaming stopped by client.")

if __name__ == '__main__':
    socketio.run(app, debug=False)