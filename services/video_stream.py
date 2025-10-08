import cv2
import time
import base64
import gc
from flask_socketio import SocketIO
from config import FRAME_SKIP, FRAME_WIDTH, FRAME_HEIGHT, RECOGNITION_THRESHOLD

class VideoStream:
    def __init__(self, face_detector, face_recognizer, database_manager, socketio):
        self.face_detector = face_detector
        self.face_recognizer = face_recognizer
        self.db_manager = database_manager
        self.socketio = socketio
        self.streaming = False
        self.cap = None
    
    def encode_frame(self, frame):
        """Encode frame to base64"""
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
        return base64.b64encode(buffer).decode('utf-8')
    
    def start_stream(self):
        """Start video streaming"""
        self.streaming = True
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        frame_id = 0
        
        try:
            while self.streaming:
                success, frame = self.cap.read()
                if not success:
                    break
                
                frame_id += 1
                
                # Skip frames for performance
                if frame_id % FRAME_SKIP != 0:
                    continue
                
                # Crop frame
                h, w = frame.shape[:2]
                frame = frame[0:h, 80:w - 80]
                
                # Process frame for face detection
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_rgb = cv2.resize(frame_rgb, (FRAME_WIDTH, FRAME_HEIGHT))
                
                # Detect faces
                detections = self.face_detector.detect_faces(frame_rgb)
                
                if len(detections) > 0:
                    frame = self._process_faces(frame, detections)
                
                # Emit frame
                encoded_frame = self.encode_frame(frame)
                self.socketio.emit('video_frame', {'image': encoded_frame})
                self.socketio.sleep(0.07)
                
                # Cleanup
                if frame_id % 15 == 0:
                    gc.collect()
                    
        finally:
            self.stop_stream()
    
    def _process_faces(self, frame, detections):
        """Process detected faces"""
        h, w = frame.shape[:2]
        
        for det in detections:
            y1, x1, y2, x2 = det[:4]
            x1, y1, x2, y2 = map(lambda v: int(v * w if v in [x1, x2] else v * h), [x1, y1, x2, y2])
            
            face_crop = frame[y1:y2, x1:x2]
            if face_crop.size == 0:
                continue
            
            # Get face embedding
            embedding = self.face_recognizer.get_embedding(face_crop)
            
            # Search in database
            D, I = self.db_manager.search_face(embedding, k=1)
            min_distance = D[0][0]
            
            if min_distance < RECOGNITION_THRESHOLD:
                recognized_person = self.db_manager.face_ids[I[0][0]]
                status = "Đã điểm danh"
                
                # Add to attendance if not already recorded
                if recognized_person in self.db_manager.remaining_people:
                    current_time = time.strftime("%H:%M:%S")
                    self.db_manager.add_attendance_record(recognized_person, current_time, status)
                    
                    # Emit recognition result
                    self.socketio.emit('recognition_result', {
                        'name': recognized_person,
                        'time': current_time,
                        'status': status
                    })
            else:
                recognized_person = "Unknown"
                status = "Không nhận diện được"
            
            # Draw bounding box and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            text = f"{recognized_person} ({min_distance:.2f})"
            cv2.putText(frame, text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 255, 0), 2, cv2.LINE_AA)
        
        return frame
    
    def stop_stream(self):
        """Stop video streaming"""
        self.streaming = False
        if self.cap:
            self.cap.release()
            self.cap = None