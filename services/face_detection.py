import torch
from blazeface.blazeface import BlazeFace
from config import device, BLAZEFACE_WEIGHTS_PATH, BLAZEFACE_ANCHORS_PATH
from config import MIN_SCORE_THRESH, MIN_SUPPRESSION_THRESHOLD

class FaceDetector:
    def __init__(self):
        self.device = device
        self.model = self._load_model()
        
    def _load_model(self):
        """Load BlazeFace model"""
        model = BlazeFace().to(self.device)
        model.load_weights(BLAZEFACE_WEIGHTS_PATH)
        model.load_anchors(BLAZEFACE_ANCHORS_PATH)
        model.min_score_thresh = MIN_SCORE_THRESH
        model.min_suppression_threshold = MIN_SUPPRESSION_THRESHOLD
        model.eval()
        return model
    
    def detect_faces(self, image):
        """Detect faces in image"""
        with torch.no_grad():
            detections = self.model.predict_on_image(image)
        return detections