# backend/models/__init__.py

from .dummy_model import UnimatchDummyModel

# Try to import the enhanced ML model
try:
    from .ml_model import SNBPPredictor, get_predictor, prepare_prediction_features, train_model_if_needed
    ML_MODEL_AVAILABLE = True
except ImportError as e:
    print(f"ML model not available: {e}")
    ML_MODEL_AVAILABLE = False
    
    # Fallback classes
    class SNBPPredictor:
        def predict_probability(self, features):
            return 0.5
    
    def get_predictor():
        return SNBPPredictor()
    
    def prepare_prediction_features(request_data):
        return {}
    
    def train_model_if_needed():
        return False

__all__ = [
    "UnimatchDummyModel", 
    "SNBPPredictor", 
    "get_predictor", 
    "prepare_prediction_features", 
    "train_model_if_needed",
    "ML_MODEL_AVAILABLE"
]