import faiss
import pickle
from config import INDEX_PATH, ID_MAPPING_PATH

class DatabaseManager:
    def __init__(self):
        self.index_path = INDEX_PATH
        self.id_mapping_path = ID_MAPPING_PATH
        self.faiss_index = self._load_index()
        self.face_ids = self._load_face_ids()
        self.remaining_people = set(self.face_ids)
        self.attendance_records = []
    
    def _load_index(self):
        """Load FAISS index"""
        return faiss.read_index(self.index_path)
    
    def _load_face_ids(self):
        """Load face IDs mapping"""
        with open(self.id_mapping_path, 'rb') as f:
            return pickle.load(f)
    
    def search_face(self, embedding, k=1):
        """Search for similar faces in database"""
        return self.faiss_index.search(embedding, k=k)
    
    def add_face(self, embedding, name):
        """Add new face to database"""
        self.faiss_index.add(embedding)
        self.face_ids.append(name)
        self.remaining_people.add(name)
        self._save_database()
    
    def _save_database(self):
        """Save database to disk"""
        faiss.write_index(self.faiss_index, self.index_path)
        with open(self.id_mapping_path, 'wb') as f:
            pickle.dump(self.face_ids, f)
    
    def add_attendance_record(self, name, time, status):
        """Add attendance record"""
        record = {
            'name': name,
            'time': time,
            'status': status
        }
        self.attendance_records.append(record)
        
        # Remove from remaining people if recognized
        if status == "Đã điểm danh" and name in self.remaining_people:
            self.remaining_people.remove(name)
    
    def reset_attendance(self):
        """Reset attendance records"""
        self.attendance_records = []
        self.remaining_people = set(self.face_ids)
    
    def get_attendance_records(self):
        """Get all attendance records"""
        return self.attendance_records