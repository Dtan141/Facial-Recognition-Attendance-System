import torch

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Model paths
BLAZEFACE_WEIGHTS_PATH = "models/blazeface.pth"
BLAZEFACE_ANCHORS_PATH = "models/anchors.npy"
FACENET_MODEL_PATH = "models/mobilefacenet_scripted.pt"

# Database paths
INDEX_PATH = 'database/face_index.faiss'
ID_MAPPING_PATH = 'database/face_ids.pkl'

# Face detection settings
MIN_SCORE_THRESH = 0.7
MIN_SUPPRESSION_THRESHOLD = 0.3
RECOGNITION_THRESHOLD = 0.38

# Video settings
FRAME_SKIP = 3
FRAME_WIDTH = 128
FRAME_HEIGHT = 128