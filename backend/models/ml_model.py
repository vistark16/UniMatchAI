"""
Enhanced ML Model for SNBP prediction using student training data.
This model learns from historical acceptance data to make better predictions.
"""

import json
import pickle
import pathlib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings('ignore')

ROOT = pathlib.Path(__file__).resolve().parent
STUDENT_DATA_PATH = ROOT / "data" / "processed_student_data.json"
STATISTICS_PATH = ROOT / "data" / "student_statistics.json"
MODEL_PATH = ROOT / "models" / "snbp_model.pkl"
SCALER_PATH = ROOT / "models" / "feature_scaler.pkl"
ENCODERS_PATH = ROOT / "models" / "label_encoders.pkl"

# Ensure models directory exists
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

class SNBPPredictor:
    """Enhanced SNBP Prediction Model"""
    
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_stats = {}
        self.is_trained = False
        
    def load_training_data(self):
        """Load processed student training data"""
        if not STUDENT_DATA_PATH.exists():
            raise FileNotFoundError(f"Training data not found: {STUDENT_DATA_PATH}")
            
        with open(STUDENT_DATA_PATH, 'r', encoding='utf-8') as f:
            student_data = json.load(f)
            
        with open(STATISTICS_PATH, 'r', encoding='utf-8') as f:
            self.feature_stats = json.load(f)
            
        return student_data
    
    def prepare_features(self, student_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare feature matrix and labels for training"""
        features_list = []
        labels = []
        feature_names = None
        
        for student in student_data:
            features = student['features']
            
            # Ensure consistent feature ordering
            if feature_names is None:
                feature_names = sorted(features.keys())
            
            # Create feature vector
            feature_vector = [features.get(fname, 0) for fname in feature_names]
            features_list.append(feature_vector)
            
            # Label is always 1 (accepted) for training data
            labels.append(1)
        
        X = np.array(features_list)
        y = np.array(labels)
        
        return X, y, feature_names
    
    def generate_negative_samples(self, student_data: List[Dict], ratio: float = 0.3) -> List[Dict]:
        """Generate synthetic negative samples (rejected students)"""
        negative_samples = []
        n_negatives = int(len(student_data) * ratio)
        
        # Strategy: Lower grades + mismatched programs
        for i in range(n_negatives):
            # Pick a random positive sample as template
            template = np.random.choice(student_data)
            
            # Create degraded version
            negative_sample = template.copy()
            features = negative_sample['features'].copy()
            
            # Reduce academic scores by 5-15 points
            grade_reduction = np.random.uniform(5, 15)
            features['rapor_avg'] = max(60, features['rapor_avg'] - grade_reduction)
            features['core_avg'] = max(60, features['core_avg'] - grade_reduction)
            features['program_avg'] = max(60, features['program_avg'] - grade_reduction)
            features['math_score'] = max(60, features['math_score'] - grade_reduction)
            features['language_score'] = max(60, features['language_score'] - grade_reduction)
            
            # Sometimes flip program compatibility
            if np.random.random() < 0.4:
                features['program_match'] = 0
                
            # Reduce subject-specific scores
            for subject in ['physics_score', 'chemistry_score', 'biology_score', 
                          'economics_score', 'geography_score', 'history_score']:
                if features.get(subject, 0) > 0:
                    features[subject] = max(60, features[subject] - grade_reduction)
            
            negative_sample['features'] = features
            negative_sample['target'] = 0  # Rejected
            negative_sample['student_id'] = f"neg_{i}"
            
            negative_samples.append(negative_sample)
        
        return negative_samples
    
    def train_models(self, force_retrain: bool = False):
        """Train multiple ML models"""
        
        # Check if models already exist
        if not force_retrain and self.load_trained_models():
            print("Loaded existing trained models")
            return
        
        print("Training new models...")
        
        # Load training data
        student_data = self.load_training_data()
        print(f"Loaded {len(student_data)} positive samples")
        
        # Generate negative samples
        negative_samples = self.generate_negative_samples(student_data)
        print(f"Generated {len(negative_samples)} negative samples")
        
        # Combine positive and negative samples
        all_samples = student_data + negative_samples
        np.random.shuffle(all_samples)
        
        # Prepare features
        X, y, feature_names = self.prepare_features(all_samples)
        print(f"Feature matrix shape: {X.shape}")
        print(f"Class distribution: {np.bincount(y)}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train multiple models
        models_config = {
            'random_forest': RandomForestClassifier(
                n_estimators=100, 
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'logistic_regression': LogisticRegression(
                random_state=42,
                class_weight='balanced',
                max_iter=1000
            )
        }
        
        best_model = None
        best_score = 0
        
        print("\nTraining and evaluating models:")
        for name, model in models_config.items():
            # Train model
            if name == 'logistic_regression':
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                y_prob = model.predict_proba(X_test_scaled)[:, 1]
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                y_prob = model.predict_proba(X_test)[:, 1]
            
            # Evaluate
            auc_score = roc_auc_score(y_test, y_prob)
            
            print(f"\n{name.upper()}:")
            print(f"AUC Score: {auc_score:.4f}")
            print(classification_report(y_test, y_pred, target_names=['Rejected', 'Accepted']))
            
            # Save model
            self.models[name] = model
            
            # Track best model
            if auc_score > best_score:
                best_score = auc_score
                best_model = name
        
        print(f"\nBest model: {best_model} (AUC: {best_score:.4f})")
        self.best_model_name = best_model
        self.feature_names = feature_names
        self.is_trained = True
        
        # Save models
        self.save_trained_models()
        
    def save_trained_models(self):
        """Save trained models to disk"""
        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'best_model_name': self.best_model_name,
            'feature_stats': self.feature_stats
        }
        
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Models saved to: {MODEL_PATH}")
    
    def load_trained_models(self) -> bool:
        """Load trained models from disk"""
        if not MODEL_PATH.exists():
            return False
            
        try:
            with open(MODEL_PATH, 'rb') as f:
                model_data = pickle.load(f)
            
            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.best_model_name = model_data['best_model_name']
            self.feature_stats = model_data.get('feature_stats', {})
            self.is_trained = True
            
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
    
    def predict_probability(self, features: Dict[str, Any]) -> float:
        """Predict acceptance probability for a student"""
        if not self.is_trained:
            if not self.load_trained_models():
                # Fallback to heuristic if no trained model
                return self._heuristic_prediction(features)
        
        # Prepare feature vector
        feature_vector = []
        for fname in self.feature_names:
            feature_vector.append(features.get(fname, 0))
        
        X = np.array([feature_vector])
        
        # Get prediction from best model
        best_model = self.models[self.best_model_name]
        
        if self.best_model_name == 'logistic_regression':
            X = self.scaler.transform(X)
        
        probability = best_model.predict_proba(X)[0, 1]
        
        return float(probability)
    
    def _heuristic_prediction(self, features: Dict[str, Any]) -> float:
        """Fallback heuristic prediction if no trained model available"""
        rapor_avg = features.get('rapor_avg', 75)
        core_avg = features.get('core_avg', rapor_avg)
        program_match = features.get('program_match', 1)
        
        # Simple heuristic based on grades and program match
        base_score = (rapor_avg + core_avg) / 2
        
        # Normalize to 0-100 scale
        normalized_score = max(0, min(100, base_score))
        
        # Apply program match penalty
        if program_match == 0:
            normalized_score *= 0.8
        
        # Convert to probability using sigmoid
        probability = 1 / (1 + np.exp(-0.1 * (normalized_score - 75)))
        
        return float(probability)
    
    def get_feature_importance(self, model_name: str = None) -> Dict[str, float]:
        """Get feature importance from trained models"""
        if not self.is_trained:
            return {}
            
        model_name = model_name or self.best_model_name
        model = self.models.get(model_name)
        
        if not model or not hasattr(model, 'feature_importances_'):
            return {}
        
        importance_dict = {}
        for i, importance in enumerate(model.feature_importances_):
            feature_name = self.feature_names[i]
            importance_dict[feature_name] = float(importance)
        
        # Sort by importance
        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))

def prepare_prediction_features(request_data: Dict) -> Dict[str, Any]:
    """Convert API request data to ML model features"""
    # Extract grades
    grades = [request_data.get(f's{i}') for i in range(1, 6)]
    valid_grades = [g for g in grades if g is not None]
    rapor_avg = np.mean(valid_grades) if valid_grades else 75.0
    
    # Program determination
    program = request_data.get('program', 'saintek')
    is_saintek = 1 if program == 'saintek' else 0
    is_soshum = 1 if program == 'soshum' else 0
    
    # Core subjects
    math_score = request_data.get('math', rapor_avg)
    language_score = (request_data.get('language', rapor_avg) + 
                     request_data.get('bahasa_inggris', rapor_avg)) / 2
    
    # Program-specific subjects
    if program == 'saintek':
        core_subjects = [
            request_data.get('math', rapor_avg),
            request_data.get('physics', rapor_avg),
            request_data.get('chemistry', rapor_avg),
            request_data.get('biology', rapor_avg),
            language_score
        ]
        physics_score = request_data.get('physics', 0)
        chemistry_score = request_data.get('chemistry', 0)
        biology_score = request_data.get('biology', 0)
        economics_score = 0
        geography_score = 0
        history_score = 0
    else:
        core_subjects = [
            request_data.get('math', rapor_avg),
            request_data.get('economics', rapor_avg),
            request_data.get('geography', rapor_avg),
            request_data.get('history', rapor_avg),
            language_score
        ]
        physics_score = 0
        chemistry_score = 0
        biology_score = 0
        economics_score = request_data.get('economics', 0)
        geography_score = request_data.get('geography', 0)
        history_score = request_data.get('history', 0)
    
    core_avg = np.mean([s for s in core_subjects if s > 0]) if any(s > 0 for s in core_subjects) else rapor_avg
    program_avg = core_avg
    
    # Program compatibility (simplified heuristic)
    target_major = request_data.get('target_major', '').upper()
    program_match = 1
    if program == 'saintek' and any(keyword in target_major for keyword in ['EKONOMI', 'HUKUM', 'KOMUNIKASI', 'SASTRA']):
        program_match = 0
    elif program == 'soshum' and any(keyword in target_major for keyword in ['TEKNIK', 'KEDOKTERAN', 'FARMASI']):
        program_match = 0
    
    features = {
        'rapor_avg': rapor_avg,
        'core_avg': core_avg,
        'program_avg': program_avg,
        'math_score': math_score,
        'language_score': language_score,
        'program_saintek': is_saintek,
        'program_soshum': is_soshum,
        'program_match': program_match,
        'physics_score': physics_score,
        'chemistry_score': chemistry_score,
        'biology_score': biology_score,
        'economics_score': economics_score,
        'geography_score': geography_score,
        'history_score': history_score,
    }
    
    return features

# Global predictor instance
_predictor = None

def get_predictor() -> SNBPPredictor:
    """Get or create global predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = SNBPPredictor()
    return _predictor

def train_model_if_needed():
    """Train model if training data is available"""
    if STUDENT_DATA_PATH.exists():
        predictor = get_predictor()
        predictor.train_models(force_retrain=False)
        return True
    return False

if __name__ == "__main__":
    # Train models when run directly
    predictor = SNBPPredictor()
    predictor.train_models(force_retrain=True)
    
    # Test prediction
    test_features = {
        'rapor_avg': 85.0,
        'core_avg': 87.0,
        'program_avg': 86.0,
        'math_score': 88.0,
        'language_score': 85.0,
        'program_saintek': 1,
        'program_soshum': 0,
        'program_match': 1,
        'physics_score': 85.0,
        'chemistry_score': 84.0,
        'biology_score': 86.0,
        'economics_score': 0,
        'geography_score': 0,
        'history_score': 0,
    }
    
    probability = predictor.predict_probability(test_features)
    print(f"\nTest prediction: {probability:.3f}")
    
    # Show feature importance
    importance = predictor.get_feature_importance()
    print("\nTop 10 Feature Importance:")
    for feature, imp in list(importance.items())[:10]:
        print(f"  {feature}: {imp:.3f}")