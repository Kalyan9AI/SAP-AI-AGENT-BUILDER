import joblib
import numpy as np
import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from ..config.settings import settings
from ..models.prediction import DeliveryPrediction, PredictionInput

class PredictionService:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.model_version = "1.0.0"
        self.load_model()

    def load_model(self):
        """Load the trained model and scaler"""
        try:
            model_data = joblib.load(settings.MODEL_PATH)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
        except FileNotFoundError:
            # Initialize new model if not found
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.scaler = StandardScaler()

    def save_model(self):
        """Save the current model and scaler"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'version': self.model_version
        }
        joblib.dump(model_data, settings.MODEL_PATH)

    def preprocess_features(self, 
                          delivery_data: List[Dict],
                          weather_data: Dict,
                          traffic_data: Dict) -> np.ndarray:
        """Preprocess input features for prediction"""
        features = []
        
        for delivery in delivery_data:
            # Basic delivery features
            delivery_features = [
                float(delivery['items']),
                float(delivery.get('distance', 0)),
                float(delivery.get('estimated_duration', 0))
            ]
            
            # Weather features
            weather_features = [
                float(weather_data.get('temperature', 20)),
                float(weather_data.get('precipitation', 0)),
                float(weather_data.get('wind_speed', 0))
            ]
            
            # Traffic features
            traffic_features = [
                float(traffic_data.get('congestion_level', 0)),
                float(traffic_data.get('incident_count', 0))
            ]
            
            # Combine all features
            combined_features = delivery_features + weather_features + traffic_features
            features.append(combined_features)
        
        # Scale features
        if len(features) > 0:
            features = self.scaler.fit_transform(features)
        
        return np.array(features)

    def predict_delays(self,
                      delivery_data: List[Dict],
                      weather_data: Dict,
                      traffic_data: Dict,
                      days_ahead: int = 7) -> List[DeliveryPrediction]:
        """Predict delivery delays"""
        try:
            # Preprocess features
            features = self.preprocess_features(delivery_data, weather_data, traffic_data)
            
            # Make predictions
            delay_predictions = self.model.predict(features)
            delay_probabilities = self.model.predict_proba(features)[:, 1] if hasattr(self.model, 'predict_proba') else np.ones(len(features)) * 0.5
            
            # Create prediction results
            predictions = []
            for i, delivery in enumerate(delivery_data):
                scheduled_date = datetime.strptime(delivery['scheduled_date'], '%Y%m%d')
                predicted_delay = delay_predictions[i]
                
                prediction = DeliveryPrediction(
                    supplier_id=delivery['supplier_id'],
                    delivery_id=delivery['delivery_id'],
                    predicted_delivery_date=scheduled_date + timedelta(hours=predicted_delay),
                    original_delivery_date=scheduled_date,
                    delay_probability=delay_probabilities[i],
                    estimated_delay_hours=predicted_delay,
                    confidence_score=0.8,  # This could be calculated based on model metrics
                    factors=[
                        {
                            'name': 'weather',
                            'impact': weather_data.get('severity', 'low'),
                            'description': weather_data.get('description', '')
                        },
                        {
                            'name': 'traffic',
                            'impact': traffic_data.get('severity', 'low'),
                            'description': traffic_data.get('description', '')
                        }
                    ]
                )
                predictions.append(prediction)
            
            return predictions
        
        except Exception as e:
            raise Exception(f"Failed to make predictions: {str(e)}")

    async def retrain_model(self, historical_data: List[Dict]):
        """Retrain the model with new data"""
        try:
            # Prepare training data
            X_train = []
            y_train = []
            
            for data in historical_data:
                features = self.preprocess_features(
                    [data['delivery_data']],
                    data['weather_data'],
                    data['traffic_data']
                )
                X_train.append(features[0])
                y_train.append(data['actual_delay'])
            
            X_train = np.array(X_train)
            y_train = np.array(y_train)
            
            # Retrain model
            self.model.fit(X_train, y_train)
            
            # Update version and save
            self.model_version = f"1.0.{datetime.now().strftime('%Y%m%d')}"
            self.save_model()
            
            return True
        
        except Exception as e:
            raise Exception(f"Failed to retrain model: {str(e)}")

    def get_feature_importance(self) -> Dict:
        """Get feature importance scores"""
        if hasattr(self.model, 'feature_importances_'):
            feature_names = [
                'items', 'distance', 'duration',
                'temperature', 'precipitation', 'wind_speed',
                'congestion', 'incidents'
            ]
            
            importance = dict(zip(feature_names, self.model.feature_importances_))
            return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        
        return {} 