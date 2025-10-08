from flask import Blueprint, request, jsonify
import cv2

register_bp = Blueprint('register', __name__)

# Không tạo instance ở đây nữa
face_detector = None
face_recognizer = None
db_manager = None

def init_register_routes(face_detector_instance, face_recognizer_instance, db_manager_instance):
    global face_detector, face_recognizer, db_manager
    face_detector = face_detector_instance
    face_recognizer = face_recognizer_instance
    db_manager = db_manager_instance

@register_bp.route('/register', methods=['POST'])
def register_user():
    if None in [face_detector, face_recognizer, db_manager]:
        return jsonify({"error": "Services not initialized!"}), 500
        
    name = request.form['name']
    image_file = request.files['image']

    # Save image
    save_path = f"static/faces/{name}.jpg"
    image_file.save(save_path)

    # Process image
    img = cv2.imread(save_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (128, 128))

    # Detect faces
    detections = face_detector.detect_faces(img)

    if len(detections) == 1:
        y1, x1, y2, x2 = detections[0][:4]
        h, w = img.shape[:2]
        x1, y1, x2, y2 = map(int, [x1 * w, y1 * h, x2 * w, y2 * h])
        face_crop = img[y1:y2, x1:x2]

        if face_crop.size == 0:
            return jsonify({"error": "Không thể cắt khuôn mặt từ ảnh!"}), 400

        # Get embedding and add to database
        embedding = face_recognizer.get_embedding(face_crop)
        db_manager.add_face(embedding, name)
        
        return jsonify({"message": f"Đăng ký thành công cho {name}!"})
    else:
        return jsonify({"error": "Vui lòng cung cấp ảnh có đúng 1 khuôn mặt!"}), 400
    