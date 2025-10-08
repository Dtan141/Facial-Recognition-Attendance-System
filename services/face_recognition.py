import torch
import torch.nn.functional as F
import torch.jit
from torchvision import transforms
from PIL import Image
import numpy as np
from config import device, FACENET_MODEL_PATH

class FaceRecognizer:
    def __init__(self):
        self.device = device
        self.model = self._load_model()
        self.transform = self._get_transform()
        
    def _load_model(self):
        """Load FaceNet model"""
        model = torch.jit.load(FACENET_MODEL_PATH, map_location=self.device)
        model.eval()
        return model
    
    def _get_transform(self):
        """Get face transformation pipeline"""
        return transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((160, 160)),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5])
        ])
    
    def get_embedding(self, face_image):
        """Get face embedding from face image"""
        face_tensor = self.transform(face_image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            embedding = self.model(face_tensor)
            embedding = F.normalize(embedding.cpu())
        return embedding.numpy().astype('float32')