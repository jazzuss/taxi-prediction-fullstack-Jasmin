"""
Streamlit Frontend for Taxi Price Prediction
"""
import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

API_URL = "http://localhost:8000/predict"

# Initialize geocoder
geolocator = Nominatim(user_agent="taxi_price_predictor")

# Page config
st.set_page_config(
    page_title="Taxi Price Prediction",
    page_icon="🚕",
    layout="wide"
)

# Title
st.title("🚕 Taxi Price Prediction")
st.markdown("---")

# Create tabs for two versions
tab1, tab2 = st.tabs(["Basic Prediction", "🗺️ Route-based Prediction"])

# basic prediction
with tab1:
    st.markdown("### Predict taxi price based on trip details")
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Trip Details")
        
        trip_distance = st.number_input(
            "Trip Distance (km)",
            min_value=0.1,
            max_value=100.0,
            value=15.5,
            step=0.1,
            key="basic_distance"
        )
        
        time_of_day = st.selectbox(
            "Time of Day",
            options=["Morning", "Afternoon", "Evening"],
            index=0,
            key="basic_time"
        )
        
        day_of_week = st.selectbox(
            "Day of Week",
            options=["Weekday", "Weekend"],
            index=0,
            key="basic_day"
        )
        
        passenger_count = st.number_input(
            "Number of Passengers",
            min_value=1,
            max_value=10,
            value=2,
            step=1,
            key="basic_passengers"
        )
        
        traffic_conditions = st.selectbox(
            "Traffic Conditions",
            options=["Low", "Medium", "High"],
            index=1,
            key="basic_traffic"
        )
    
    with col2:
        st.subheader("Pricing & Weather")
        
        weather = st.selectbox(
            "Weather",
            options=["Clear", "Rain", "Fog"],
            index=0,
            key="basic_weather"
        )
        
        base_fare = st.number_input(
            "Base Fare (SEK)",
            min_value=0.1,
            max_value=20.0,
            value=3.5,
            step=0.1,
            key="basic_base"
        )
        
        per_km_rate = st.number_input(
            "Rate per Kilometer (SEK)",
            min_value=0.1,
            max_value=10.0,
            value=1.5,
            step=0.1,
            key="basic_km_rate"
        )
        
        per_minute_rate = st.number_input(
            "Rate per Minute (SEK)",
            min_value=0.01,
            max_value=5.0,
            value=0.3,
            step=0.01,
            key="basic_min_rate"
        )
        
        trip_duration = st.number_input(
            "Trip Duration (minutes)",
            min_value=1,
            max_value=300,
            value=25,
            step=1,
            key="basic_duration"
        )
    
    st.markdown("---")
    
    if st.button("Predict Price", type="primary", key="basic_predict"):
        trip_data = {
            "Trip_Distance_km": float(trip_distance),
            "Time_of_Day": time_of_day,
            "Day_of_Week": day_of_week,
            "Passenger_Count": float(passenger_count),
            "Traffic_Conditions": traffic_conditions,
            "Weather": weather,
            "Base_Fare": float(base_fare),
            "Per_Km_Rate": float(per_km_rate),
            "Per_Minute_Rate": float(per_minute_rate),
            "Trip_Duration_Minutes": float(trip_duration)
        }
        
        try:
            with st.spinner("Calculating price..."):
                response = requests.post(API_URL, json=trip_data)
            
            if response.status_code == 200:
                result = response.json()
                predicted_price = result["predicted_price"]
                
                st.success("Prediction successful!")
                st.markdown("### Estimated Trip Price")
                st.markdown(f"# {predicted_price:.2f} {result['currency']}")
                
                st.info(f"""
                **Trip Summary:**
                - Distance: {trip_distance} km
                - Duration: {trip_duration} minutes
                - Time: {time_of_day}, {day_of_week}
                - Traffic: {traffic_conditions}
                - Weather: {weather}
                """)
            else:
                st.error(f"Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend API")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with tab2:
    st.markdown("## Enter locations and see route on map")
    
    # Location inputs
    col_from, col_to = st.columns(2)
    
    with col_from:
        from_location = st.text_input(
            "📍 From (City or Address)",
            value="Stockholm",
            help="Enter starting location"
        )
    
    with col_to:
        to_location = st.text_input(
            "📍 To (City or Address)",
            value="Göteborg",
            help="Enter destination"
        )
    
    # Additional parameters
    with st.expander("Trip Parameters", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            route_time = st.selectbox(
                "Time of Day",
                options=["Morning", "Afternoon", "Evening"],
                key="route_time"
            )
            
            route_day = st.selectbox(
                "Day of Week",
                options=["Weekday", "Weekend"],
                key="route_day"
            )
            
            route_passengers = st.number_input(
                "Passengers",
                min_value=1,
                max_value=10,
                value=2,
                key="route_passengers"
            )
        
        with col2:
            route_traffic = st.selectbox(
                "Traffic",
                options=["Low", "Medium", "High"],
                index=1,
                key="route_traffic"
            )
            
            route_weather = st.selectbox(
                "Weather",
                options=["Clear", "Rain", "Fog"],
                key="route_weather"
            )
    
    # Pricing parameters
    with st.expander("Pricing Parameters", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            route_base = st.number_input("Base Fare (SEK)", value=3.5, key="route_base")
            route_km_rate = st.number_input("Per Km Rate (SEK)", value=1.5, key="route_km")
        
        with col2:
            route_min_rate = st.number_input("Per Minute Rate (SEK)", value=0.3, key="route_min")
            route_duration = st.number_input("Est. Duration (min)", value=180, key="route_dur")
    
    st.markdown("---")
    
    # Initialize session state for route results
    if 'route_result' not in st.session_state:
        st.session_state.route_result = None
    
    if st.button("Calculate Route & Price", type="primary", key="route_predict"):
        try:
            with st.spinner(f"Geocoding {from_location} and {to_location}..."):
                # Geocode locations
                from_loc = geolocator.geocode(from_location)
                to_loc = geolocator.geocode(to_location)
            
            if from_loc and to_loc:
                # Calculate distance
                from_coords = (from_loc.latitude, from_loc.longitude)
                to_coords = (to_loc.latitude, to_loc.longitude)
                distance_km = geodesic(from_coords, to_coords).kilometers
                
                # Create map
                mid_lat = (from_loc.latitude + to_loc.latitude) / 2
                mid_lon = (from_loc.longitude + to_loc.longitude) / 2
                
                m = folium.Map(
                    location=[mid_lat, mid_lon],
                    zoom_start=6
                )
                
                # Add markers
                folium.Marker(
                    from_coords,
                    popup=f"From: {from_location}",
                    tooltip="Start",
                    icon=folium.Icon(color='green', icon='play')
                ).add_to(m)
                
                folium.Marker(
                    to_coords,
                    popup=f"To: {to_location}",
                    tooltip="Destination",
                    icon=folium.Icon(color='red', icon='stop')
                ).add_to(m)
                
                folium.PolyLine(
                    [from_coords, to_coords],
                    color='blue',
                    weight=3,
                    opacity=0.7,
                    popup=f"Distance: {distance_km:.2f} km"
                ).add_to(m)
                
                # Make prediction with calculated distance
                trip_data = {
                    "Trip_Distance_km": float(distance_km),
                    "Time_of_Day": route_time,
                    "Day_of_Week": route_day,
                    "Passenger_Count": float(route_passengers),
                    "Traffic_Conditions": route_traffic,
                    "Weather": route_weather,
                    "Base_Fare": float(route_base),
                    "Per_Km_Rate": float(route_km_rate),
                    "Per_Minute_Rate": float(route_min_rate),
                    "Trip_Duration_Minutes": float(route_duration)
                }
                
                with st.spinner("Predicting price..."):
                    response = requests.post(API_URL, json=trip_data)
                
                if response.status_code == 200:
                    result = response.json()
                    predicted_price = result["predicted_price"]
                    
                    # Save to session state
                    st.session_state.route_result = {
                        'success': True,
                        'from_location': from_location,
                        'to_location': to_location,
                        'distance_km': distance_km,
                        'predicted_price': predicted_price,
                        'currency': result['currency'],
                        'map': m,
                        'route_time': route_time,
                        'route_day': route_day,
                        'route_traffic': route_traffic,
                        'route_weather': route_weather,
                        'route_duration': route_duration
                    }
                else:
                    st.session_state.route_result = {
                        'success': False,
                        'error': f"Prediction error: {response.status_code}"
                    }
            
            else:
                error_msg = []
                if not from_loc:
                    error_msg.append(f"Could not find location: {from_location}")
                if not to_loc:
                    error_msg.append(f"Could not find location: {to_location}")
                
                st.session_state.route_result = {
                    'success': False,
                    'error': ' | '.join(error_msg)
                }
        
        except Exception as e:
            st.session_state.route_result = {
                'success': False,
                'error': str(e)
            }
    
    # Display results from session state
    if st.session_state.route_result is not None:
        result = st.session_state.route_result
        
        if result['success']:
            st.success(f"Found locations! Distance: {result['distance_km']:.2f} km")
            
            # Display map
            st.markdown("### 🗺️ Route Map")
            st_folium(result['map'], width=700, height=500)
            
            # Display result
            st.markdown("### Estimated Trip Price")
            st.markdown(f"# {result['predicted_price']:.2f} {result['currency']}")
            
            st.info(f"""
            **Route Summary:**
            - From: {result['from_location']}
            - To: {result['to_location']}
            - Distance: {result['distance_km']:.2f} km (calculated from route)
            - Duration: {result['route_duration']} minutes
            - Time: {result['route_time']}, {result['route_day']}
            - Traffic: {result['route_traffic']}, Weather: {result['route_weather']}
            """)
        else:
            st.error(f"❌ {result['error']}")

# Footer
st.markdown("---")
st.markdown("*Powered by Gradient Boosting ML Model (R² = 0.9722)")