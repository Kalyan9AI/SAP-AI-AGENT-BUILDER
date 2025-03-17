from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DeliveryPrediction(BaseModel):
    supplier_id: str
    delivery_id: str
    predicted_delivery_date: datetime
    original_delivery_date: datetime
    delay_probability: float
    estimated_delay_hours: float
    confidence_score: float
    factors: List[dict]
    
    class Config:
        from_attributes = True

class PredictionInput(BaseModel):
    supplier_id: str
    delivery_id: str
    scheduled_date: datetime
    origin_location: dict
    destination_location: dict
    cargo_type: str
    weight: float
    historical_performance: Optional[dict]
    weather_conditions: Optional[dict]
    traffic_conditions: Optional[dict]

class PredictionResult(BaseModel):
    predictions: List[DeliveryPrediction]
    generated_at: datetime
    model_version: str
    recommendations: List[str] 