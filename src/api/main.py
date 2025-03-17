from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
import uvicorn

from ..config.settings import settings
from ..models.prediction import DeliveryPrediction
from ..services.sap_service import SAPService
from ..services.prediction_service import PredictionService
from ..services.external_service import ExternalDataService

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize services
sap_service = SAPService()
prediction_service = PredictionService()
external_service = ExternalDataService()

@app.get("/")
async def root():
    return {"message": "SAP AI Agent - Supplier Delivery Prediction System"}

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "sap_connection": sap_service.check_connection()
    }

@app.get("/api/v1/suppliers/deliveries/predictions")
async def get_delivery_predictions(
    supplier_id: Optional[str] = None,
    days_ahead: int = 7,
    token: str = Depends(oauth2_scheme)
):
    try:
        # Get delivery data from SAP
        delivery_data = await sap_service.get_delivery_data(supplier_id)
        
        # Get external factors
        weather_data = await external_service.get_weather_forecast()
        traffic_data = await external_service.get_traffic_conditions()
        
        # Make predictions
        predictions = prediction_service.predict_delays(
            delivery_data,
            weather_data,
            traffic_data,
            days_ahead
        )
        
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/alerts/configure")
async def configure_alerts(
    threshold: float,
    email: str,
    token: str = Depends(oauth2_scheme)
):
    try:
        # Update alert settings
        settings.ALERT_THRESHOLD_PROBABILITY = threshold
        settings.NOTIFICATION_EMAIL = email
        return {"message": "Alert settings updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 