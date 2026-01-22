"""
FastAPI backend for Taxi Price Prediction
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from typing import List, Dict

# Initialize FastAPI app
app = FastAPI(
    title="Taxi Price Prediction API",
    description="API for predicting taxi trip prices",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_DIR = Path(__file__).parent.parent.parent.parent / "models"

print("Loading model artifacts...")
model = joblib.load(MODEL_DIR / "taxi_price_model.joblib")
scaler = joblib.load(MODEL_DIR / "scaler.joblib")
label_encoders = joblib.load(MODEL_DIR / "label_encoders.joblib")
feature_info = joblib.load(MODEL_DIR / "feature_names.joblib")
print("Model artifacts loaded successfully!")


# Pydantic models for request/response 
class TripInput(BaseModel):
    """Input data for a taxi trip prediction"""
    Trip_Distance_km: float = Field(..., gt=0, description="Trip distance in kilometers")
    Time_of_Day: str = Field(..., description="Time of day: Morning, Afternoon, Evening")
    Day_of_Week: str = Field(..., description="Day: Weekday or Weekend")
    Passenger_Count: float = Field(..., gt=0, le=10, description="Number of passengers")
    Traffic_Conditions: str = Field(..., description="Traffic: Low, Medium, High")
    Weather: str = Field(..., description="Weather: Clear, Rain, Fog")
    Base_Fare: float = Field(..., gt=0, description="Base fare in currency")
    Per_Km_Rate: float = Field(..., gt=0, description="Rate per kilometer")
    Per_Minute_Rate: float = Field(..., gt=0, description="Rate per minute")
    Trip_Duration_Minutes: float = Field(..., gt=0, description="Trip duration in minutes")

    class Config:
        schema_extra = {
            "example": {
                "Trip_Distance_km": 15.5,
                "Time_of_Day": "Morning",
                "Day_of_Week": "Weekday",
                "Passenger_Count": 2.0,
                "Traffic_Conditions": "Medium",
                "Weather": "Clear",
                "Base_Fare": 3.5,
                "Per_Km_Rate": 1.5,
                "Per_Minute_Rate": 0.3,
                "Trip_Duration_Minutes": 25.0
            }
        }


class PredictionResponse(BaseModel):
    """Response with predicted price"""
    predicted_price: float
    currency: str = "SEK"


# Root endpoint
@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "message": "Taxi Price Prediction API is running!",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict",
            "docs": "/docs"
        }
    }


# Prediction endpoint
@app.post("/predict", response_model=PredictionResponse)
def predict_price(trip: TripInput):
    """
    Predict taxi trip price based on input features
    """
    try:
    
        input_data = trip.dict()
        
        df = pd.DataFrame([input_data])
        
        for col in feature_info['categorical_features']:
            if col in df.columns:
                df[col] = label_encoders[col].transform(df[col])
        
        df[feature_info['numerical_features']] = scaler.transform(
            df[feature_info['numerical_features']]
        )
        
        prediction = model.predict(df)[0]
        
        return PredictionResponse(
            predicted_price=round(float(prediction), 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)