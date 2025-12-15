"""
Weather App - Streamlit Version
Gets current temperature for any location using Open-Meteo API (free, no API key required)
Supports multiple weather models: ECMWF, GFS, ICON
"""

import streamlit as st
import requests
from datetime import datetime, timezone, timedelta
import streamlit.components.v1 as components
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import urllib3

# Disable SSL warnings when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables from .env file
load_dotenv()

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from groq import Groq
except Exception:
    Groq = None

# Page configuration
st.set_page_config(
    page_title="Weather App",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants: US states
US_STATES = {
    'alabama': 'al', 'alaska': 'ak', 'arizona': 'az', 'arkansas': 'ar', 'california': 'ca',
    'colorado': 'co', 'connecticut': 'ct', 'delaware': 'de', 'florida': 'fl', 'georgia': 'ga',
    'hawaii': 'hi', 'idaho': 'id', 'illinois': 'il', 'indiana': 'in', 'iowa': 'ia',
    'kansas': 'ks', 'kentucky': 'ky', 'louisiana': 'la', 'maine': 'me', 'maryland': 'md',
    'massachusetts': 'ma', 'michigan': 'mi', 'minnesota': 'mn', 'mississippi': 'ms', 'missouri': 'mo',
    'montana': 'mt', 'nebraska': 'ne', 'nevada': 'nv', 'new hampshire': 'nh', 'new jersey': 'nj',
    'new mexico': 'nm', 'new york': 'ny', 'north carolina': 'nc', 'north dakota': 'nd', 'ohio': 'oh',
    'oklahoma': 'ok', 'oregon': 'or', 'pennsylvania': 'pa', 'rhode island': 'ri', 'south carolina': 'sc',
    'south dakota': 'sd', 'tennessee': 'tn', 'texas': 'tx', 'utah': 'ut', 'vermont': 'vt',
    'virginia': 'va', 'washington': 'wa', 'west virginia': 'wv', 'wisconsin': 'wi', 'wyoming': 'wy'
}
ABBREV_TO_STATE = {v: k for k, v in US_STATES.items()}

# Custom CSS - Dark Mode (background will be set dynamically based on temperature)
st.markdown("""
<style>
    .weather-card {
        background: rgba(30, 30, 45, 0.95);
        border-radius: 30px;
        padding: 40px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        animation: slideIn 0.5s ease-out;
        border: 1px solid rgba(100, 100, 150, 0.2);
    }
    .weather-icon {
        text-align: center;
        font-size: 100px;
        animation: float 3s ease-in-out infinite;
        filter: drop-shadow(0 0 20px rgba(255, 255, 255, 0.3));
        margin: 10px 0;
    }
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-15px); }
    }
    .temperature {
        text-align: center;
        font-size: 64px;
        font-weight: bold;
        color: #00d4ff;
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        margin: 5px 0;
    }
    .detail-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 12px 16px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    }
    .coordinates {
        text-align: center;
        color: #aaa;
        font-size: 12px;
        padding-top: 20px;
        border-top: 2px solid #444;
    }
    h1, h2, h3 {
        color: #e0e0e0;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.5);
        transform: translateY(-2px);
    }
    /* Sidebar Dark Mode */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p {
        color: #e0e0e0 !important;
    }
    /* Input fields dark mode */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stTextInput input::placeholder {
        color: rgba(255, 255, 255, 0.5);
    }
    /* Radio buttons dark mode */
    .stRadio > div {
        color: white;
    }
    /* Info boxes dark mode */
    .stAlert {
        background-color: rgba(30, 30, 45, 0.8);
        color: #e0e0e0;
        border: 1px solid rgba(100, 100, 150, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'unit_temp' not in st.session_state:
    st.session_state.unit_temp = 'F'
if 'unit_wind' not in st.session_state:
    st.session_state.unit_wind = 'mph'
if 'last_location' not in st.session_state:
    st.session_state.last_location = None
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'travel_destination' not in st.session_state:
    st.session_state.travel_destination = None

def get_location_by_name(location_name):
    """Get coordinates for a location name using geocoding API.
    
    Intelligently ranks results to prioritize exact matches.
    For example, "Niles, Ohio" will rank Niles, OH above Niles, IL.
    """
    print(f"===== FUNCTION CALLED: get_location_by_name('{location_name}') =====", flush=True)
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            'name': location_name,
            'count': 50,  # Request more results to improve matching
            'language': 'en',
            'format': 'json'
        }
        
        print(f"DEBUG: About to call API...", flush=True)
        response = requests.get(url, params=params, timeout=10, verify=False)
        data = response.json()
        print(f"DEBUG: API returned data: {bool(data.get('results'))}", flush=True)
        
        if 'results' in data and len(data['results']) > 0:
            print(f"DEBUG: Found {len(data['results'])} results", flush=True)
            results = data['results']
            
            # Parse the user's input to extract city and state/region
            parsed_input = location_name.lower().strip()
            parts = [p.strip() for p in parsed_input.split(',')]
            print(f"PARSE DEBUG: Input='{location_name}', Parts={parts}, Len={len(parts)}", flush=True)
            
            # Determine desired city/state from input (supports abbreviations)
            search_city = parts[0] if len(parts) >= 1 else parsed_input
            search_region = parts[1] if len(parts) >= 2 else ''

            # US State name to abbreviation mapping
            us_states = {
                    'alabama': 'al', 'alaska': 'ak', 'arizona': 'az', 'arkansas': 'ar', 'california': 'ca',
                    'colorado': 'co', 'connecticut': 'ct', 'delaware': 'de', 'florida': 'fl', 'georgia': 'ga',
                    'hawaii': 'hi', 'idaho': 'id', 'illinois': 'il', 'indiana': 'in', 'iowa': 'ia',
                    'kansas': 'ks', 'kentucky': 'ky', 'louisiana': 'la', 'maine': 'me', 'maryland': 'md',
                    'massachusetts': 'ma', 'michigan': 'mi', 'minnesota': 'mn', 'mississippi': 'ms', 'missouri': 'mo',
                    'montana': 'mt', 'nebraska': 'ne', 'nevada': 'nv', 'new hampshire': 'nh', 'new jersey': 'nj',
                    'new mexico': 'nm', 'new york': 'ny', 'north carolina': 'nc', 'north dakota': 'nd', 'ohio': 'oh',
                    'oklahoma': 'ok', 'oregon': 'or', 'pennsylvania': 'pa', 'rhode island': 'ri', 'south carolina': 'sc',
                    'south dakota': 'sd', 'tennessee': 'tn', 'texas': 'tx', 'utah': 'ut', 'vermont': 'vt',
                    'virginia': 'va', 'washington': 'wa', 'west virginia': 'wv', 'wisconsin': 'wi', 'wyoming': 'wy'
                }
            
            # Create reverse mapping (abbreviation -> state name)
            abbrev_to_state = {v: k for k, v in us_states.items()}
            
            # Score each result based on how well it matches
            def score_result(result):
                    score = 0
                    result_city = result.get('name', '').lower()
                    result_region = result.get('admin1', '').lower()
                    result_country = result.get('country', '').lower()
                    
                    # DEBUG: Print what we're comparing
                    print(f"DEBUG: City={result_city}, Region={result_region}, Country={result_country}, Search={search_region}", flush=True)
                    
                    # Exact city name match
                    if result_city == search_city:
                        score += 100
                    elif search_city in result_city:
                        score += 50
                    
                    # State/Region match (CRITICAL) - normalize desired state first
                    state_match = False
                    desired_state = search_region
                    if desired_state in abbrev_to_state:
                        desired_state = abbrev_to_state[desired_state]
                    normalized_result = result_region
                    if normalized_result in abbrev_to_state:
                        normalized_result = abbrev_to_state[normalized_result]
                    if desired_state and normalized_result:
                        if desired_state == normalized_result:
                            score += 400  # even stronger priority
                            state_match = True
                        else:
                            # penalize wrong US state when user specified a US state
                            is_us = 'united states' in result_country or result_country in ['us', 'usa', 'united states of america']
                            if is_us:
                                score -= 150
                    
                    # Partial region match (fallback)
                    if not state_match and desired_state and (desired_state in result_region or result_region in desired_state):
                        score += 40
                    
                    # Check if search term matches country
                    if search_region == result_country:
                        score += 70
                    elif search_region in result_country:
                        score += 35
                    
                    # Country preference
                    is_us = 'united states' in result_country or result_country in ['us', 'usa', 'united states of america']
                    if is_us:
                        score += 50
                    
                    return score
                
            # Sort results by score (highest first) ALWAYS
            results_with_scores = [(score_result(r), r) for r in results]
            results_with_scores.sort(key=lambda x: x[0], reverse=True)
            
            # (Debug removed) Return sorted results
            # Return top 5 sorted results
            sorted_results = [r for score, r in results_with_scores]
            return sorted_results[:5]
        else:
            # Fallbacks when API returns no data
            parsed_input = location_name.lower().strip()
            parts = [p.strip() for p in parsed_input.split(',')]
            # If input was "City, State" try city-only with larger count and then filter admin1 by state
            if len(parts) >= 2:
                city_only = parts[0]
                state_term = parts[1]
                # Normalize state abbreviation
                abbrev_to_state = ABBREV_TO_STATE
                desired_state = state_term
                if desired_state.lower() in abbrev_to_state:
                    desired_state = abbrev_to_state[desired_state.lower()]
                # Retry with city-only
                params['name'] = city_only
                params['count'] = 50
                response = requests.get(url, params=params, timeout=10, verify=False)
                data = response.json()
                if 'results' in data and len(data['results']) > 0:
                    # Filter to US and desired state first
                    filtered = []
                    for r in data['results']:
                        admin1 = (r.get('admin1') or '').lower()
                        country = (r.get('country') or '').lower()
                        norm_admin1 = abbrev_to_state.get(admin1, admin1)
                        if desired_state and country.startswith('united') and norm_admin1 == desired_state.lower():
                            filtered.append(r)
                    if filtered:
                        return filtered[:5]
                    # Otherwise return top few city-only results
                    return data['results'][:5]
            # Last resort: return None
            return None
    except Exception as e:
        print(f"EXCEPTION in get_location_by_name: {e}", flush=True)
        st.error(f"Error searching for location: {e}")
        return None

def get_current_location():
    """Get current location using browser's geolocation API.
    
    This uses the HTML5 Geolocation API which accesses:
    - GPS (if available)
    - WiFi positioning
    - Cell tower triangulation
    
    Much more accurate than IP-based geolocation.
    """
    # Use Streamlit's component to execute JavaScript geolocation
    geolocation_html = """
    <script>
    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    // Send coordinates back to Streamlit
                    const data = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    };
                    
                    // Store in session storage for Streamlit to read
                    sessionStorage.setItem('geolocation', JSON.stringify(data));
                    
                    // Display success message
                    document.getElementById('status').innerHTML = 
                        '✅ Location detected! Latitude: ' + position.coords.latitude.toFixed(4) + 
                        ', Longitude: ' + position.coords.longitude.toFixed(4) +
                        '<br><small>Accuracy: ± ' + Math.round(position.coords.accuracy) + ' meters</small>' +
                        '<br><br><strong>Click "Detect Location" button again to load weather.</strong>';
                    document.getElementById('status').style.color = '#00d4ff';
                },
                function(error) {
                    let errorMsg = '';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            errorMsg = '❌ Permission denied. Please allow location access in your browser settings.';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMsg = '❌ Location information unavailable.';
                            break;
                        case error.TIMEOUT:
                            errorMsg = '❌ Location request timed out.';
                            break;
                        default:
                            errorMsg = '❌ Unknown error occurred.';
                    }
                    document.getElementById('status').innerHTML = errorMsg;
                    document.getElementById('status').style.color = '#ff4444';
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        } else {
            document.getElementById('status').innerHTML = '❌ Geolocation not supported by this browser.';
            document.getElementById('status').style.color = '#ff4444';
        }
    }
    
    // Auto-run on load
    getLocation();
    </script>
    
    <div id="status" style="padding: 15px; background: rgba(30,30,45,0.9); border-radius: 10px; border: 1px solid rgba(100,100,150,0.3); color: #aaa; text-align: center;">
        🔍 Requesting location permission...<br>
        <small>Please allow location access when prompted by your browser.</small>
    </div>
    """
    
    # Display the geolocation component
    components.html(geolocation_html, height=150)
    
    # Try to read from session storage (if coordinates were stored)
    # Note: We need to use a different approach since we can't directly read sessionStorage
    # Instead, we'll use IP-based fallback and inform users about browser geolocation
    try:
        st.info("💡 **Tip:** For best accuracy, allow location access when prompted by your browser. If you see the success message above, click 'Detect Location' again to fetch weather.")
        
        # Fallback to IP-based geolocation
        response = requests.get('https://ipapi.co/json/', timeout=5, verify=False)
        data = response.json()
        
        if data.get('latitude') and data.get('longitude'):
            st.warning(f"📍 Using IP-based location (approximate): {data.get('city')}, {data.get('region')}")
            return {
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'city': data.get('city', 'Unknown'),
                'region': data.get('region', 'Unknown'),
                'country': data.get('country_name', 'Unknown')
            }
        return None
    except Exception as e:
        st.error(f"Error getting location: {e}")
        st.info("💡 Try searching by city name instead, or check if your firewall is blocking location services.")
        return None

def get_weather_alerts(latitude, longitude):
    """Get active weather alerts from National Weather Service API.
    
    Returns alerts for the given location including:
    - Severe weather warnings
    - Watches
    - Special weather statements
    - Advisories
    
    Note: NWS API only covers United States territories
    """
    try:
        # NWS API endpoint - point-specific alerts
        url = f"https://api.weather.gov/alerts/active"
        params = {
            'point': f"{latitude},{longitude}",
            'status': 'actual',  # Only actual alerts, not tests/exercises
            'message_type': 'alert,update'  # Alert messages and updates
        }
        
        headers = {
            'User-Agent': '(Weather App, github.com/jxwnpvs2mv-netizen/Weather-App)',
            'Accept': 'application/geo+json'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
        
        # NWS sometimes returns 500 errors, handle gracefully
        if response.status_code != 200:
            return None
            
        data = response.json()
        
        if 'features' in data and len(data['features']) > 0:
            alerts = []
            for feature in data['features']:
                props = feature.get('properties', {})
                
                # Extract alert details
                alert = {
                    'event': props.get('event', 'Unknown Event'),
                    'headline': props.get('headline', ''),
                    'description': props.get('description', ''),
                    'instruction': props.get('instruction', ''),
                    'severity': props.get('severity', 'Unknown'),  # Extreme, Severe, Moderate, Minor
                    'urgency': props.get('urgency', 'Unknown'),    # Immediate, Expected, Future
                    'certainty': props.get('certainty', 'Unknown'), # Observed, Likely, Possible
                    'onset': props.get('onset', ''),
                    'expires': props.get('expires', ''),
                    'sender_name': props.get('senderName', 'NWS'),
                    'areas': props.get('areaDesc', ''),
                    'response': props.get('response', 'Monitor'),
                }
                
                alerts.append(alert)
            
            return alerts
        
        return None
        
    except Exception as e:
        # Fail silently for non-US locations or API issues
        return None

def get_weather(latitude, longitude, model='best_match'):
    """Get current weather data from Open-Meteo API with hourly forecast.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        model: Weather model to use. Options:
            - 'best_match' (default): Automatically selects best model for region
              Open-Meteo intelligently picks from: ICON (Europe), GFS (N.America), 
              ECMWF (global), or best regional model available
            - 'ecmwf_ifs025': ECMWF IFS 0.25° (European model, global coverage)
            - 'gfs_global': GFS Global (NOAA model, best for North America)
            - 'icon_global': ICON Global (German Weather Service, high resolution)
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code',
            'hourly': 'temperature_2m,precipitation_probability,precipitation,weather_code',
            'daily': 'sunrise,sunset,daylight_duration,sunshine_duration,uv_index_max',
            'temperature_unit': 'fahrenheit',
            'wind_speed_unit': 'mph',
            'forecast_days': 3,  # 3 days = 72 hours of hourly forecast
            'timezone': 'auto'
        }
        
        # Add model parameter if not using best_match
        if model != 'best_match':
            params['models'] = model
        
        response = requests.get(url, params=params, timeout=10, verify=False)
        response.raise_for_status()
        data = response.json()
        
        # Add model info to response for display
        data['model_used'] = model
        
        return data
    except Exception as e:
        st.error(f"Error getting weather: {e}")
        return None

def check_precipitation_soon(weather_data):
    """Check if precipitation is expected soon and return details including type."""
    try:
        if not weather_data or 'hourly' not in weather_data:
            return None
        
        hourly = weather_data['hourly']
        times = hourly.get('time', [])
        precip_prob = hourly.get('precipitation_probability', [])
        precipitation = hourly.get('precipitation', [])
        rain = hourly.get('rain', [])
        showers = hourly.get('showers', [])
        snowfall = hourly.get('snowfall', [])
        weather_codes = hourly.get('weather_code', [])
        
        current_time = datetime.now()
        
        # Check next 12 hours for precipitation
        for i, time_str in enumerate(times[:12]):
            if i >= len(precip_prob):
                continue
                
            prob = precip_prob[i] if i < len(precip_prob) else 0
            precip = precipitation[i] if i < len(precipitation) else 0
            rain_amt = rain[i] if i < len(rain) else 0
            shower_amt = showers[i] if i < len(showers) else 0
            snow_amt = snowfall[i] if i < len(snowfall) else 0
            w_code = weather_codes[i] if i < len(weather_codes) else 0
            
            # If moderate to high probability (>30%) or actual precipitation expected
            if (prob and prob > 30) or precip > 0.1:
                # Calculate minutes until this time
                try:
                    # Handle different time formats
                    if 'T' in time_str:
                        forecast_time = datetime.fromisoformat(time_str.replace('Z', ''))
                    else:
                        forecast_time = datetime.fromisoformat(time_str)
                    
                    # Calculate time difference
                    current_time = datetime.now()
                    time_diff = (forecast_time - current_time).total_seconds()
                    minutes = int(time_diff / 60)
                    
                    if minutes > 0 and minutes <= 720:  # Within next 12 hours
                        # Determine precipitation type
                        precip_type = 'Rain'
                        emoji = '🌧️'
                        color_start = '#ff6b6b'
                        color_end = '#ee5a6f'
                        
                        # Check for snow
                        if snow_amt > 0 or w_code in [71, 73, 75, 77, 85, 86]:
                            precip_type = 'Snow'
                            emoji = '❄️'
                            color_start = '#64b5f6'
                            color_end = '#42a5f5'
                        # Check for freezing rain/sleet
                        elif w_code in [56, 57, 66, 67]:
                            precip_type = 'Freezing Rain'
                            emoji = '🧊'
                            color_start = '#9575cd'
                            color_end = '#7e57c2'
                        # Check for thunderstorm
                        elif w_code in [95, 96, 99]:
                            precip_type = 'Thunderstorm'
                            emoji = '⛈️'
                            color_start = '#ffa726'
                            color_end = '#ff9800'
                        # Check for showers vs rain
                        elif shower_amt > rain_amt:
                            precip_type = 'Showers'
                            emoji = '🌦️'
                        
                        return {
                            'minutes': minutes,
                            'probability': prob,
                            'amount': precip if precip else 0,
                            'type': precip_type,
                            'emoji': emoji,
                            'color_start': color_start,
                            'color_end': color_end
                        }
                except Exception as time_err:
                    continue  # Skip this time slot if parsing fails
        
        return None
    except Exception as e:
        st.error(f"Error checking precipitation: {e}")
        return None

def get_weather_description(weather_code):
    """Convert weather code to description."""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return weather_codes.get(weather_code, "Unknown")

def get_weather_emoji(conditions, time_str=None):
    """Get emoji based on weather conditions and time of day.
    
    Args:
        conditions: Weather condition string
        time_str: Optional ISO format time string (e.g., "2024-12-12T22:00")
                  If provided and it's nighttime, uses night-appropriate emojis
    """
    # Determine if it's nighttime (6 PM to 6 AM)
    is_night = False
    if time_str:
        try:
            from datetime import datetime
            if 'T' in time_str:
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                hour = dt.hour
                is_night = hour >= 18 or hour < 6  # 6 PM to 6 AM
        except:
            pass
    
    # Night-specific emojis
    if is_night:
        night_emoji = {
            "Clear sky": "🌙",
            "Mainly clear": "🌙",
            "Partly cloudy": "☁️",
            "Overcast": "☁️",
            "Foggy": "🌫️",
            "Depositing rime fog": "🌫️",
            "Light drizzle": "🌧️",
            "Moderate drizzle": "🌧️",
            "Dense drizzle": "🌧️",
            "Slight rain": "🌧️",
            "Moderate rain": "🌧️",
            "Heavy rain": "⛈️",
            "Slight snow": "🌨️",
            "Moderate snow": "❄️",
            "Heavy snow": "❄️",
            "Snow grains": "❄️",
            "Slight rain showers": "🌧️",
            "Moderate rain showers": "🌧️",
            "Violent rain showers": "⛈️",
            "Slight snow showers": "🌨️",
            "Heavy snow showers": "❄️",
            "Thunderstorm": "⛈️",
            "Thunderstorm with slight hail": "⛈️",
            "Thunderstorm with heavy hail": "⛈️"
        }
        return night_emoji.get(conditions, "🌙")
    
    # Daytime emojis
    weather_emoji = {
        "Clear sky": "☀️",
        "Mainly clear": "🌤️",
        "Partly cloudy": "⛅",
        "Overcast": "☁️",
        "Foggy": "🌫️",
        "Depositing rime fog": "🌫️",
        "Light drizzle": "🌦️",
        "Moderate drizzle": "🌧️",
        "Dense drizzle": "🌧️",
        "Slight rain": "🌧️",
        "Moderate rain": "🌧️",
        "Heavy rain": "⛈️",
        "Slight snow": "🌨️",
        "Moderate snow": "❄️",
        "Heavy snow": "❄️",
        "Snow grains": "❄️",
        "Slight rain showers": "🌦️",
        "Moderate rain showers": "🌧️",
        "Violent rain showers": "⛈️",
        "Slight snow showers": "🌨️",
        "Heavy snow showers": "❄️",
        "Thunderstorm": "⛈️",
        "Thunderstorm with slight hail": "⛈️",
        "Thunderstorm with heavy hail": "⛈️"
    }
    return weather_emoji.get(conditions, "🌤️")

def get_visual_crossing_outlook(latitude, longitude):
    """Get daily weather description from Visual Crossing API (free tier).
    
    Visual Crossing free tier includes:
    - 1000 records/day free
    - Daily descriptions in natural language
    - No credit card required
    
    Returns the 'description' field for today's weather or None if unavailable.
    """
    try:
        # Visual Crossing API endpoint (free tier)
        # Sign up at: https://www.visualcrossing.com/sign-up
        # Free tier: 1000 records/day
        
        # Get API key from session state first (user's custom key in sidebar)
        api_key = st.session_state.get('visual_crossing_api_key', '')
        
        if not api_key:
            # Try environment variable (recommended for security)
            api_key = os.environ.get('VISUAL_CROSSING_API_KEY', '')
        
        if not api_key:
            # No API key configured - Visual Crossing features will be disabled
            return None
        
        # Build API URL - request only today's data to minimize record usage
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{latitude},{longitude}/today"
        
        params = {
            'key': api_key,
            'unitGroup': 'us',  # Fahrenheit, mph, etc.
            'include': 'days',  # Only include daily data
            'elements': 'datetime,description',  # Only get the description
            'contentType': 'json'
        }
        
        response = requests.get(url, params=params, timeout=10, verify=False)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Get description from today's data
            if 'days' in data and len(data['days']) > 0:
                description = data['days'][0].get('description')
                if description:
                    return description
        elif response.status_code == 401:
            # Invalid API key - show warning once
            if 'vc_api_key_warning_shown' not in st.session_state:
                st.warning("⚠️ Visual Crossing API key is invalid. Using generated outlook instead.")
                st.session_state.vc_api_key_warning_shown = True
        
        return None
        
    except Exception as e:
        # Silently fail and use fallback
        return None

def visual_crossing_icon_to_wmo_code(icon):
    """Convert Visual Crossing icon codes to WMO weather codes for consistency."""
    icon_mapping = {
        'clear-day': 0,
        'clear-night': 0,
        'partly-cloudy-day': 2,
        'partly-cloudy-night': 2,
        'cloudy': 3,
        'fog': 45,
        'wind': 1,
        'rain': 61,
        'snow': 71,
        'sleet': 66,
        'hail': 96,
        'thunderstorm': 95,
        'tornado': 95
    }
    return icon_mapping.get(icon, 1)  # Default to mainly clear

def get_visual_crossing_forecast(latitude, longitude):
    """Get complete weather forecast from Visual Crossing API including hourly data.
    
    Returns weather data in a format compatible with display_weather() function.
    """
    try:
        # Get API key from session state first (user's custom key in sidebar)
        api_key = st.session_state.get('visual_crossing_api_key', '')
        
        if not api_key:
            # Try environment variable (recommended for security)
            api_key = os.environ.get('VISUAL_CROSSING_API_KEY', '')
        
        if not api_key:
            # No API key configured - return None to use Open-Meteo instead
            return None
        
        # Build API URL - request 3 days of data with hourly details
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{latitude},{longitude}"
        
        params = {
            'key': api_key,
            'unitGroup': 'us',  # Fahrenheit, mph, etc.
            'include': 'hours,current',  # Include hourly and current conditions
            'elements': 'datetime,temp,humidity,precip,precipprob,windspeed,conditions,icon',
            'contentType': 'json'
        }
        
        response = requests.get(url, params=params, timeout=10, verify=False)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Convert Visual Crossing format to Open-Meteo compatible format
            converted_data = {
                'current': {},
                'hourly': {
                    'time': [],
                    'temperature_2m': [],
                    'precipitation_probability': [],
                    'precipitation': [],
                    'weather_code': []
                }
            }
            
            # Get current conditions
            if 'currentConditions' in data:
                current = data['currentConditions']
                icon = current.get('icon', 'clear-day')
                converted_data['current'] = {
                    'temperature_2m': current.get('temp', 0),
                    'relative_humidity_2m': current.get('humidity', 0),
                    'wind_speed_10m': current.get('windspeed', 0),
                    'weather_code': visual_crossing_icon_to_wmo_code(icon)
                }
            
            # Get hourly data from all days
            if 'days' in data:
                for day in data['days'][:3]:  # Get 3 days like other models
                    if 'hours' in day:
                        for hour in day['hours']:
                            # Combine date and time
                            date = day.get('datetime', '')
                            time = hour.get('datetime', '')
                            datetime_str = f"{date}T{time}"
                            
                            # Get weather code from icon
                            icon = hour.get('icon', 'clear-day')
                            weather_code = visual_crossing_icon_to_wmo_code(icon)
                            
                            converted_data['hourly']['time'].append(datetime_str)
                            converted_data['hourly']['temperature_2m'].append(hour.get('temp', 0))
                            converted_data['hourly']['precipitation_probability'].append(hour.get('precipprob', 0))
                            # Convert precipitation from inches to mm for consistency (1 inch = 25.4 mm)
                            precip_inches = hour.get('precip', 0) or 0
                            precip_mm = precip_inches * 25.4
                            converted_data['hourly']['precipitation'].append(precip_mm)
                            converted_data['hourly']['weather_code'].append(weather_code)
            
            # Add timezone info (required by display functions)
            converted_data['timezone'] = data.get('timezone', 'America/New_York')
            
            return converted_data
        else:
            return None
        
    except Exception as e:
        return None

def convert_temp(temp_f, to_celsius=False):
    """Convert temperature between F and C."""
    if to_celsius:
        return (temp_f - 32) * 5/9
    return temp_f

def convert_wind(wind_mph, to_kmh=False):
    """Convert wind speed between mph and km/h."""
    if to_kmh:
        return wind_mph * 1.60934
    return wind_mph

def get_temp_gradient(temp_f):
    """Generate background gradient colors based on temperature in Fahrenheit.
    
    Returns a tuple of (color1, color2, color3) for gradient.
    """
    # Temperature ranges and their colors
    if temp_f <= 32:  # Freezing - Ice Blue
        return ('#0a1128', '#1c2541', '#0d1b2a')
    elif temp_f <= 50:  # Cold - Cool Blue
        return ('#0f0c29', '#302b63', '#24243e')
    elif temp_f <= 68:  # Cool - Mild Blue-Purple
        return ('#141e30', '#243b55', '#1a2332')
    elif temp_f <= 75:  # Pleasant - Blue-Green
        return ('#134e5e', '#71b280', '#2c5f6f')
    elif temp_f <= 85:  # Warm - Orange-Yellow
        return ('#f46b45', '#eea849', '#d35400')
    elif temp_f <= 95:  # Hot - Red-Orange
        return ('#eb3349', '#f45c43', '#c0392b')
    else:  # Extreme Heat - Deep Red
        return ('#7b2d26', '#c94b4b', '#8b1e3f')

def apply_temp_background(temp_f):
    """Apply temperature-based background styling and adjust text colors for readability."""
    color1, color2, color3 = get_temp_gradient(temp_f)
    
    # Adjust text colors for warm/orange backgrounds (76-95°F) for better contrast
    if 76 <= temp_f <= 95:
        # Use dark colors for better visibility on warm backgrounds
        header_color = "#1a1a2e"  # Dark blue-black
        temp_color = "#0d47a1"  # Deep blue
        conditions_color = "#37474f"  # Dark gray-blue
        text_color = "#263238"  # Very dark gray
        detail_card_bg = "linear-gradient(135deg, #1565c0 0%, #0d47a1 100%)"  # Deep blue gradient
    else:
        # Default light colors for cool backgrounds
        header_color = "#e0e0e0"
        temp_color = "#00d4ff"
        conditions_color = "#bbb"
        text_color = "#aaa"
        detail_card_bg = "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)"
    
    st.markdown(f"""
    <style>
        .main {{
            background: linear-gradient(135deg, {color1} 0%, {color2} 50%, {color3} 100%);
        }}
        .stApp {{
            background: linear-gradient(135deg, {color1} 0%, {color2} 50%, {color3} 100%);
        }}
        h1, h2, h3 {{
            color: {header_color} !important;
        }}
        .temperature {{
            color: {temp_color} !important;
            text-shadow: 0 0 20px rgba(13, 71, 161, 0.5);
        }}
        .coordinates {{
            color: {text_color} !important;
        }}
        .detail-card {{
            background: {detail_card_bg} !important;
        }}
        /* Adjust description text color */
        h3[style*="text-align: center"][style*="color: #bbb"] {{
            color: {conditions_color} !important;
        }}
        /* Adjust subtitle and location text color */
        p[style*="color: #aaa"], p[style*="color: {text_color}"] {{
            color: {text_color} !important;
        }}
    </style>
    """, unsafe_allow_html=True)

def display_sun_times(weather_data, temperature_f=None):
    """Display sunrise, sunset, and twilight information from daily weather data.
    
    Args:
        weather_data: Weather data dict containing 'daily' with sun times
        temperature_f: Current temperature in Fahrenheit (to adjust box color)
    """
    try:
        daily = weather_data.get('daily', {})
        if not daily:
            return
        
        # Get today's data (first entry)
        sunrise = daily.get('sunrise', [None])[0]
        sunset = daily.get('sunset', [None])[0]
        daylight_duration = daily.get('daylight_duration', [None])[0]
        sunshine_duration = daily.get('sunshine_duration', [None])[0]
        uv_index = daily.get('uv_index_max', [None])[0]
        
        if not sunrise or not sunset:
            return
        
        from datetime import datetime, timedelta
        
        # Parse sunrise and sunset times
        sunrise_dt = datetime.fromisoformat(sunrise.replace('Z', '+00:00'))
        sunset_dt = datetime.fromisoformat(sunset.replace('Z', '+00:00'))
        
        # Format times
        sunrise_time = sunrise_dt.strftime('%I:%M %p').lstrip('0')
        sunset_time = sunset_dt.strftime('%I:%M %p').lstrip('0')
        
        # Estimate civil twilight (approximately 25-30 minutes before sunrise / after sunset)
        # Civil twilight is when the sun is between 0° and 6° below the horizon
        first_light_dt = sunrise_dt - timedelta(minutes=28)
        last_light_dt = sunset_dt + timedelta(minutes=28)
        
        first_light = first_light_dt.strftime('%I:%M %p').lstrip('0')
        last_light = last_light_dt.strftime('%I:%M %p').lstrip('0')
        
        # Convert daylight duration from seconds to hours and minutes
        if daylight_duration:
            hours = int(daylight_duration // 3600)
            minutes = int((daylight_duration % 3600) // 60)
            daylight_str = f"{hours}h {minutes}m"
        else:
            daylight_str = "N/A"
        
        # Sunshine duration (actual sunshine vs possible daylight)
        if sunshine_duration:
            sun_hours = int(sunshine_duration // 3600)
            sun_minutes = int((sunshine_duration % 3600) // 60)
            sunshine_str = f"{sun_hours}h {sun_minutes}m"
            sunshine_percent = int((sunshine_duration / daylight_duration * 100)) if daylight_duration else 0
        else:
            sunshine_str = "N/A"
            sunshine_percent = 0
        
        # UV Index color coding
        if uv_index:
            if uv_index < 3:
                uv_color = "#2ecc71"  # Green - Low
                uv_level = "Low"
            elif uv_index < 6:
                uv_color = "#f39c12"  # Yellow - Moderate
                uv_level = "Moderate"
            elif uv_index < 8:
                uv_color = "#e67e22"  # Orange - High
                uv_level = "High"
            elif uv_index < 11:
                uv_color = "#e74c3c"  # Red - Very High
                uv_level = "Very High"
            else:
                uv_color = "#8e44ad"  # Purple - Extreme
                uv_level = "Extreme"
        else:
            uv_color = "#888"
            uv_level = "N/A"
        
        # Adjust box color based on temperature to avoid clash with background
        # When background is warm/orange (76-95°F), use dark contrasting colors
        if temperature_f is not None and 76 <= temperature_f <= 95:
            # Use dark blue/navy tones with high contrast for warm orange backgrounds
            box_gradient = "linear-gradient(135deg, rgba(13, 71, 161, 0.95) 0%, rgba(21, 101, 192, 0.95) 100%)"
            border_color = "rgba(13, 71, 161, 0.8)"
            title_color = "#ffffff"
            border_top_color = "rgba(255, 255, 255, 0.3)"
            
            # Dark backgrounds for individual time cards
            card_bg = "rgba(13, 71, 161, 0.6)"
            label_color = "#e3f2fd"  # Very light blue
            time_color = "#ffffff"  # White
            subtitle_color = "#bbdefb"  # Light blue
            
            # Bottom section colors
            stat_label_color = "#e3f2fd"
            stat_value_color = "#ffffff"
        else:
            # Default warm orange tones for cool backgrounds
            box_gradient = "linear-gradient(135deg, rgba(255, 183, 77, 0.15) 0%, rgba(255, 112, 67, 0.15) 100%)"
            border_color = "rgba(255, 183, 77, 0.3)"
            title_color = "#FFB74D"
            border_top_color = "rgba(255, 183, 77, 0.2)"
            
            # Light backgrounds for individual time cards
            card_bg = "rgba(255, 255, 255, 0.05)"
            label_color = "#aaa"
            time_color = "#FFB74D"
            subtitle_color = "#888"
            
            # Bottom section colors
            stat_label_color = "#aaa"
            stat_value_color = "#FFD54F"
        
        # Display sun times in an attractive card
        st.markdown(f"""<div style='background: {box_gradient}; border: 1px solid {border_color}; border-radius: 15px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
<div style='text-align: center; margin-bottom: 15px;'>
<span style='font-size: 24px; font-weight: 600; color: {title_color};'>☀️ Sun & Light Information</span>
</div>
<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;'>
<div style='background: {card_bg}; padding: 12px; border-radius: 10px; text-align: center;'>
<div style='font-size: 28px; margin-bottom: 5px;'>🌅</div>
<div style='font-size: 12px; color: {label_color}; text-transform: uppercase; letter-spacing: 1px;'>First Light</div>
<div style='font-size: 20px; font-weight: 600; color: {time_color}; margin-top: 5px;'>{first_light}</div>
<div style='font-size: 11px; color: {subtitle_color}; margin-top: 3px;'>Civil Twilight</div>
</div>
<div style='background: {card_bg}; padding: 12px; border-radius: 10px; text-align: center;'>
<div style='font-size: 28px; margin-bottom: 5px;'>🌄</div>
<div style='font-size: 12px; color: {label_color}; text-transform: uppercase; letter-spacing: 1px;'>Sunrise</div>
<div style='font-size: 20px; font-weight: 600; color: {time_color}; margin-top: 5px;'>{sunrise_time}</div>
<div style='font-size: 11px; color: {subtitle_color}; margin-top: 3px;'>Sun appears</div>
</div>
<div style='background: {card_bg}; padding: 12px; border-radius: 10px; text-align: center;'>
<div style='font-size: 28px; margin-bottom: 5px;'>🌇</div>
<div style='font-size: 12px; color: {label_color}; text-transform: uppercase; letter-spacing: 1px;'>Sunset</div>
<div style='font-size: 20px; font-weight: 600; color: {time_color}; margin-top: 5px;'>{sunset_time}</div>
<div style='font-size: 11px; color: {subtitle_color}; margin-top: 3px;'>Sun disappears</div>
</div>
<div style='background: {card_bg}; padding: 12px; border-radius: 10px; text-align: center;'>
<div style='font-size: 28px; margin-bottom: 5px;'>🌆</div>
<div style='font-size: 12px; color: {label_color}; text-transform: uppercase; letter-spacing: 1px;'>Last Light</div>
<div style='font-size: 20px; font-weight: 600; color: {time_color}; margin-top: 5px;'>{last_light}</div>
<div style='font-size: 11px; color: {subtitle_color}; margin-top: 3px;'>Civil Twilight</div>
</div>
</div>
<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-top: 15px; padding-top: 15px; border-top: 1px solid {border_top_color};'>
<div style='text-align: center;'>
<div style='font-size: 11px; color: {stat_label_color}; text-transform: uppercase;'>Daylight</div>
<div style='font-size: 16px; font-weight: 600; color: {stat_value_color}; margin-top: 3px;'>{daylight_str}</div>
</div>
<div style='text-align: center;'>
<div style='font-size: 11px; color: {stat_label_color}; text-transform: uppercase;'>Sunshine</div>
<div style='font-size: 16px; font-weight: 600; color: {stat_value_color}; margin-top: 3px;'>{sunshine_str}</div>
<div style='font-size: 10px; color: {subtitle_color};'>({sunshine_percent}% of day)</div>
</div>
<div style='text-align: center;'>
<div style='font-size: 11px; color: {stat_label_color}; text-transform: uppercase;'>UV Index</div>
<div style='font-size: 16px; font-weight: 600; color: {uv_color}; margin-top: 3px;'>{uv_index:.0f} - {uv_level}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
        
    except Exception as e:
        # Silently fail if sun data not available
        pass

# ===== AI Overview (OpenAI) =====
def build_hourly_summary(hourly: Dict[str, Any], start_idx: int, hours_to_show: int = 24) -> List[Dict[str, Any]]:
    """Extract a compact hourly slice for AI summarization (up to 24 hours)."""
    times = hourly.get('time', [])
    temps = hourly.get('temperature_2m', [])
    codes = hourly.get('weather_code', [])
    probs = hourly.get('precipitation_probability', [])
    precips = hourly.get('precipitation', [])
    end = min(len(times), start_idx + hours_to_show)
    summary = []
    for i in range(start_idx, end):
        hour = {
            'time': times[i],
            'temp_f': temps[i] if i < len(temps) else None,
            'wmo_code': codes[i] if i < len(codes) else None,
            'precip_prob': probs[i] if i < len(probs) else None,
            'precip_mm': precips[i] if i < len(precips) else None,
        }
        summary.append(hour)
    return summary

def get_openai_client():
    """Initialize OpenAI client using environment variable."""
    # Load API key from environment variable
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        return None
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception:
        return None

def generate_ai_overview(location: Dict[str, Any], hourly_slice: List[Dict[str, Any]], temp_unit='F', wind_unit='mph') -> Dict[str, Any]:
    """Use Groq AI (ultra-fast!) to produce a web-based, human-friendly weather overview from hourly forecast data.
    
    Returns:
        dict with 'text' (formatted response), 'raw_response' (JSON), 'prompt' (user prompt), 'system_prompt'
    """
    # Groq API configuration - load from session state first, then environment variable
    groq_api_key = st.session_state.get('groq_api_key', '')
    
    if not groq_api_key:
        groq_api_key = os.environ.get('GROQ_API_KEY', '')
    
    if not groq_api_key:
        return {"text": "⚠️ Groq API key not configured. Please set GROQ_API_KEY environment variable.", "raw_response": None, "prompt": None, "system_prompt": None}
    
    if not Groq:
        return {"text": "⚠️ Groq library not installed. Run: pip install groq", "raw_response": None, "prompt": None, "system_prompt": None}

    city = location.get('city', 'Unknown')
    region = location.get('region', '')
    country = location.get('country', '')
    
    # Get current date for context
    from datetime import datetime
    today = datetime.now().strftime('%B %d, %Y')

    # Build hourly data summary for the prompt (simplified - only next 24 hours)
    if not hourly_slice:
        return {"text": "AI overview unavailable: missing hourly data.", "raw_response": None, "prompt": None, "system_prompt": None}
    
    # Summarize data by day and convert to requested units
    day1_temps = [h.get('temp_f') for h in hourly_slice[:24] if h.get('temp_f')]
    day1_precip = [h.get('precip_prob', 0) for h in hourly_slice[:24]]
    day2_temps = [h.get('temp_f') for h in hourly_slice[24:48] if h.get('temp_f')]
    day2_precip = [h.get('precip_prob', 0) for h in hourly_slice[24:48]]
    
    # Convert temperatures if needed
    if temp_unit == 'C':
        day1_high = int(convert_temp(max(day1_temps), to_celsius=True)) if day1_temps else "N/A"
        day1_low = int(convert_temp(min(day1_temps), to_celsius=True)) if day1_temps else "N/A"
        day2_high = int(convert_temp(max(day2_temps), to_celsius=True)) if day2_temps else "N/A"
        day2_low = int(convert_temp(min(day2_temps), to_celsius=True)) if day2_temps else "N/A"
        temp_symbol = '°C'
    else:
        day1_high = int(max(day1_temps)) if day1_temps else "N/A"
        day1_low = int(min(day1_temps)) if day1_temps else "N/A"
        day2_high = int(max(day2_temps)) if day2_temps else "N/A"
        day2_low = int(min(day2_temps)) if day2_temps else "N/A"
        temp_symbol = '°F'
    
    day1_precip_max = int(max(day1_precip)) if day1_precip else 0
    day2_precip_max = int(max(day2_precip)) if day2_precip else 0

    # Build detailed hourly breakdown for 48 hours
    hourly_details = []
    for idx, h in enumerate(hourly_slice[:48]):
        temp_f = h.get('temp_f')
        if temp_f is None:
            continue
        
        # Convert temperature if needed
        if temp_unit == 'C':
            temp_display = f"{int(convert_temp(temp_f, to_celsius=True))}°C"
        else:
            temp_display = f"{int(temp_f)}°F"
        
        precip_prob = h.get('precip_prob', 0)
        precip_mm = h.get('precip_mm', 0)
        weather_code = h.get('weather_code', 0)
        conditions = get_weather_description(weather_code)
        time_str = h.get('time', '')
        
        hourly_details.append(
            f"Hour {idx+1} ({time_str[-5:] if len(time_str) > 5 else time_str}): {temp_display}, "
            f"{conditions}, {precip_prob}% rain, {precip_mm:.1f}mm"
        )
    
    # Create comprehensive hourly data string
    hourly_data_str = "\n".join(hourly_details[:48])  # All 48 hours

    system_prompt = """You are an expert meteorologist providing comprehensive weather analysis. 

Your analysis should include:
- **Current Weather Pattern**: Explain atmospheric conditions, pressure systems, fronts
- **48-Hour Forecast Breakdown**: Detailed timeline with temperature trends and precipitation
- **Weather Hazards & Alerts**: Any concerning conditions (storms, extreme temps, high winds)
- **Activity Recommendations**: Best times for outdoor/indoor activities based on conditions
- **Travel & Clothing Advice**: What to wear, what to bring (umbrella, sunscreen, jacket)
- **Health & Comfort Tips**: UV exposure, air quality, humidity impacts

Use professional weather terminology but keep it accessible. Include emojis for visual appeal.
Format with clear sections using markdown headers (##) and bullet points."""

    prompt = f"""Provide a comprehensive meteorological analysis for {city}, {region}, {country} on {today}.

## 48-Hour Detailed Forecast Data:

### Summary Statistics:
- **Day 1 (Next 24h)**: High {day1_high}{temp_symbol}, Low {day1_low}{temp_symbol}, Max precipitation: {day1_precip_max}%
- **Day 2 (24-48h)**: High {day2_high}{temp_symbol}, Low {day2_low}{temp_symbol}, Max precipitation: {day2_precip_max}%

### Hour-by-Hour Breakdown (48 Hours):
{hourly_data_str}

## Required Analysis Sections:

### 1. 🌍 Current Weather Pattern Analysis
Explain the meteorological conditions causing this weather (high/low pressure, fronts, seasonal patterns, etc.)

### 2. 📅 48-Hour Detailed Timeline
Break down the forecast into logical time periods (morning, afternoon, evening, night for both days). Highlight key changes.

### 3. ⚠️ Weather Hazards & Alerts
Identify any concerning conditions: extreme temperatures, heavy precipitation, storms, strong winds, poor visibility

### 4. 🎯 Activity & Travel Recommendations
- Best times for outdoor activities
- When to avoid being outside
- Travel considerations and road conditions

### 5. 👔 Clothing & Gear Advisor
What to wear and what to bring (layers, umbrella, sunglasses, sunscreen, winter gear, etc.)

### 6. 🏥 Health & Comfort Tips
UV index concerns, humidity impacts, temperature-related health advice

Be thorough but concise. Use emojis strategically. Format for easy reading."""

    def local_overview() -> str:
        """Build a detailed, non-AI 2-day overview from hourly data (next 48 hours).
        Includes likely precipitation hours per day and temperature ranges.
        """
        if not hourly_slice:
            return "Local overview unavailable: missing hourly data."
        city = location.get('city', 'Unknown')
        region = location.get('region', '')
        country = location.get('country', '')

        window = hourly_slice[:48]
        from datetime import datetime
        # Group by day (local date derived from ISO timestamp; assumes provided times are local or UTC-consistent)
        days = {}
        for h in window:
            ts = h.get('time')
            try:
                dt = datetime.fromisoformat(ts.replace('Z','+00:00'))
                day_key = dt.strftime('%Y-%m-%d')
                hour_label = dt.strftime('%-I %p')
            except Exception:
                # Fallback to raw string
                day_key = (ts or '')[:10]
                hour_label = ts
            days.setdefault(day_key, []).append({
                'temp_f': h.get('temp_f'),
                'precip_prob': h.get('precip_prob') or 0,
                'precip_mm': h.get('precip_mm') or 0.0,
                'label': hour_label,
            })

        lines = []
        lines.append(f"**Detailed 2-Day Weather Overview for {city}, {region}, {country}**\n")
        
        for i, (day, entries) in enumerate(sorted(days.items())):
            # Parse day for better formatting
            try:
                day_dt = datetime.fromisoformat(day)
                day_name = day_dt.strftime('%A')
                full_date = day_dt.strftime('%B %d, %Y')
                day_header = f"🌨️ {day_name} — {full_date}"
            except Exception:
                day_header = f"📅 {day}"
            
            lines.append(f"\n{day_header}")
            lines.append("=" * 50)
            
            # Temperature analysis
            temps = [e['temp_f'] for e in entries if e['temp_f'] is not None]
            if temps:
                tmin = int(round(min(temps)))
                tmax = int(round(max(temps)))
                tmin_c = int(round((tmin - 32) * 5/9))
                tmax_c = int(round((tmax - 32) * 5/9))
                
                lines.append(f"\n🌡️ **Temperature Range:**")
                lines.append(f"   • High: ~{tmax}°F ({tmax_c}°C)")
                lines.append(f"   • Low: ~{tmin}°F ({tmin_c}°C)")
                
                # Temperature description
                temp_range = tmax - tmin
                if temp_range > 20:
                    lines.append(f"   • Significant temperature variation of {temp_range}°F throughout the day")
                else:
                    lines.append(f"   • Relatively stable temperatures with {temp_range}°F variation")
            else:
                lines.append("\n🌡️ **Temperature Range:** Data unavailable")
            
            # Precipitation analysis
            pmax = int(max([e['precip_prob'] for e in entries])) if entries else 0
            total_mm = round(sum([e['precip_mm'] for e in entries]), 2)
            total_inches = round(total_mm * 0.0393701, 2)
            
            lines.append(f"\n� **Precipitation:**")
            lines.append(f"   • Maximum probability: {pmax}%")
            lines.append(f"   • Total accumulation: ~{total_mm} mm ({total_inches} inches)")
            
            # Detailed hourly precipitation breakdown
            precip_hours = [
                (e['label'], int(e['precip_prob']), round(e['precip_mm'], 2))
                for e in entries if (e['precip_prob'] >= 25 or e['precip_mm'] >= 0.5)
            ]
            
            if precip_hours:
                lines.append(f"\n⏰ **Precipitation Timeline:** (Times with ≥25% chance or ≥0.5mm)")
                
                # Group by time of day
                morning = [(h, p, m) for h, p, m in precip_hours if 'AM' in h and not ('12 AM' in h)]
                afternoon = [(h, p, m) for h, p, m in precip_hours if ('12 PM' in h or ('PM' in h and int(h.split()[0]) <= 5))]
                evening = [(h, p, m) for h, p, m in precip_hours if 'PM' in h and int(h.split()[0]) > 5]
                night = [(h, p, m) for h, p, m in precip_hours if '12 AM' in h or ('AM' in h and int(h.split()[0]) >= 11)]
                
                if morning:
                    lines.append(f"\n   ☀️ **Morning (6 AM - 11 AM):** {len(morning)} hour(s)")
                    for h, p, m in morning:
                        lines.append(f"      • {h}: {p}% probability, {m} mm expected")
                
                if afternoon:
                    lines.append(f"\n   🌤️ **Afternoon (12 PM - 5 PM):** {len(afternoon)} hour(s)")
                    for h, p, m in afternoon:
                        lines.append(f"      • {h}: {p}% probability, {m} mm expected")
                
                if evening:
                    lines.append(f"\n   🌙 **Evening (6 PM - 11 PM):** {len(evening)} hour(s)")
                    for h, p, m in evening:
                        lines.append(f"      • {h}: {p}% probability, {m} mm expected")
                
                if night:
                    lines.append(f"\n   🌃 **Night (12 AM - 5 AM):** {len(night)} hour(s)")
                    for h, p, m in night:
                        lines.append(f"      • {h}: {p}% probability, {m} mm expected")
                
                # Summary
                if pmax >= 70:
                    lines.append(f"\n   📌 **Alert:** High precipitation probability. Plan for wet conditions.")
                elif pmax >= 40:
                    lines.append(f"\n   📌 **Note:** Moderate precipitation expected. Carry an umbrella.")
                else:
                    lines.append(f"\n   📌 **Note:** Low to moderate precipitation chance.")
            else:
                lines.append(f"   • No significant precipitation expected")
                lines.append(f"   📌 **Note:** Dry conditions expected throughout the day")
            
            lines.append("")  # Blank line between days
        
        # Overall summary
        lines.append("\n" + "=" * 50)
        lines.append("📊 **2-Day Summary:**")
        all_temps = []
        all_precip_prob = []
        all_precip_mm = []
        for day, entries in sorted(days.items()):
            all_temps.extend([e['temp_f'] for e in entries if e['temp_f'] is not None])
            all_precip_prob.extend([e['precip_prob'] for e in entries])
            all_precip_mm.extend([e['precip_mm'] for e in entries])
        
        if all_temps:
            overall_high = int(round(max(all_temps)))
            overall_low = int(round(min(all_temps)))
            lines.append(f"   • Overall temperature range: {overall_low}°F to {overall_high}°F")
        
        if all_precip_prob:
            avg_precip_prob = int(sum(all_precip_prob) / len(all_precip_prob))
            total_precip_mm = round(sum(all_precip_mm), 2)
            total_precip_in = round(total_precip_mm * 0.0393701, 2)
            lines.append(f"   • Average precipitation probability: {avg_precip_prob}%")
            lines.append(f"   • Total 48-hour precipitation: {total_precip_mm} mm ({total_precip_in} inches)")
        
        return "\n".join(lines)

    try:
        # Use Groq AI - ultra-fast inference!
        import httpx
        
        # Create HTTP client with SSL verification disabled
        http_client = httpx.Client(verify=False, timeout=15.0)
        client = Groq(api_key=groq_api_key, http_client=http_client)
        
        # Generate content with Groq (blazing fast!)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Fast and capable model
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000  # Increased for detailed comprehensive response
        )
        
        http_client.close()
        
        # Return full response data
        return {
            "text": response.choices[0].message.content,
            "raw_response": response.model_dump_json(indent=2),
            "prompt": prompt,
            "system_prompt": system_prompt
        }
    except Exception as e:
        # If API fails, return local overview
        error_msg = f"⚠️ AI unavailable: {str(e)[:80]}\n\nUsing local forecast:\n\n{local_overview()}"
        return {
            "text": error_msg,
            "raw_response": None,
            "prompt": prompt,
            "system_prompt": system_prompt
        }

def generate_ai_overview_narrative(location: Dict[str, Any], hourly_slice: List[Dict], temp_unit='F', wind_unit='mph') -> Dict[str, Any]:
    """Use Groq AI to produce a narrative-style weather forecast with day-by-day breakdown.
    
    Returns:
        dict with 'text' (formatted response), 'raw_response' (JSON), 'prompt' (user prompt), 'system_prompt'
    """
    # Groq API configuration - load from session state first, then environment variable
    groq_api_key = st.session_state.get('groq_api_key', '')
    
    if not groq_api_key:
        groq_api_key = os.environ.get('GROQ_API_KEY', '')
    
    if not groq_api_key:
        return {"text": "⚠️ Groq API key not configured. Please set GROQ_API_KEY environment variable.", "raw_response": None, "prompt": None, "system_prompt": None}
    
    if not Groq:
        return {"text": "⚠️ Groq library not installed. Run: pip install groq", "raw_response": None, "prompt": None, "system_prompt": None}

    city = location.get('city', 'Unknown')
    region = location.get('region', '')
    country = location.get('country', '')
    
    # Get current date for context
    from datetime import datetime
    today = datetime.now().strftime('%B %d, %Y')

    if not hourly_slice:
        return {"text": "AI overview unavailable: missing hourly data.", "raw_response": None, "prompt": None, "system_prompt": None}
    
    # Build detailed hourly breakdown for 48 hours
    hours_blob = []
    for idx, h in enumerate(hourly_slice[:48]):
        temp_f = h.get('temp_f')
        if temp_f is None:
            continue
        
        # Convert temperature if needed
        if temp_unit == 'C':
            temp_display = f"{int(convert_temp(temp_f, to_celsius=True))}°C"
        else:
            temp_display = f"{int(temp_f)}°F"
        
        precip_prob = h.get('precip_prob', 0)
        precip_mm = h.get('precip_mm', 0)
        weather_code = h.get('weather_code', 0)
        conditions = get_weather_description(weather_code)
        time_str = h.get('time', '')
        
        hours_blob.append(
            f"{time_str}: {temp_display}, {conditions}, Precip: {precip_prob}%, {precip_mm:.1f}mm"
        )
    
    hours_blob_str = "\n".join(hours_blob)

    system_prompt = """You are a professional meteorologist creating detailed weather forecasts in a narrative style. 

Write in complete, natural sentences (not bullet points). Use weather terminology like 'accumulating snow', 'lingering showers', 'tapering off'. Include transitions like 'developing', 'becomes steadier', 'continuing into'.

Break precipitation into 4 time periods with emojis:
- ☀️ Morning (6 AM - 11 AM)
- 🌤️ Afternoon (12 PM - 5 PM)  
- 🌙 Evening (6 PM - 11 PM)
- 🌃 Night (12 AM - 5 AM)

Call out specific hours with percentages when relevant (e.g., '7 AM: 45% chance', '2 PM: 65% chance').

Use proper formatting with double line breaks between sections and separator lines for organization."""

    prompt = f"""Location: {city}, {region}, {country}
Date: {today}

HOURLY FORECAST DATA (next 48 hours):
{hours_blob_str}

Create a comprehensive forecast using this EXACT format:

🌨️ <DayName> — <Full Date (e.g., December 15, 2025)>
==================================================

**General**

<2-3 complete sentences describing overall conditions, sky cover, and primary weather pattern for the day.>

**Temperatures**

🌡️ High: ~<high°F> (<high°C>)

🌡️ Low: ~<low°F> (<low°C>) overnight

<Additional sentence about temperature feel and trends.>

**Precipitation Timeline**

☀️ **Morning (6 AM - 11 AM):**
<Natural narrative with specific hours and percentages if precip occurs, or 'No precipitation expected.'>

🌤️ **Afternoon (12 PM - 5 PM):**
<Natural narrative with specific hours like '2 PM: 65% chance' if precip occurs, or 'Dry conditions.'>

🌙 **Evening (6 PM - 11 PM):**
<Natural narrative describing evening precip with specific hours and intensity changes, or 'Clear skies.'>

🌃 **Night (12 AM - 5 AM):**
<Natural narrative describing overnight precip with specific hours, or 'No precipitation overnight.'>

**Winds & Conditions**

<Complete sentences about wind speeds, gusts, and overall comfort conditions based on the data patterns.>

[Repeat exact same format for Day 2]

==================================================

**📊 2-Day Summary**

<DayName>: <One-sentence summary highlighting key weather impacts.>

<DayName>: <One-sentence summary highlighting key weather impacts.>

<Additional summary sentence about overall pattern or temperatures.>

CRITICAL FORMATTING RULES:
- Use double line breaks between sections
- Write in complete, natural sentences (not bullet points)
- Call out specific hours with percentages: '7 AM: 45%', '2 PM: 65% chance'
- Include transitions: 'developing', 'becomes steadier', 'tapering off'
- Add separator lines (==================================================) for visual organization"""

    try:
        # Use Groq AI - ultra-fast inference!
        import httpx
        
        # Create HTTP client with SSL verification disabled
        http_client = httpx.Client(verify=False, timeout=15.0)
        client = Groq(api_key=groq_api_key, http_client=http_client)
        
        # Generate content with Groq (blazing fast!)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Fast and capable model
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000  # Increased for detailed comprehensive response
        )
        
        http_client.close()
        
        # Return full response data
        return {
            "text": response.choices[0].message.content,
            "raw_response": response.model_dump_json(indent=2),
            "prompt": prompt,
            "system_prompt": system_prompt
        }
    except Exception as e:
        error_msg = f"⚠️ AI unavailable: {str(e)[:80]}"
        return {
            "text": error_msg,
            "raw_response": None,
            "prompt": prompt,
            "system_prompt": system_prompt
        }

def chat_with_weather_ai(user_message: str, weather_context: str) -> Dict[str, Any]:
    """Chat with AI about weather using Groq.
    
    Args:
        user_message: User's question or message
        weather_context: Current weather data as context
    
    Returns:
        dict with 'text', 'system_prompt', 'user_prompt', 'raw_response'
    """
    # Groq API configuration - load from session state first, then environment variable
    groq_api_key = st.session_state.get('groq_api_key', '')
    
    if not groq_api_key:
        groq_api_key = os.environ.get('GROQ_API_KEY', '')
    
    if not groq_api_key or not Groq:
        return {"text": "⚠️ Groq API not configured.", "system_prompt": None, "user_prompt": None, "raw_response": None}
    
    try:
        import httpx
        
        # Create HTTP client with SSL verification disabled
        http_client = httpx.Client(verify=False, timeout=15.0)
        client = Groq(api_key=groq_api_key, http_client=http_client)
        
        # System prompt
        system_prompt = f"""You are a confident and assertive weather expert. You provide accurate, reliable weather information based on professional-grade weather data. Answer questions decisively based on this context:

{weather_context}

IMPORTANT GUIDELINES:
- Be assertive and confident in your responses
- Our weather data is highly accurate and comes from multiple trusted global weather models (ECMWF, GFS, ICON)
- Never recommend users to check other weather apps or services - our data is comprehensive and reliable
- Speak with authority about weather patterns and forecasts
- Use emojis to make responses engaging, but maintain a professional, confident tone
- If asked about accuracy, confidently affirm that our data is reliable and sourced from top meteorological agencies
- Provide definitive answers rather than uncertain or hedging language"""
        
        # Build chat messages with context
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add chat history (last 10 messages to keep context manageable)
        for msg in st.session_state.chat_history[-10:]:
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Generate response
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        
        http_client.close()
        
        return {
            "text": response.choices[0].message.content,
            "system_prompt": system_prompt,
            "user_prompt": user_message,
            "raw_response": response.model_dump_json(indent=2)
        }
        
    except Exception as e:
        return {"text": f"Error: {str(e)}", "system_prompt": None, "user_prompt": user_message, "raw_response": None}

def compare_travel_weather(current_location: Dict[str, Any], current_weather: Dict[str, Any], 
                          destination_location: Dict[str, Any], destination_weather: Dict[str, Any],
                          temp_unit='F', wind_unit='mph') -> Dict[str, Any]:
    """Compare weather between current location and travel destination using Groq AI.
    
    Returns:
        dict with 'table_data', 'ai_insights', 'raw_response', 'prompt', 'system_prompt'
    """
    # Groq API configuration - load from session state first, then environment variable
    groq_api_key = st.session_state.get('groq_api_key', '')
    
    if not groq_api_key:
        groq_api_key = os.environ.get('GROQ_API_KEY', '')
    
    if not groq_api_key or not Groq:
        return {"table_data": None, "ai_insights": "⚠️ Groq API not configured.", "raw_response": None, "prompt": None, "system_prompt": None}
    
    try:
        # Extract current weather data
        current_temp = current_weather.get('current_weather', {}).get('temperature', 'N/A')
        current_city = current_location.get('city', 'Unknown')
        current_region = current_location.get('region', '')
        
        # Extract destination weather data
        dest_temp = destination_weather.get('current_weather', {}).get('temperature', 'N/A')
        dest_city = destination_location.get('city', 'Unknown')
        dest_region = destination_location.get('region', '')
        
        # Get hourly forecasts for both
        current_hourly = current_weather.get('hourly', {})
        dest_hourly = destination_weather.get('hourly', {})
        current_current = current_weather.get('current', {})
        dest_current = destination_weather.get('current', {})
        
        # Calculate temperature ranges for next 24 hours
        # Note: Open-Meteo API returns temps in Fahrenheit (set in get_weather function)
        def get_temp_range(hourly_data):
            temps_f = hourly_data.get('temperature_2m', [])[:24]
            if temps_f:
                min_f = int(min(temps_f))
                max_f = int(max(temps_f))
                min_c = int((min_f - 32) * 5/9)
                max_c = int((max_f - 32) * 5/9)
                return f"{min_f}°F ({min_c}°C) to {max_f}°F ({max_c}°C)"
            return "N/A"
        
        def get_precip_info(hourly_data):
            precip_probs = hourly_data.get('precipitation_probability', [])[:24]
            if precip_probs:
                return f"{int(max(precip_probs))}%"
            return "N/A"
        
        def get_current_temp(current_data):
            temp_f = current_data.get('temperature_2m', 'N/A')
            if temp_f != 'N/A':
                temp_c = int((temp_f - 32) * 5/9)
                return f"{int(temp_f)}°F ({temp_c}°C)"
            return "N/A"
        
        def get_humidity(current_data):
            hum = current_data.get('relative_humidity_2m', 'N/A')
            return f"{hum}%" if hum != 'N/A' else "N/A"
        
        def get_wind(current_data):
            wind_mph = current_data.get('wind_speed_10m', 'N/A')
            if wind_mph != 'N/A':
                wind_kmh = int(wind_mph * 1.60934)
                return f"{int(wind_mph)} mph ({wind_kmh} km/h)"
            return "N/A"
        
        def get_conditions(current_data):
            weather_code = current_data.get('weather_code', 0)
            return get_weather_description(weather_code)
        
        current_temp_range = get_temp_range(current_hourly)
        dest_temp_range = get_temp_range(dest_hourly)
        current_precip = get_precip_info(current_hourly)
        dest_precip = get_precip_info(dest_hourly)
        
        # Build comparison table data
        table_data = {
            'Metric': ['📍 Location', '🌡️ Current Temp', '📊 24h Range', '💧 Humidity', '💨 Wind Speed', '🌤️ Conditions', '🌧️ Rain Chance (24h)'],
            f'{current_city}': [
                f"{current_city}, {current_region}",
                get_current_temp(current_current),
                current_temp_range,
                get_humidity(current_current),
                get_wind(current_current),
                get_conditions(current_current),
                current_precip
            ],
            f'{dest_city}': [
                f"{dest_city}, {dest_region}",
                get_current_temp(dest_current),
                dest_temp_range,
                get_humidity(dest_current),
                get_wind(dest_current),
                get_conditions(dest_current),
                dest_precip
            ]
        }
        
        system_prompt = """You are a travel weather advisor. Provide travel insights and recommendations based on weather comparison.
- Focus on actionable travel advice and packing tips
- Highlight what the traveler should prepare for
- Be concise and use emojis
- Use bullet points for clarity"""
        
        prompt = f"""Based on this weather comparison for travel from {current_city} to {dest_city}:

Current Location: {current_city}, {current_region}
- Temperature Range (24h): {current_temp_range}
- Precipitation Chance: {current_precip}

Destination: {dest_city}, {dest_region}
- Temperature Range (24h): {dest_temp_range}
- Precipitation Chance: {dest_precip}

Provide brief travel insights:
• Key weather differences to prepare for
• Essential items to pack
• Best timing or weather considerations

Keep it under 150 words, use emojis and bullet points."""
        
        import httpx
        
        # Create HTTP client with SSL verification disabled
        http_client = httpx.Client(verify=False, timeout=15.0)
        client = Groq(api_key=groq_api_key, http_client=http_client)
        
        # Generate insights
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        
        http_client.close()
        
        ai_insights = response.choices[0].message.content
        
        return {
            "table_data": table_data,
            "ai_insights": ai_insights,
            "raw_response": response.model_dump_json(indent=2),
            "prompt": prompt,
            "system_prompt": system_prompt
        }
        
    except Exception as e:
        return {"table_data": None, "ai_insights": f"Error comparing weather: {str(e)}", "raw_response": None, "prompt": None, "system_prompt": None}

def display_radar(location, temperature_f=None):
    """Display animated weather radar using RainViewer and OpenStreetMap."""
    
    lat = location['latitude']
    lon = location['longitude']
    
    # Create radar map HTML with animation using RainViewer and Leaflet
    radar_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background: #1e1e2d; }}
            #map {{ 
                height: 500px; 
                width: 100%; 
                border-radius: 15px;
                border: 2px solid rgba(100, 100, 150, 0.3);
            }}
            .leaflet-container {{
                background: #0f0c29;
            }}
            .leaflet-layer {{
                transition: opacity 0.3s ease-in-out;
            }}
            .radar-controls {{
                position: absolute;
                top: 10px;
                right: 10px;
                z-index: 9999;
                background: rgba(20, 20, 35, 0.98);
                padding: 15px;
                border-radius: 12px;
                color: white;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                min-width: 200px;
                border: 2px solid rgba(100, 100, 255, 0.4);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            }}
            .radar-controls button {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                cursor: pointer;
                margin: 2px;
                font-size: 12px;
                width: 100%;
            }}
            .radar-controls button:hover {{
                background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            }}
            .radar-controls button:disabled {{
                background: #555;
                cursor: not-allowed;
                opacity: 0.5;
            }}
            .timestamp {{
                font-size: 13px;
                font-weight: 600;
                color: #fff;
                margin-top: 10px;
                padding: 8px;
                text-align: center;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            .control-group {{
                margin: 5px 0;
            }}
            .play-btn {{
                background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%) !important;
            }}
            .play-btn:hover {{
                background: linear-gradient(135deg, #0099cc 0%, #00d4ff 100%) !important;
            }}
        </style>
    </head>
    <body>
        <div class="radar-controls">
            <div style="margin-bottom: 10px; font-size: 14px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 8px;"><strong>🌧️ Radar Controls</strong></div>
            <div class="control-group">
                <button id="playBtn" class="play-btn" onclick="toggleAnimation()">▶️ Play</button>
            </div>
            <div class="control-group">
                <button onclick="map.setView([{lat}, {lon}], map.getZoom())">📍 Center</button>
            </div>
            <div class="control-group">
                <button onclick="toggleRadarVisibility()">👁️ Toggle Radar</button>
            </div>
            <div class="timestamp" id="timestamp">Loading frames...</div>
        </div>
        <div id="map"></div>
        <script>
            // Clean up any existing map instance
            if (window.radarMap) {{
                window.radarMap.remove();
                window.radarMap = null;
            }}
            
            // Clear any existing animation intervals
            if (window.radarAnimationInterval) {{
                clearInterval(window.radarAnimationInterval);
                window.radarAnimationInterval = null;
            }}
            
            // Initialize map with reasonable zoom limits
            const map = L.map('map', {{
                maxZoom: 15,  // Good balance between detail and radar quality
                zoomControl: true
            }}).setView([{lat}, {lon}], 8);
            window.radarMap = map;  // Store globally for cleanup
            
            // Add dark tile layer
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                maxZoom: 19  // Base map supports higher zoom
            }}).addTo(map);
            
            // Add zoom level indicator
            map.on('zoomend', function() {{
                const zoom = map.getZoom();
                const timestamp = document.getElementById('timestamp');
                if (zoom > 13 && radarVisible && radarFrames.length > 0) {{
                    // At zoom 14-15, tiles are scaled up
                    updateTimestamp();
                    const currentText = timestamp.textContent;
                    if (!currentText.includes('⚠️')) {{
                        timestamp.textContent = currentText + ' ⚠️ Scaled';
                    }}
                }} else if (radarFrames.length > 0 && !timestamp.textContent.includes('⚠️')) {{
                    updateTimestamp();
                }}
            }});
            
            // Add location marker
            const marker = L.marker([{lat}, {lon}]).addTo(map);
            marker.bindPopup('<b>{location['city']}</b><br>{location['region']}, {location['country']}').openPopup();
            
            // Animation variables
            let radarFrames = [];
            let radarLayers = [];
            let animationInterval = null;
            let currentFrameIndex = 0;
            let isPlaying = false;
            let radarVisible = true;
            let framesLoaded = 0;
            let pastFramesCount = 0;  // Track where past ends and future begins
            
            // Load all radar frames with preloading for smooth animation
            function loadRadarFrames() {{
                console.log('🔄 Loading RainViewer radar data...');
                document.getElementById('timestamp').textContent = '🔄 Connecting to radar service...';
                document.getElementById('timestamp').style.color = '#00d4ff';
                
                fetch('https://api.rainviewer.com/public/weather-maps.json')
                    .then(response => {{
                        console.log('✅ Radar API response received:', response.status);
                        if (!response.ok) {{
                            throw new Error(`HTTP error! status: ${{response.status}}`);
                        }}
                        return response.json();
                    }})
                    .then(data => {{
                        console.log('📊 Radar data parsed:', data);
                        if (data.radar) {{
                            // Combine past and future (nowcast) frames
                            let allFrames = [];
                            
                            // Add past frames (2 hours)
                            if (data.radar.past && data.radar.past.length > 0) {{
                                allFrames = allFrames.concat(data.radar.past);
                                console.log(`📥 Loaded ${{data.radar.past.length}} past frames`);
                            }}
                            
                            // Add nowcast frames (30 min future) if available
                            if (data.radar.nowcast && data.radar.nowcast.length > 0) {{
                                allFrames = allFrames.concat(data.radar.nowcast);
                                console.log(`🔮 Loaded ${{data.radar.nowcast.length}} future frames`);
                            }}
                            
                            if (allFrames.length === 0) {{
                                document.getElementById('timestamp').textContent = '⚠️ No radar data available';
                                document.getElementById('timestamp').style.color = '#ff9800';
                                console.warn('⚠️ No radar frames available in API response');
                                return;
                            }}
                            
                            radarFrames = allFrames;
                            framesLoaded = 0;
                            
                            pastFramesCount = data.radar.past ? data.radar.past.length : 0;
                            
                            // Create and preload layers for all frames
                            radarFrames.forEach((frame, index) => {{
                                // Color scheme 4 = The Weather Channel style
                                // RainViewer tiles work best up to zoom level 12-13
                                const radarUrl = `https://tilecache.rainviewer.com${{frame.path}}/256/{{z}}/{{x}}/{{y}}/4/1_1.png`;
                                
                                const layer = L.tileLayer(radarUrl, {{
                                    opacity: 0,
                                    zIndex: 10 + index,
                                    className: 'radar-layer',
                                    maxZoom: 15,  // Map can zoom to level 15
                                    maxNativeZoom: 13,  // Radar tiles exist up to level 13
                                    minZoom: 0,
                                    tileSize: 256,
                                    keepBuffer: 4,  // Keep more tiles in memory for smoother display
                                    updateWhenIdle: true,  // Wait for idle to prevent constant reloading
                                    updateWhenZooming: true,
                                    updateInterval: 200
                                }});
                                
                                // Add to map immediately but invisible (for preloading)
                                layer.addTo(map);
                                
                                // Listen for tile loading
                                layer.on('load', function() {{
                                    framesLoaded++;
                                    console.log(`✅ Frame ${{framesLoaded}}/${{radarFrames.length}} loaded`);
                                    if (framesLoaded === radarFrames.length) {{
                                        const hasNowcast = data.radar.nowcast && data.radar.nowcast.length > 0;
                                        const msg = hasNowcast ? 
                                            `✅ Ready - ${{pastFramesCount}} past + ${{radarFrames.length - pastFramesCount}} future` :
                                            `✅ Ready - ${{radarFrames.length}} frames loaded`;
                                        document.getElementById('timestamp').textContent = msg;
                                        document.getElementById('timestamp').style.color = '#00ff88';
                                        console.log('✅ All radar frames loaded successfully!');
                                        // Show last past frame (present moment) once all loaded
                                        showFrame(pastFramesCount - 1);
                                    }} else {{
                                        document.getElementById('timestamp').textContent = 
                                            `⏳ Loading... ${{framesLoaded}}/${{radarFrames.length}}`;
                                        document.getElementById('timestamp').style.color = '#00d4ff';
                                    }}
                                }});
                                
                                // Listen for tile errors
                                layer.on('tileerror', function(error) {{
                                    console.error('❌ Tile load error for frame ${{index}}:', error);
                                }});
                                
                                radarLayers.push(layer);
                            }});
                            
                            currentFrameIndex = pastFramesCount - 1;  // Start at current time
                        }} else {{
                            document.getElementById('timestamp').textContent = '⚠️ No radar data in response';
                            document.getElementById('timestamp').style.color = '#ff9800';
                            console.warn('⚠️ API returned no radar data');
                        }}
                    }})
                    .catch(error => {{
                        console.error('❌ Error loading radar:', error);
                        document.getElementById('timestamp').textContent = '❌ Radar service unavailable - Check network/firewall';
                        document.getElementById('timestamp').style.color = '#ff4444';
                    }});
            }}
            
            function updateTimestamp() {{
                if (radarFrames.length > 0) {{
                    const frame = radarFrames[currentFrameIndex];
                    const date = new Date(frame.time * 1000);
                    const timeStr = date.toLocaleTimeString();
                    
                    // Determine if frame is past or future
                    const label = currentFrameIndex < pastFramesCount ? '📊 PAST' : '🔮 FUTURE';
                    const now = currentFrameIndex === pastFramesCount - 1 ? ' (NOW)' : '';
                    
                    document.getElementById('timestamp').textContent = 
                        `${{label}}${{now}} - ${{timeStr}}`;
                }}
            }}
            
            function showFrame(index) {{
                // Smoothly fade out current frame
                if (radarLayers[currentFrameIndex]) {{
                    radarLayers[currentFrameIndex].setOpacity(0);
                }}
                
                // Update index
                currentFrameIndex = index;
                
                // Smoothly fade in new frame
                if (radarVisible && radarLayers[currentFrameIndex]) {{
                    radarLayers[currentFrameIndex].setOpacity(0.7);
                }}
                
                updateTimestamp();
            }}
            
            function toggleAnimation() {{
                const playBtn = document.getElementById('playBtn');
                
                if (isPlaying) {{
                    // Stop animation
                    clearInterval(animationInterval);
                    window.radarAnimationInterval = null;
                    isPlaying = false;
                    playBtn.textContent = '▶️ Play';
                }} else {{
                    // Start animation
                    isPlaying = true;
                    playBtn.textContent = '⏸️ Pause';
                    
                    animationInterval = setInterval(() => {{
                        let nextFrame = currentFrameIndex + 1;
                        if (nextFrame >= radarFrames.length) {{
                            nextFrame = 0;  // Loop back to start
                        }}
                        showFrame(nextFrame);
                    }}, 500);  // 500ms per frame (2 frames/second)
                    window.radarAnimationInterval = animationInterval;  // Store globally for cleanup
                }}
            }}
            
            function toggleRadarVisibility() {{
                radarVisible = !radarVisible;
                
                if (radarVisible) {{
                    // Fade in current frame
                    if (radarLayers[currentFrameIndex]) {{
                        radarLayers[currentFrameIndex].setOpacity(0.7);
                    }}
                }} else {{
                    // Fade out all frames
                    radarLayers.forEach(layer => {{
                        layer.setOpacity(0);
                    }});
                }}
            }}
            
            // Load radar on startup
            loadRadarFrames();
            
            // Refresh radar data every 5 minutes
            setInterval(function() {{
                // Stop animation if playing
                if (isPlaying) {{
                    toggleAnimation();
                }}
                
                // Clear existing layers
                radarLayers.forEach(layer => map.removeLayer(layer));
                radarLayers = [];
                radarFrames = [];
                currentFrameIndex = 0;
                
                // Reload
                loadRadarFrames();
            }}, 300000);
        </script>
    </body>
    </html>
    """
    
    # Display the radar map
    components.html(radar_html, height=520)
    
    # Dynamic description color based on temperature
    desc_color = "#263238" if temperature_f is not None and 76 <= temperature_f <= 95 else "#888"
    st.markdown(f"""
    <div style='text-align: center; margin-top: 10px; color: {desc_color}; font-size: 0.85em;'>
        🔄 Radar updates every 5 minutes | 
        <span style='color: #667eea;'>Blue/Green</span> = Light Rain | 
        <span style='color: #e6b800;'>Yellow</span> = Moderate | 
        <span style='color: #ff4444;'>Red</span> = Heavy
    </div>
    """, unsafe_allow_html=True)

def display_visual_crossing_radar(location, temperature_f=None):
    """Display animated radar using OpenWeatherMap precipitation layer."""
    
    lat = location['latitude']
    lon = location['longitude']
    
    # Create animated radar HTML
    vc_radar_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background: #1e1e2d; }}
            #vcmap {{ 
                height: 500px; 
                width: 100%; 
                border-radius: 15px;
                border: 2px solid rgba(100, 100, 150, 0.3);
            }}
            .leaflet-container {{
                background: #0f0c29;
            }}
            .vc-controls {{
                position: absolute;
                top: 10px;
                right: 10px;
                z-index: 9999;
                background: rgba(20, 20, 35, 0.98);
                padding: 15px;
                border-radius: 12px;
                color: white;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                min-width: 200px;
                border: 2px solid rgba(100, 100, 255, 0.4);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            }}
            .vc-controls button {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                cursor: pointer;
                margin: 2px;
                font-size: 12px;
                width: 100%;
            }}
            .vc-controls button:hover {{
                background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            }}
            .play-btn {{
                background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%) !important;
            }}
            .play-btn:hover {{
                background: linear-gradient(135deg, #0099cc 0%, #00d4ff 100%) !important;
            }}
            .control-group {{
                margin: 5px 0;
            }}
            .timestamp {{
                font-size: 13px;
                font-weight: 600;
                color: #fff;
                margin-top: 10px;
                padding: 8px;
                text-align: center;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        </style>
    </head>
    <body>
        <div class="vc-controls">
            <div style="margin-bottom: 10px; font-size: 14px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 8px;"><strong>Precipitation Controls</strong></div>
            <div class="control-group">
                <button id="playBtn" class="play-btn" onclick="toggleAnimation()">▶️ Play</button>
            </div>
            <div class="control-group">
                <button onclick="vcmap.setView([{lat}, {lon}], vcmap.getZoom())">📍 Center</button>
            </div>
            <div class="control-group">
                <button onclick="toggleRadar()">👁️ Toggle Radar</button>
            </div>
            <div class="timestamp" id="timestamp">Loading...</div>
        </div>
        <div id="vcmap"></div>
        <script>
            // Initialize map
            const vcmap = L.map('vcmap', {{
                maxZoom: 15,  // Good balance between detail and radar quality
                zoomControl: true
            }}).setView([{lat}, {lon}], 8);
            
            // Add dark tile layer
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                attribution: '&copy; OpenStreetMap contributors',
                maxZoom: 19
            }}).addTo(vcmap);
            
            // Add location marker
            const vcmarker = L.marker([{lat}, {lon}]).addTo(vcmap);
            vcmarker.bindPopup('<b>{location['city']}</b><br>{location['region']}, {location['country']}').openPopup();
            
            // Add zoom level indicator
            vcmap.on('zoomend', function() {{
                const zoom = vcmap.getZoom();
                const timestamp = document.getElementById('timestamp');
                if (zoom > 13 && radarVisible && radarFrames.length > 0 && !timestamp.textContent.includes('Loading')) {{
                    const currentText = timestamp.textContent;
                    if (!currentText.includes('⚠️')) {{
                        timestamp.textContent = currentText + ' ⚠️ Scaled';
                    }}
                }}
            }});
            
            // Animation variables
            let precipLayers = [];
            let radarFrames = [];
            let animationInterval = null;
            let currentFrame = 0;
            let isPlaying = false;
            let radarVisible = true;
            
            // Load precipitation frames from RainViewer
            function loadPrecipFrames() {{
                console.log('🔄 Loading Visual Crossing radar data...');
                document.getElementById('timestamp').textContent = '🔄 Connecting to radar service...';
                document.getElementById('timestamp').style.color = '#00d4ff';
                
                fetch('https://api.rainviewer.com/public/weather-maps.json')
                    .then(response => {{
                        console.log('✅ Radar API response received:', response.status);
                        if (!response.ok) {{
                            throw new Error(`HTTP error! status: ${{response.status}}`);
                        }}
                        return response.json();
                    }})
                    .then(data => {{
                        if (data.radar && data.radar.past) {{
                            // Clear existing layers
                            precipLayers.forEach(layer => vcmap.removeLayer(layer));
                            precipLayers = [];
                            radarFrames = [];
                            
                            // Use only last 4 frames for faster loading and better performance
                            const pastFrames = data.radar.past || [];
                            radarFrames = pastFrames.slice(-4);
                            
                            if (radarFrames.length === 0) {{
                                document.getElementById('timestamp').textContent = '⚠️ No radar data available';
                                document.getElementById('timestamp').style.color = '#ff9800';
                                console.warn('⚠️ No radar frames in API response');
                                return;
                            }}
                            
                            console.log(`📊 Processing ${{radarFrames.length}} radar frames`);
                            
                            let loadedCount = 0;
                            const totalFrames = radarFrames.length;
                            
                            // Create layers for each frame with preloading
                            radarFrames.forEach((frame, index) => {{
                                // Color scheme 6 = NEXRAD style (different from main radar)
                                const radarUrl = `https://tilecache.rainviewer.com${{frame.path}}/256/{{z}}/{{x}}/{{y}}/6/1_1.png`;
                                
                                const layer = L.tileLayer(radarUrl, {{
                                    opacity: 0,
                                    zIndex: 10 + index,
                                    maxZoom: 15,  // Map can zoom to level 15
                                    maxNativeZoom: 13,  // Radar tiles exist up to level 13
                                    tileSize: 256,
                                    keepBuffer: 4,  // Keep more tiles in memory
                                    updateWhenIdle: true,  // Wait for idle
                                    updateWhenZooming: true,
                                    updateInterval: 200
                                }});
                                
                                // Add to map first
                                layer.addTo(vcmap);
                                precipLayers.push(layer);
                                
                                // Track tile loading
                                layer.on('load', function() {{
                                    loadedCount++;
                                    console.log(`✅ Frame ${{loadedCount}}/${{totalFrames}} loaded`);
                                    if (loadedCount === totalFrames) {{
                                        document.getElementById('timestamp').textContent = `✅ Ready - ${{totalFrames}} frames`;
                                        document.getElementById('timestamp').style.color = '#00ff88';
                                        console.log('✅ All precipitation frames loaded!');
                                        // Show most recent frame once loaded
                                        currentFrame = totalFrames - 1;
                                        showFrame(currentFrame);
                                    }} else {{
                                        document.getElementById('timestamp').textContent = `⏳ Loading... ${{loadedCount}}/${{totalFrames}}`;
                                        document.getElementById('timestamp').style.color = '#00d4ff';
                                    }}
                                }});
                                
                                // Handle tile errors
                                layer.on('tileerror', function(error) {{
                                    console.error('❌ Tile load error for frame ${{index}}:', error);
                                }});
                            }});
                            
                            // Show most recent frame immediately (will update when loaded)
                            currentFrame = radarFrames.length - 1;
                            showFrame(currentFrame);
                        }} else {{
                            document.getElementById('timestamp').textContent = '⚠️ No radar data in response';
                            document.getElementById('timestamp').style.color = '#ff9800';
                            console.warn('⚠️ API returned no radar data');
                        }}
                    }})
                    .catch(error => {{
                        console.error('❌ Error loading radar:', error);
                        document.getElementById('timestamp').textContent = '❌ Radar service unavailable - Check network/firewall';
                        document.getElementById('timestamp').style.color = '#ff4444';
                    }});
            }}
            
            function showFrame(index) {{
                // Hide all frames
                precipLayers.forEach(layer => {{
                    layer.setOpacity(0);
                }});
                
                // Show selected frame
                if (radarVisible && precipLayers[index]) {{
                    precipLayers[index].setOpacity(0.7);
                    // Force redraw to ensure tiles appear at all zoom levels
                    precipLayers[index].redraw();
                }}
                
                currentFrame = index;
                
                // Update timestamp
                if (radarFrames.length > 0 && radarFrames[index]) {{
                    const frame = radarFrames[index];
                    const date = new Date(frame.time * 1000);
                    const now = Date.now();
                    const minutesAgo = Math.round((now - date.getTime()) / 60000);
                    
                    if (minutesAgo < 5) {{
                        document.getElementById('timestamp').textContent = 'Current';
                    }} else {{
                        document.getElementById('timestamp').textContent = `${{minutesAgo}} min ago`;
                    }}
                }}
            }}
            
            function toggleAnimation() {{
                const playBtn = document.getElementById('playBtn');
                
                if (isPlaying) {{
                    clearInterval(animationInterval);
                    isPlaying = false;
                    playBtn.textContent = '▶️ Play';
                }} else {{
                    isPlaying = true;
                    playBtn.textContent = '⏸️ Pause';
                    
                    animationInterval = setInterval(() => {{
                        let nextFrame = currentFrame + 1;
                        if (nextFrame >= precipLayers.length) {{
                            nextFrame = 0;
                        }}
                        showFrame(nextFrame);
                    }}, 500); // 500ms per frame
                }}
            }}
            
            function toggleRadar() {{
                radarVisible = !radarVisible;
                if (radarVisible) {{
                    precipLayers[currentFrame].setOpacity(0.7);
                }} else {{
                    precipLayers.forEach(layer => layer.setOpacity(0));
                }}
            }}
            
            // Load radar on startup
            loadPrecipFrames();
            
            // Refresh every 5 minutes
            setInterval(() => {{
                if (isPlaying) {{
                    toggleAnimation();
                }}
                loadPrecipFrames();
            }}, 300000);
        </script>
    </body>
    </html>
    """
    
    # Display the map
    components.html(vc_radar_html, height=520)
    
    # Dynamic description color based on temperature
    desc_color = "#263238" if temperature_f is not None and 76 <= temperature_f <= 95 else "#888"
    st.markdown(f"""
    <div style='text-align: center; margin-top: 10px; color: {desc_color}; font-size: 0.85em;'>
        🔄 Animation shows last 4 hours of precipitation | 
        <span style='color: #667eea;'>Blue</span> = Light | 
        <span style='color: #00d4ff;'>Cyan</span> = Moderate | 
        <span style='color: #ff4444;'>Red</span> = Heavy
    </div>
    """, unsafe_allow_html=True)

def display_windy_radar(location, temperature_f=None):
    """Display interactive weather radar using Windy.com embedded map."""
    
    lat = location['latitude']
    lon = location['longitude']
    
    # Use Windy.com's embedded iframe (free - no API key required!)
    windy_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; background: #1e1e2d; }}
            #windy-container {{ 
                height: 520px; 
                width: 100%; 
                border-radius: 15px;
                overflow: hidden;
                border: 2px solid rgba(100, 100, 150, 0.3);
            }}
            iframe {{
                width: 100%;
                height: 100%;
                border: none;
            }}
        </style>
    </head>
    <body>
        <div id="windy-container">
            <iframe 
                src="https://embed.windy.com/embed2.html?lat={lat}&lon={lon}&detailLat={lat}&detailLon={lon}&width=100%&height=520&zoom=8&level=surface&overlay=radar&product=ecmwf&menu=&message=true&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=default&metricTemp=default&radarRange=-1"
                frameborder="0">
            </iframe>
        </div>
    </body>
    </html>
    """
    
    # Display the embedded Windy map
    components.html(windy_html, height=540)
    
    # Dynamic description color based on temperature
    desc_color = "#263238" if temperature_f is not None and 76 <= temperature_f <= 95 else "#888"
    st.markdown(f"""
    <div style='text-align: center; margin-top: 10px; color: {desc_color}; font-size: 0.85em;'>
        🌬️ Powered by <span style='color: #667eea;'>Windy.com</span> - Full interactive weather map<br>
        Use controls to change layers: Radar, Wind, Temperature, Clouds, Satellite & more
    </div>
    """, unsafe_allow_html=True)

def display_weather_alerts(alerts):
    """Display weather alerts with appropriate styling based on severity."""
    if not alerts:
        return
    
    # Sort by severity (most severe first)
    severity_order = {'Extreme': 0, 'Severe': 1, 'Moderate': 2, 'Minor': 3, 'Unknown': 4}
    sorted_alerts = sorted(alerts, key=lambda x: severity_order.get(x['severity'], 4))
    
    for alert in sorted_alerts:
        # Determine color scheme based on severity
        if alert['severity'] == 'Extreme':
            bg_color = '#8B0000'  # Dark red
            border_color = '#FF0000'
            icon = '🚨'
            text_color = '#FFFFFF'
        elif alert['severity'] == 'Severe':
            bg_color = '#FF4500'  # Orange red
            border_color = '#FF6347'
            icon = '🔥'
            text_color = '#FFFFFF'
        elif alert['severity'] == 'Moderate':
            bg_color = '#FFA500'  # Orange
            border_color = '#FFB84D'
            icon = '⚠️'
            text_color = '#FFFFFF'
        elif alert['severity'] == 'Minor':
            bg_color = '#4682B4'  # Steel blue
            border_color = '#87CEEB'
            icon = 'ℹ️'
            text_color = '#FFFFFF'
        else:  # Unknown
            bg_color = '#808080'  # Gray
            border_color = '#A9A9A9'
            icon = '❓'
            text_color = '#FFFFFF'
        
        # Create alert card
        alert_html = f"""
        <div style='background-color: {bg_color}; border-left: 5px solid {border_color}; padding: 15px; margin-bottom: 15px; border-radius: 5px;'>
            <h3 style='color: {text_color}; margin: 0 0 10px 0;'>{icon} {alert['event']}</h3>
            <p style='color: {text_color}; margin: 5px 0;'><strong>Severity:</strong> {alert['severity']}</p>
            <p style='color: {text_color}; margin: 5px 0;'><strong>Start:</strong> {alert['start']}</p>
            <p style='color: {text_color}; margin: 5px 0;'><strong>End:</strong> {alert['end']}</p>
            <p style='color: {text_color}; margin: 5px 0;'><strong>Description:</strong> {alert['description']}</p>
        </div>
        """
        st.markdown(alert_html, unsafe_allow_html=True)

def display_weather_alerts(alerts):
    """Display weather alerts with appropriate styling based on severity."""
    if not alerts:
        return
    
    # Sort by severity (most severe first)
    severity_order = {'Extreme': 0, 'Severe': 1, 'Moderate': 2, 'Minor': 3, 'Unknown': 4}
    sorted_alerts = sorted(alerts, key=lambda x: severity_order.get(x['severity'], 4))
    
    for alert in sorted_alerts:
        # Determine color scheme based on severity
        if alert['severity'] == 'Extreme':
            bg_color = '#8B0000'  # Dark red
            border_color = '#FF0000'
            icon = '🚨'
            text_color = '#FFFFFF'
        elif alert['severity'] == 'Severe':
            bg_color = '#FF4500'  # Orange red
            border_color = '#FF6347'
            icon = '⚠️'
            text_color = '#FFFFFF'
        elif alert['severity'] == 'Moderate':
            bg_color = '#FFA500'  # Orange
            border_color = '#FFD700'
            icon = '⚠️'
            text_color = '#000000'
        else:  # Minor or Unknown
            bg_color = '#4682B4'  # Steel blue
            border_color = '#87CEEB'
            icon = 'ℹ️'
            text_color = '#FFFFFF'
        
        # Format times if available
        onset_text = ''
        if alert['onset']:
            try:
                onset_dt = datetime.fromisoformat(alert['onset'].replace('Z', '+00:00'))
                onset_text = f"<div style='font-size: 12px; opacity: 0.9; margin-top: 5px;'>⏰ Effective: {onset_dt.strftime('%b %d, %I:%M %p')}</div>"
            except:
                pass
        
        expires_text = ''
        if alert['expires']:
            try:
                expires_dt = datetime.fromisoformat(alert['expires'].replace('Z', '+00:00'))
                expires_text = f"<div style='font-size: 12px; opacity: 0.9;'>⏱️ Expires: {expires_dt.strftime('%b %d, %I:%M %p')}</div>"
            except:
                pass
        
        # Create alert box
        st.markdown(f"""
        <div style='background: {bg_color}; 
                    border-left: 5px solid {border_color}; 
                    padding: 15px; 
                    border-radius: 10px; 
                    margin: 15px 0; 
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
                    color: {text_color};'>
            <div style='font-size: 24px; margin-bottom: 8px;'>{icon} <strong>{alert['event']}</strong></div>
            <div style='font-size: 14px; opacity: 0.95; margin-bottom: 8px;'>{alert['headline']}</div>
            {onset_text}
            {expires_text}
            <div style='margin-top: 10px; font-size: 13px; line-height: 1.5;'>{alert['description']}</div>
        </div>
        """, unsafe_allow_html=True)

def display_weather_alerts(alerts):
    """Display weather alerts with appropriate styling based on severity."""
    if not alerts:
        return
    
    # Sort by severity (most severe first)
    severity_order = {'Extreme': 0, 'Severe': 1, 'Moderate': 2, 'Minor': 3, 'Unknown': 4}
    sorted_alerts = sorted(alerts, key=lambda x: severity_order.get(x['severity'], 4))
    
    for alert in sorted_alerts:
        # Determine color scheme based on severity
        if alert['severity'] == 'Extreme':
            bg_color = '#8B0000'  # Dark red
            border_color = '#FF0000'
            icon = '🚨'
            text_color = '#FFFFFF'
        elif alert['severity'] == 'Severe':
            bg_color = '#FF4500'  # Orange red
            border_color = '#FF6347'
            icon = '⚠️'
            text_color = '#FFFFFF'
        elif alert['severity'] == 'Moderate':
            bg_color = '#FFA500'  # Orange
            border_color = '#FFD700'
            icon = '⚠️'
            text_color = '#000000'
        else:  # Minor or Unknown
            bg_color = '#4682B4'  # Steel blue
            border_color = '#87CEEB'
            icon = 'ℹ️'
            text_color = '#FFFFFF'
        
        # Format times if available
        onset_text = ''
        if alert['onset']:
            try:
                onset_dt = datetime.fromisoformat(alert['onset'].replace('Z', '+00:00'))
                onset_text = f"<div style='font-size: 12px; opacity: 0.9; margin-top: 5px;'>⏰ Effective: {onset_dt.strftime('%b %d, %I:%M %p')}</div>"
            except:
                pass
        
        expires_text = ''
        if alert['expires']:
            try:
                expires_dt = datetime.fromisoformat(alert['expires'].replace('Z', '+00:00'))
                expires_text = f"<div style='font-size: 12px; opacity: 0.9;'>⏱️ Expires: {expires_dt.strftime('%b %d, %I:%M %p')}</div>"
            except:
                pass
        
        # Create alert box
        st.markdown(f"""
        <div style='background: {bg_color}; 
                    border-left: 5px solid {border_color}; 
                    padding: 15px; 
                    border-radius: 10px; 
                    margin: 15px 0; 
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
                    color: {text_color};'>
            <div style='font-size: 24px; margin-bottom: 8px;'>{icon} <strong>{alert['event']}</strong></div>
            <div style='font-size: 14px; opacity: 0.95; margin-bottom: 8px;'>{alert['headline']}</div>
            {onset_text}
            {expires_text}
            <div style='font-size: 11px; opacity: 0.8; margin-top: 8px;'>📍 {alert['areas']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show detailed information in an expander
        with st.expander(f"📋 Details: {alert['event']}", expanded=False):
            if alert['description']:
                st.markdown(f"**Description:**\n\n{alert['description']}")
            
            if alert['instruction']:
                st.markdown(f"**⚡ What To Do:**\n\n{alert['instruction']}")
            
            st.markdown(f"""
            ---
            **Alert Details:**
            - **Severity:** {alert['severity']}
            - **Urgency:** {alert['urgency']}
            - **Certainty:** {alert['certainty']}
            - **Recommended Action:** {alert['response']}
            - **Issued By:** {alert['sender_name']}
            """)

def display_weather(location, weather_data, model_key='default'):
    """Display weather information.
    
    Args:
        location: Location dictionary
        weather_data: Weather data from API
        model_key: Unique key for this model instance (prevents widget ID conflicts in tabs)
    """
    current = weather_data.get('current', {})
    temperature = current.get('temperature_2m')
    humidity = current.get('relative_humidity_2m')
    wind_speed = current.get('wind_speed_10m')
    weather_code = current.get('weather_code')
    current_time = current.get('time')  # Get current time from API
    conditions = get_weather_description(weather_code)
    emoji = get_weather_emoji(conditions, current_time)  # Pass time for night/day detection
    
    # Location header
    # Determine text color based on temperature
    if temperature is not None and 76 <= temperature <= 95:
        location_text_color = "#263238"  # Dark gray for warm backgrounds
    else:
        location_text_color = "#aaa"  # Light gray for cool backgrounds
    
    st.markdown(f"<h1 style='text-align: center; color: #e0e0e0; margin-bottom: 5px; margin-top: 0px;'>{location['city']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: {location_text_color}; margin-top: 0px; margin-bottom: 10px;'>{location['region']}, {location['country']}</p>", unsafe_allow_html=True)
    
    # Weather Alerts (NWS for US locations)
    # Check for US location using multiple possible country name formats
    country = location.get('country', '').lower()
    is_us_location = any(us_name in country for us_name in ['united states', 'usa', 'us'])
    
    if is_us_location or country == 'united states':
        alerts = get_weather_alerts(location['latitude'], location['longitude'])
        if alerts:
            st.markdown("<br>", unsafe_allow_html=True)
            display_weather_alerts(alerts)
            st.markdown("<br>", unsafe_allow_html=True)
    
    # Apply temperature-based background color
    if temperature is not None:
        apply_temp_background(temperature)
    
    # Weather icon
    st.markdown(f"<div class='weather-icon'>{emoji}</div>", unsafe_allow_html=True)
    
    # Temperature display
    if st.session_state.unit_temp == 'F':
        temp_display = f"{temperature:.1f}°F"
    else:
        temp_c = convert_temp(temperature, to_celsius=True)
        temp_display = f"{temp_c:.1f}°C"
    
    st.markdown(f"<div class='temperature'>{temp_display}</div>", unsafe_allow_html=True)
    
    # Conditions
    st.markdown(f"<h3 style='text-align: center; color: #bbb; margin-top: 10px; margin-bottom: 20px;'>{conditions}</h3>", unsafe_allow_html=True)
    
    # Sun times display (sunrise, sunset, first/last light)
    display_sun_times(weather_data, temperature)
    
    # Daily Outlook - Visual Crossing API disabled (not needed)
    # outlook = get_visual_crossing_outlook(location['latitude'], location['longitude'])
    # Daily outlook feature disabled to simplify app
    
    # 🌐 AI Weather Overview (Groq - Ultra Fast!)
    with st.expander("⚡ AI Weather Overview (Groq)", expanded=False):
        mode = st.selectbox(
            "Overview mode",
            ["AI Overview (Current Format)", "AI Overview (Narrative Format)", "Local Detailed (no AI)"], 
            key=f"overview_mode_select_{model_key}"
        )
        if weather_data.get('hourly'):
            hourly = weather_data['hourly']
            # Determine start_idx similar to hourly forecast logic
            all_times = hourly.get('time', [])
            start_idx = 0
            if all_times:
                try:
                    # Use location timezone if available
                    tzname = weather_data.get('timezone', 'UTC')
                    # Fallback to naive matching: find the first time >= now
                    now_iso = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0).isoformat(timespec='minutes')
                    for i, t in enumerate(all_times):
                        if t >= now_iso:
                            start_idx = i
                            break
                except Exception:
                    start_idx = 0
            hourly_slice = build_hourly_summary(hourly, start_idx, hours_to_show=48)
            if st.button("Generate Overview", key=f"overview_{model_key}"):
                with st.spinner("⚡ Generating AI weather overview with Groq (ultra-fast!)..."):
                    if mode == "AI Overview (Current Format)":
                        # Pass current unit preferences
                        ai_result = generate_ai_overview(location, hourly_slice, st.session_state.unit_temp, st.session_state.unit_wind)
                        ai_text = ai_result.get('text', 'Error generating overview')
                        
                        # Display 48-hour detailed timeline as table FIRST
                        st.markdown("### 📅 48-Hour Detailed Timeline")
                        
                        # Build table from hourly data
                        timeline_data = []
                        for idx, h in enumerate(hourly_slice[:48]):
                            temp_f = h.get('temp_f')
                            if temp_f is None:
                                continue
                            
                            # Convert based on unit preference
                            if st.session_state.unit_temp == 'C':
                                temp_display = f"{int(convert_temp(temp_f, to_celsius=True))}°C"
                            else:
                                temp_display = f"{int(temp_f)}°F"
                            
                            wind_mph = h.get('wind_speed', 0)
                            if st.session_state.unit_wind == 'kmh':
                                wind_display = f"{int(convert_wind(wind_mph, to_kmh=True))} km/h"
                            else:
                                wind_display = f"{int(wind_mph)} mph"
                            
                            time_str = h.get('time', '')
                            # Format time nicely (show just hour)
                            try:
                                from datetime import datetime as dt_parse
                                dt_obj = dt_parse.fromisoformat(time_str.replace('Z', '+00:00'))
                                time_display = dt_obj.strftime('%a %I %p')  # e.g., "Mon 3 PM"
                            except:
                                time_display = time_str[-5:] if len(time_str) > 5 else time_str
                            
                            timeline_data.append({
                                'Time': time_display,
                                'Temp': temp_display,
                                'Conditions': get_weather_description(h.get('weather_code', 0)),
                                'Precip %': f"{h.get('precip_prob', 0)}%",
                                'Precip mm': f"{h.get('precip_mm', 0):.1f}",
                                'Wind': wind_display,
                                'Humidity': f"{h.get('humidity', 0)}%"
                            })
                        
                        import pandas as pd
                        timeline_df = pd.DataFrame(timeline_data)
                        
                        # Display as interactive table
                        st.dataframe(timeline_df, use_container_width=True, height=400)
                        
                        st.markdown("---")
                        
                        # Display the AI overview with proper markdown rendering
                        st.markdown(ai_text)
                        
                        st.markdown("---")
                        
                        # Build CSV download from the same table data
                        csv_data = timeline_df.to_csv(index=False)
                        
                        # Generate filename with location and timestamp
                        from datetime import datetime as dt
                        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
                        city_clean = location.get('city', 'Unknown').replace(' ', '_').replace(',', '')
                        region_clean = location.get('region', '').replace(' ', '_').replace(',', '')
                        filename = f"Weather_{city_clean}_{region_clean}_{timestamp}.csv"
                        
                        # Add download button
                        st.download_button(
                            label="📥 Download 48-Hour Forecast (CSV)",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv",
                            key=f"download_forecast_{model_key}"
                        )
                        
                        # Show debug information in expander
                        with st.expander("🛠️ View Prompts & Raw Response", expanded=False):
                            if ai_result.get('system_prompt'):
                                st.markdown("**System Prompt:**")
                                st.code(ai_result['system_prompt'], language="text")
                            
                            if ai_result.get('prompt'):
                                st.markdown("**User Prompt:**")
                                st.code(ai_result['prompt'], language="text")
                            
                            if ai_result.get('raw_response'):
                                st.markdown("**Raw JSON Response:**")
                                st.code(ai_result['raw_response'], language="json")
                    
                    elif mode == "AI Overview (Narrative Format)":
                        # Use narrative format with day-by-day breakdown
                        ai_result = generate_ai_overview_narrative(location, hourly_slice, st.session_state.unit_temp, st.session_state.unit_wind)
                        ai_text = ai_result.get('text', 'Error generating overview')
                        
                        # Display the narrative AI overview
                        st.markdown(ai_text)
                        
                        st.markdown("---")
                        
                        # Build table from hourly data for download
                        table_data = []
                        for h in hourly_slice[:48]:
                            temp_f = h.get('temp_f')
                            if temp_f is None:
                                continue
                            
                            # Convert based on unit preference
                            if st.session_state.unit_temp == 'C':
                                temp_display = f"{int(convert_temp(temp_f, to_celsius=True))}°C"
                            else:
                                temp_display = f"{int(temp_f)}°F"
                            
                            wind_mph = h.get('wind_speed', 0)
                            if st.session_state.unit_wind == 'kmh':
                                wind_display = f"{int(convert_wind(wind_mph, to_kmh=True))} km/h"
                            else:
                                wind_display = f"{int(wind_mph)} mph"
                            
                            table_data.append({
                                'Time': h.get('time', ''),
                                'Temperature': temp_display,
                                'Conditions': get_weather_description(h.get('weather_code', 0)),
                                'Precipitation Probability': f"{h.get('precip_prob', 0)}%",
                                'Precipitation Amount': f"{h.get('precip_mm', 0):.1f} mm",
                                'Wind Speed': wind_display,
                                'Humidity': f"{h.get('humidity', 0)}%"
                            })
                        
                        import pandas as pd
                        from datetime import datetime as dt
                        
                        df = pd.DataFrame(table_data)
                        
                        # Generate filename with location and timestamp
                        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
                        city_clean = location.get('city', 'Unknown').replace(' ', '_').replace(',', '')
                        region_clean = location.get('region', '').replace(' ', '_').replace(',', '')
                        filename = f"Weather_{city_clean}_{region_clean}_{timestamp}.csv"
                        
                        # Convert to CSV
                        csv_data = df.to_csv(index=False)
                        
                        # Add download button
                        st.download_button(
                            label="📥 Download 48-Hour Forecast (CSV)",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv",
                            key=f"download_forecast_narrative_{model_key}"
                        )
                        
                        # Show debug information in expander
                        with st.expander("🛠️ View Prompts & Raw Response", expanded=False):
                            if ai_result.get('system_prompt'):
                                st.markdown("**System Prompt:**")
                                st.code(ai_result['system_prompt'], language="text")
                            
                            if ai_result.get('prompt'):
                                st.markdown("**User Prompt:**")
                                st.code(ai_result['prompt'], language="text")
                            
                            if ai_result.get('raw_response'):
                                st.markdown("**Raw JSON Response:**")
                                st.code(ai_result['raw_response'], language="json")
                    else:
                        # Local detailed overview without AI
                        def _local_only(location, slice_):
                            if not slice_:
                                return "Local overview unavailable: missing hourly data."
                            city = location.get('city', 'Unknown')
                            region = location.get('region', '')
                            country = location.get('country', '')
                            window = slice_[:24]
                            temps = [h.get('temp_f') for h in window if h.get('temp_f') is not None]
                            t0 = temps[0] if temps else None
                            tmin = min(temps) if temps else None
                            tmax = max(temps) if temps else None
                            precip_hours = []
                            from datetime import datetime
                            for h in window:
                                prob = h.get('precip_prob') or 0
                                amt = h.get('precip_mm') or 0.0
                                if prob >= 25 or amt >= 0.5:
                                    try:
                                        dt = datetime.fromisoformat(h.get('time').replace('Z','+00:00'))
                                        label = dt.strftime('%-I %p')
                                    except Exception:
                                        label = h.get('time')
                                    precip_hours.append(f"{label} ({int(prob)}% / {round(amt,2)} mm)")
                            total_mm = round(sum([(h.get('precip_mm') or 0.0) for h in window]), 2)
                            pmax = int(max([(h.get('precip_prob') or 0) for h in window]))
                            lines = []
                            lines.append(f"Detailed overview for {city}, {region}, {country}:")
                            if t0 is not None:
                                lines.append(f"- Temps: start ~{t0}°F; range {tmin}–{tmax}°F today.")
                            else:
                                lines.append("- Temps: data unavailable.")
                            lines.append(f"- Precipitation: max chance ~{pmax}%; total ~{total_mm} mm over the day.")
                            if precip_hours:
                                lines.append("- Likely precip hours: " + ", ".join(precip_hours[:12]) + ("…" if len(precip_hours) > 12 else ""))
                            else:
                                lines.append("- No significant precipitation expected based on current data.")
                            return "\n".join(lines)
                        ai_text = _local_only(location, hourly_slice)
                        st.markdown(f"<div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); color:#e0e0e0;'>{ai_text}</div>", unsafe_allow_html=True)
        else:
            st.write("Hourly data unavailable.")
    
    # 💬 AI Weather Chatbot
    with st.expander("💬 AI Weather Chatbot", expanded=False):
        st.markdown("<p style='color: #888; font-size: 0.9em;'>Ask me anything about current conditions and the 2-day forecast!</p>", unsafe_allow_html=True)
        
        # Create weather context for chatbot
        if weather_data:
            current = weather_data.get('current', {})
            temp = current.get('temperature_2m', 'N/A')
            humidity = current.get('relative_humidity_2m', 'N/A')
            wind = current.get('wind_speed_10m', 'N/A')
            weather_code = current.get('weather_code', 0)
            conditions = get_weather_description(weather_code)
            
            city = location.get('city', 'Unknown')
            region = location.get('region', '')
            
            # Add hourly forecast data for 2-day context (similar to AI overview)
            hourly = weather_data.get('hourly', {})
            hourly_temps = hourly.get('temperature_2m', [])[:48] if hourly else []
            hourly_precip = hourly.get('precipitation_probability', [])[:48] if hourly else []
            
            # Get user's unit preferences
            temp_unit = st.session_state.unit_temp
            wind_unit = st.session_state.unit_wind
            
            # Convert current weather based on user preference
            if temp_unit == 'C':
                display_temp = int(convert_temp(temp, to_celsius=True)) if isinstance(temp, (int, float)) else temp
                temp_symbol = '°C'
            else:
                display_temp = int(temp) if isinstance(temp, (int, float)) else temp
                temp_symbol = '°F'
            
            if wind_unit == 'kmh':
                display_wind = int(convert_wind(wind, to_kmh=True)) if isinstance(wind, (int, float)) else wind
                wind_symbol = 'km/h'
            else:
                display_wind = int(wind) if isinstance(wind, (int, float)) else wind
                wind_symbol = 'mph'
            
            # Calculate 2-day forecast summary with proper unit conversion
            if hourly_temps and hourly_precip:
                day1_temps = [t for t in hourly_temps[:24] if t is not None]
                day2_temps = [t for t in hourly_temps[24:48] if t is not None]
                day1_precip = [p for p in hourly_precip[:24] if p is not None]
                day2_precip = [p for p in hourly_precip[24:48] if p is not None]
                
                # Convert forecast temps based on user preference (API returns Fahrenheit)
                if temp_unit == 'C':
                    day1_high = int(convert_temp(max(day1_temps), to_celsius=True)) if day1_temps else 'N/A'
                    day1_low = int(convert_temp(min(day1_temps), to_celsius=True)) if day1_temps else 'N/A'
                    day2_high = int(convert_temp(max(day2_temps), to_celsius=True)) if day2_temps else 'N/A'
                    day2_low = int(convert_temp(min(day2_temps), to_celsius=True)) if day2_temps else 'N/A'
                else:
                    day1_high = int(max(day1_temps)) if day1_temps else 'N/A'
                    day1_low = int(min(day1_temps)) if day1_temps else 'N/A'
                    day2_high = int(max(day2_temps)) if day2_temps else 'N/A'
                    day2_low = int(min(day2_temps)) if day2_temps else 'N/A'
                
                day1_precip_max = int(max(day1_precip)) if day1_precip else 0
                day2_precip_max = int(max(day2_precip)) if day2_precip else 0
                
                forecast_summary = f"""

2-Day Forecast:
- Day 1: High {day1_high}{temp_symbol}, Low {day1_low}{temp_symbol}, {day1_precip_max}% rain chance
- Day 2: High {day2_high}{temp_symbol}, Low {day2_low}{temp_symbol}, {day2_precip_max}% rain chance"""
            else:
                forecast_summary = ""
            
            weather_context = f"""Current Weather for {city}, {region}:
- Temperature: {display_temp}{temp_symbol}
- Conditions: {conditions}
- Humidity: {humidity}%
- Wind Speed: {display_wind} {wind_symbol}{forecast_summary}

You can answer questions about current conditions and the 2-day forecast. Be conversational and helpful."""
            
            # Display chat history
            for message in st.session_state.chat_history:
                role = message["role"]
                content = message["content"]
                
                if role == "user":
                    st.chat_message("user").markdown(content)
                else:
                    st.chat_message("assistant").markdown(content)
            
            # Chat input
            if user_input := st.chat_input("Ask about the weather...", key=f"chat_input_{model_key}"):
                # Display user message
                st.chat_message("user").markdown(user_input)
                
                # Add to chat history
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # Get AI response with debug data
                with st.spinner("Thinking..."):
                    ai_result = chat_with_weather_ai(user_input, weather_context)
                
                ai_text = ai_result.get('text', 'Error generating response')
                
                # Display AI response
                st.chat_message("assistant").markdown(ai_text)
                
                # Add to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
                
                # Store debug data in session state for the last interaction
                st.session_state.last_chat_debug = ai_result
            
            # Show debug information for last interaction
            if 'last_chat_debug' in st.session_state and st.session_state.last_chat_debug:
                with st.expander("🛠️ View Last Chat Prompts & Raw Response", expanded=False):
                    debug_data = st.session_state.last_chat_debug
                    
                    if debug_data.get('system_prompt'):
                        st.markdown("**System Prompt:**")
                        st.code(debug_data['system_prompt'], language="text")
                    
                    if debug_data.get('user_prompt'):
                        st.markdown("**User Prompt:**")
                        st.code(debug_data['user_prompt'], language="text")
                    
                    if debug_data.get('raw_response'):
                        st.markdown("**Raw JSON Response:**")
                        st.code(debug_data['raw_response'], language="json")
            
            # Clear chat button
            if st.button("Clear Chat History", key=f"clear_chat_{model_key}"):
                st.session_state.chat_history = []
                if 'last_chat_debug' in st.session_state:
                    del st.session_state.last_chat_debug
                st.rerun()
        else:
            st.write("Weather data unavailable for chat.")
    
    # ✈️ AI Travel Weather Compare
    with st.expander("✈️ AI Travel Weather Compare", expanded=False):
        st.markdown("<p style='color: #888; font-size: 0.9em;'>Compare weather at your destination with your current location!</p>", unsafe_allow_html=True)
        
        # Function to handle comparison when Enter is pressed
        def handle_travel_compare():
            if st.session_state.get(f"destination_input_{model_key}"):
                st.session_state[f'trigger_compare_{model_key}'] = True
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            destination_input = st.text_input(
                "Enter travel destination (city, country or city, state)",
                placeholder="e.g., Paris, France or Miami, FL",
                key=f"destination_input_{model_key}",
                on_change=handle_travel_compare
            )
        
        with col2:
            compare_btn = st.button("Compare Weather", key=f"compare_btn_{model_key}")
        
        # Trigger comparison on button click or Enter key
        if (compare_btn or st.session_state.get(f'trigger_compare_{model_key}', False)) and destination_input:
            if st.session_state.get(f'trigger_compare_{model_key}'):
                st.session_state[f'trigger_compare_{model_key}'] = False  # Reset trigger
            with st.spinner(f"Fetching weather for {destination_input}..."):
                # Get destination coordinates
                dest_results = get_location_by_name(destination_input)
                
                if dest_results:
                    dest_location = {
                        'latitude': dest_results[0]['latitude'],
                        'longitude': dest_results[0]['longitude'],
                        'city': dest_results[0].get('name'),
                        'region': dest_results[0].get('admin1', ''),
                        'country': dest_results[0].get('country')
                    }
                    
                    # Get destination weather
                    dest_weather = get_weather(dest_location['latitude'], dest_location['longitude'])
                    
                    if dest_weather:
                        # Generate AI comparison
                        with st.spinner("Generating travel weather comparison..."):
                            comparison = compare_travel_weather(
                                location, weather_data,
                                dest_location, dest_weather,
                                st.session_state.unit_temp, st.session_state.unit_wind
                            )
                            
                            # Display comparison table
                            if comparison.get('table_data'):
                                import pandas as pd
                                df = pd.DataFrame(comparison['table_data'])
                                
                                st.markdown("### 📊 Weather Comparison")
                                st.dataframe(
                                    df,
                                    use_container_width=True,
                                    hide_index=True
                                )
                            
                            # Display AI insights
                            if comparison.get('ai_insights'):
                                st.markdown("### 💡 Travel Insights & Recommendations")
                                st.markdown(comparison.get('ai_insights'))
                            
                            # Create downloadable report
                            import pandas as pd
                            from datetime import datetime as dt
                            
                            # Generate filename with both locations and timestamp
                            timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
                            current_city = location.get('city', 'Current').replace(' ', '_').replace(',', '')
                            dest_city = dest_location.get('city', 'Destination').replace(' ', '_').replace(',', '')
                            filename = f"Travel_Compare_{current_city}_vs_{dest_city}_{timestamp}.txt"
                            
                            # Build comprehensive report content
                            report_lines = []
                            report_lines.append("=" * 80)
                            report_lines.append("TRAVEL WEATHER COMPARISON REPORT")
                            report_lines.append("=" * 80)
                            report_lines.append(f"Generated: {dt.now().strftime('%B %d, %Y at %I:%M %p')}")
                            report_lines.append("")
                            
                            # Location information
                            report_lines.append("LOCATIONS:")
                            report_lines.append(f"  Current: {location.get('city')}, {location.get('region')}, {location.get('country')}")
                            report_lines.append(f"  Destination: {dest_location.get('city')}, {dest_location.get('region')}, {dest_location.get('country')}")
                            report_lines.append("")
                            report_lines.append("=" * 80)
                            
                            # Add comparison table
                            if comparison.get('table_data'):
                                report_lines.append("WEATHER COMPARISON TABLE")
                                report_lines.append("=" * 80)
                                report_lines.append("")
                                
                                df = pd.DataFrame(comparison['table_data'])
                                # Convert DataFrame to formatted text table
                                table_str = df.to_string(index=False)
                                report_lines.append(table_str)
                                report_lines.append("")
                                report_lines.append("=" * 80)
                            
                            # Add AI insights
                            if comparison.get('ai_insights'):
                                report_lines.append("TRAVEL INSIGHTS & RECOMMENDATIONS")
                                report_lines.append("=" * 80)
                                report_lines.append("")
                                # Remove HTML/markdown formatting for plain text
                                insights_text = comparison.get('ai_insights', '').replace('**', '').replace('##', '').replace('#', '')
                                report_lines.append(insights_text)
                                report_lines.append("")
                                report_lines.append("=" * 80)
                            
                            # Footer
                            report_lines.append("")
                            report_lines.append("Report generated by Matt's Weather App")
                            report_lines.append("Powered by Open-Meteo API and Groq AI")
                            report_lines.append("")
                            
                            report_content = "\n".join(report_lines)
                            
                            # Add download button
                            st.download_button(
                                label="📥 Download Travel Comparison Report",
                                data=report_content,
                                file_name=filename,
                                mime="text/plain",
                                key=f"download_travel_{model_key}"
                            )
                            
                            # Show debug information
                            with st.expander("🛠️ View Comparison Prompts & Raw Response", expanded=False):
                                if comparison.get('system_prompt'):
                                    st.markdown("**System Prompt:**")
                                    st.code(comparison['system_prompt'], language="text")
                                
                                if comparison.get('prompt'):
                                    st.markdown("**User Prompt:**")
                                    st.code(comparison['prompt'], language="text")
                                
                                if comparison.get('raw_response'):
                                    st.markdown("**Raw JSON Response:**")
                                    st.code(comparison['raw_response'], language="json")
                    else:
                        st.error(f"Could not fetch weather data for {destination_input}")
                else:
                    st.error(f"Could not find location: {destination_input}")

    # Check for upcoming precipitation
    precip_alert = check_precipitation_soon(weather_data)
    
    # Debug: Show precipitation forecast data (you can remove this later)
    if weather_data.get('hourly'):
        with st.expander("🔍 Debug: Precipitation Forecast (next 12 hours)", expanded=False):
            hourly = weather_data['hourly']
            if 'precipitation_probability' in hourly:
                # Find current hour index using timezone-aware comparison
                all_times = hourly.get('time', [])
                start_idx = 0
                
                if all_times:
                    try:
                        # Get the timezone from the API response
                        api_timezone = weather_data.get('timezone', 'UTC')
                        
                        try:
                            from zoneinfo import ZoneInfo
                            tz = ZoneInfo(api_timezone)
                            now_local = datetime.now(tz).replace(minute=0, second=0, microsecond=0)
                            
                            for i, time_str in enumerate(all_times):
                                dt_naive = datetime.fromisoformat(time_str)
                                dt_aware = dt_naive.replace(tzinfo=tz)
                                
                                if dt_aware >= now_local:
                                    start_idx = i
                                    break
                                    
                        except ImportError:
                            # Fallback without zoneinfo
                            for i, time_str in enumerate(all_times):
                                dt_naive = datetime.fromisoformat(time_str)
                                if i == 0 or dt_naive.hour >= datetime.now().hour:
                                    start_idx = i
                                    break
                    except:
                        start_idx = 0
                
                # Get next 12 hours starting from current hour
                probs = hourly['precipitation_probability'][start_idx:start_idx+12]
                times = all_times[start_idx:start_idx+12]
                
                st.write("**Precipitation Probabilities:**")
                for i, (time_str, prob) in enumerate(zip(times, probs)):
                    # Show all hours, even if probability is 0 or None
                    try:
                        dt = datetime.fromisoformat(time_str)
                        time_only = dt.strftime("%I:%M %p")  # Format as 12-hour time
                    except:
                        time_only = time_str.split('T')[1] if 'T' in time_str else time_str
                    
                    # Display probability, defaulting to 0% if None
                    prob_display = f"{prob}%" if prob is not None else "0%"
                    st.write(f"- {time_only}: {prob_display}")
    
    # Debug: Weather Alerts Status
    country = location.get('country', '').lower()
    is_us_location = any(us_name in country for us_name in ['united states', 'usa', 'us'])
    
    with st.expander("🚨 Debug: Weather Alerts Status", expanded=False):
        st.write(f"**Location Country:** {location.get('country')}")
        st.write(f"**Is US Location:** {is_us_location}")
        st.write(f"**Coordinates:** {location['latitude']}, {location['longitude']}")
        
        if is_us_location:
            st.write("**Checking NWS for alerts...**")
            test_alerts = get_weather_alerts(location['latitude'], location['longitude'])
            if test_alerts:
                st.success(f"✅ Found {len(test_alerts)} active alert(s)!")
                for alert in test_alerts:
                    st.write(f"- {alert['event']} ({alert['severity']})")
            else:
                st.info("ℹ️ No active weather alerts for this location.")
                st.write("This is good news - no severe weather expected!")
        else:
            st.warning("⚠️ Weather alerts only available for US locations.")
            st.write("NWS API only covers United States and territories.")

    
    if precip_alert:
        minutes = precip_alert['minutes']
        prob = precip_alert['probability']
        precip_type = precip_alert['type']
        precip_emoji = precip_alert['emoji']
        color_start = precip_alert['color_start']
        color_end = precip_alert['color_end']
        
        if minutes < 60:
            time_str = f"{minutes} minutes"
        else:
            hours = minutes // 60
            time_str = f"{hours} hour{'s' if hours > 1 else ''}"
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {color_start} 0%, {color_end} 100%); 
                    padding: 15px; border-radius: 15px; text-align: center; 
                    margin: 20px auto; max-width: 500px; 
                    box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
                    animation: pulse 2s ease-in-out infinite;'>
            <div style='font-size: 32px; margin-bottom: 5px;'>{precip_emoji}</div>
            <div style='font-size: 18px; font-weight: bold; color: white;'>
                {precip_type} Expected in {time_str}
            </div>
            <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px;'>
                {prob}% probability
            </div>
        </div>
        <style>
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.02); }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    # Details cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class='detail-card'>
            <div style='font-size: 28px; margin-bottom: 5px;'>💧</div>
            <div style='font-size: 12px; opacity: 0.9; margin-bottom: 3px;'>Humidity</div>
            <div style='font-size: 22px; font-weight: bold;'>{humidity}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.session_state.unit_wind == 'mph':
            wind_display = f"{wind_speed:.1f} mph"
        else:
            wind_kmh = convert_wind(wind_speed, to_kmh=True)
            wind_display = f"{wind_kmh:.1f} km/h"
        
        st.markdown(f"""
        <div class='detail-card'>
            <div style='font-size: 28px; margin-bottom: 5px;'>💨</div>
            <div style='font-size: 12px; opacity: 0.9; margin-bottom: 3px;'>Wind Speed</div>
            <div style='font-size: 22px; font-weight: bold;'>{wind_display}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Hourly Forecast Section
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📅 Hourly Forecast")
    
    if weather_data.get('hourly'):
        hourly = weather_data['hourly']
        all_times = hourly.get('time', [])
        all_temps = hourly.get('temperature_2m', [])
        all_weather_codes = hourly.get('weather_code', [])
        all_precip_probs = hourly.get('precipitation_probability', [])
        
        
        # Find current hour index
        # The API with timezone='auto' returns times in the location's local timezone
        # We need to use the timezone info from the API response to find "now"
        start_idx = 0
        if all_times:
            try:
                # Get the timezone from the API response
                api_timezone = weather_data.get('timezone', 'UTC')
                
                # Try to use zoneinfo (Python 3.9+) or fall back to simpler comparison
                try:
                    from zoneinfo import ZoneInfo
                    tz = ZoneInfo(api_timezone)
                    now_local = datetime.now(tz).replace(minute=0, second=0, microsecond=0)
                    
                    # Find the first hour that is >= now in the local timezone
                    for i, time_str in enumerate(all_times):
                        # Parse as naive datetime (it's already in local TZ from API)
                        dt_naive = datetime.fromisoformat(time_str)
                        # Make it aware in the location's timezone
                        dt_aware = dt_naive.replace(tzinfo=tz)
                        
                        if dt_aware >= now_local:
                            start_idx = i
                            break
                            
                except ImportError:
                    # Fallback for systems without zoneinfo: use simple string comparison
                    # Since all times are in the same timezone, we can compare ISO strings
                    # Get current UTC time and convert offset if timezone is known
                    now_utc = datetime.now(timezone.utc)
                    
                    # Parse each time and compare
                    for i, time_str in enumerate(all_times):
                        dt_naive = datetime.fromisoformat(time_str)
                        # Rough comparison: if the date/hour looks current or future, use it
                        # This works because the API returns consecutive hours
                        if i == 0 or dt_naive.hour >= datetime.now().hour:
                            start_idx = i
                            break
                            
            except Exception as e:
                # Ultimate fallback: start from index 0
                start_idx = 0
        
        # Get 72 hours (3 days) starting from current hour
        hours_to_show = 72
        times = all_times[start_idx:start_idx+hours_to_show]
        temps = all_temps[start_idx:start_idx+hours_to_show] if all_temps else []
        weather_codes = all_weather_codes[start_idx:start_idx+hours_to_show] if all_weather_codes else []
        precip_probs = all_precip_probs[start_idx:start_idx+hours_to_show] if all_precip_probs else []
        
        # Get precipitation amounts (in mm from API)
        all_precip_amounts = hourly.get('precipitation', [])
        precip_amounts = all_precip_amounts[start_idx:start_idx+hours_to_show] if all_precip_amounts else []
        
        # Create scrollable horizontal forecast
        hourly_cards = []
        last_day = None  # Track day changes for labels
        
        for idx in range(len(times)):
            try:
                # Parse time (handles timezone from API response)
                dt = datetime.fromisoformat(times[idx])
                
                # Check if we've crossed into a new day
                current_day = dt.strftime("%A")  # Full day name (e.g., "Monday")
                show_day_label = (current_day != last_day)
                last_day = current_day
                
                # Show "Now" for first hour, day label for new days, otherwise time
                if idx == 0:
                    time_str = "Now"
                    day_label = ""
                elif show_day_label and idx > 0:
                    # Show day name for first hour of each new day
                    time_str = dt.strftime("%I%p").lstrip('0')  # "2PM" format
                    day_label = f"<div style='font-size: 10px; color: #888; margin-bottom: 2px;'>{current_day[:3]}</div>"  # "Mon"
                else:
                    time_str = dt.strftime("%I%p").lstrip('0')  # "2PM" format
                    day_label = ""
                
                # Get temperature
                if idx < len(temps):
                    temp = temps[idx]
                    if st.session_state.unit_temp == 'C':
                        temp = convert_temp(temp, to_celsius=True)
                        temp_str = f"{temp:.0f}°"
                    else:
                        temp_str = f"{temp:.0f}°"
                else:
                    temp_str = "N/A"
                
                # Get weather emoji (time-aware for night/day)
                weather_emoji = "🌤️"
                if idx < len(weather_codes):
                    w_desc = get_weather_description(weather_codes[idx])
                    # Pass the time string for night/day detection
                    time_for_emoji = times[idx] if idx < len(times) else None
                    weather_emoji = get_weather_emoji(w_desc, time_for_emoji)
                
                # Get precipitation probability and amount
                precip_str = ""
                prob_value = precip_probs[idx] if idx < len(precip_probs) and precip_probs[idx] is not None else 0
                
                # Get precipitation amount (convert from mm to inches if needed)
                precip_amount = 0
                if idx < len(precip_amounts) and precip_amounts[idx] is not None:
                    precip_amount = precip_amounts[idx]
                
                # API returns in mm, convert to inches: 1 mm = 0.0393701 inches
                precip_amount_in = precip_amount * 0.0393701
                
                # Always show probability, and show amount when probability > 0
                if prob_value > 0:
                    # Show probability and amount (even if 0.00")
                    precip_str = f"""<div style='font-size: 13px; color: #64b5f6; margin-top: 5px; line-height: 1.6;'>
                        💧 {prob_value:.0f}%<br>
                        <span style='font-size: 12px; color: #87CEEB; font-weight: 500;'>{precip_amount_in:.2f}"</span>
                    </div>"""
                else:
                    # No precipitation expected
                    precip_str = f"<div style='font-size: 13px; color: #64b5f6; margin-top: 5px;'>💧 {prob_value:.0f}%</div>"
                
                hourly_cards.append(f"""
                    <div style='background: rgba(30, 30, 45, 0.6); 
                                padding: 18px 15px 20px 15px; 
                                border-radius: 12px; 
                                text-align: center;
                                border: 1px solid rgba(100, 100, 150, 0.2);
                                min-width: 110px;
                                flex-shrink: 0;
                                margin-right: 12px;'>
                        {day_label}
                        <div style='font-size: 12px; color: #aaa; margin-bottom: 8px; font-weight: {"bold" if idx == 0 else "normal"};'>{time_str}</div>
                        <div style='font-size: 36px; margin: 10px 0;'>{weather_emoji}</div>
                        <div style='font-size: 22px; font-weight: bold; color: #e0e0e0; margin-bottom: 8px;'>{temp_str}</div>
                        {precip_str}
                    </div>
                """)
            except Exception as e:
                continue
        
        # Display scrollable container using components.html for proper rendering
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ 
                    margin: 0; 
                    padding: 0; 
                    background: transparent;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }}
                .hourly-container {{
                    overflow-x: auto; 
                    display: flex; 
                    padding: 10px 0;
                    scrollbar-width: thin;
                    scrollbar-color: rgba(100, 100, 150, 0.5) rgba(30, 30, 45, 0.3);
                }}
                .hourly-container::-webkit-scrollbar {{
                    height: 8px;
                }}
                .hourly-container::-webkit-scrollbar-track {{
                    background: rgba(30, 30, 45, 0.3);
                    border-radius: 10px;
                }}
                .hourly-container::-webkit-scrollbar-thumb {{
                    background: rgba(100, 100, 150, 0.5);
                    border-radius: 10px;
                }}
                .hourly-container::-webkit-scrollbar-thumb:hover {{
                    background: rgba(100, 100, 150, 0.7);
                }}
            </style>
        </head>
        <body>
            <div class='hourly-container'>
                {"".join(hourly_cards)}
            </div>
        </body>
        </html>
        """
        
        components.html(html_content, height=250, scrolling=False)
    
    # Coordinates
    st.markdown(f"""
    <div class='coordinates' style='margin-top: 30px;'>
        📍 {location['latitude']:.4f}°, {location['longitude']:.4f}°
    </div>
    """, unsafe_allow_html=True)
    
    # Timestamp
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    st.markdown(f"<p style='text-align: center; color: #888; font-size: 12px; margin-top: 15px; font-style: italic;'>Updated: {timestamp}</p>", unsafe_allow_html=True)
    
    # Action buttons
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("°F ⇄ °C", key=f"temp_toggle_{model_key}"):
            st.session_state.unit_temp = 'C' if st.session_state.unit_temp == 'F' else 'F'
            st.rerun()
    
    with col2:
        if st.button("mph ⇄ km/h", key=f"wind_toggle_{model_key}"):
            st.session_state.unit_wind = 'kmh' if st.session_state.unit_wind == 'mph' else 'mph'
            st.rerun()
    
    with col3:
        if st.button("🔄 Refresh", key=f"refresh_{model_key}"):
            st.rerun()

def main():
    # Sidebar
    with st.sidebar:
        st.header("🔍 Location Search")
        
        search_option = st.radio(
            "Choose search method:",
            ["📍 Use Current Location", "🌍 Search by Name"],
            index=1
        )
        
        location = None
        
        if search_option == "📍 Use Current Location":
            st.markdown("""
            <div style='background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 15px; font-size: 0.85em;'>
            <strong>📍 How it works:</strong><br>
            1. Click "Detect Location" below<br>
            2. Allow location access when browser prompts<br>
            3. Wait for confirmation message<br>
            4. Click "Detect Location" again to load weather<br><br>
            <em>Note: Uses IP-based location as fallback (city-level accuracy)</em>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📍 Detect Location", use_container_width=True, type="primary"):
                with st.spinner("Detecting your location..."):
                    location = get_current_location()
                    if location:
                        st.success(f"✅ Location set to: {location['city']}, {location['region']}")
                        st.session_state.last_location = location
                        weather_data = get_weather(location['latitude'], location['longitude'])
                        st.session_state.weather_data = (location, weather_data)
                        st.rerun()
                    else:
                        st.error("Could not detect your location. Please try searching by name.")
        
        else:
            # Function to handle search when Enter is pressed
            def handle_search():
                if st.session_state.location_search_input:
                    location_name = st.session_state.location_search_input
                    # Clear any stale results before new search
                    st.session_state.search_results = None
                    st.session_state.search_query = location_name
                    st.session_state.trigger_search = True
            
            location_name = st.text_input(
                "Enter location:",
                placeholder="e.g., London, Boston, Paris",
                help="Enter city name, or 'City, Country' for more specific results",
                key="location_search_input",
                on_change=handle_search
            )
            
            # Search button or Enter key trigger
            if st.button("Search", use_container_width=True) or st.session_state.get('trigger_search', False):
                if st.session_state.get('trigger_search'):
                    st.session_state.trigger_search = False  # Reset trigger
                
                if location_name:
                    # Clear any stale results before new search
                    st.session_state.search_results = None
                    st.session_state.search_query = location_name
                    with st.spinner(f"Searching for {location_name}..."):
                        results = get_location_by_name(location_name)
                        
                        if results:
                            st.session_state.search_results = results
                        else:
                            st.session_state.search_results = None
                            st.error(f"Location '{location_name}' not found. Try a different search.")
                else:
                    st.warning("Please enter a location name")
            
            # Display search results if available
            if 'search_results' in st.session_state and st.session_state.search_results and st.session_state.get('search_query'):
                results = st.session_state.search_results
                
                if len(results) > 1:
                    st.info(f"Found {len(results)} locations:")
                    
                    # Create selection options
                    location_options = [
                        f"{r.get('name')}, {r.get('admin1', '')}, {r.get('country')}"
                        for r in results
                    ]
                    
                    selected = st.selectbox(
                        "Choose location:", 
                        location_options,
                        key="location_selector"
                    )
                    
                    if st.button("Get Weather", use_container_width=True, type="primary"):
                        selected_idx = location_options.index(selected)
                        result = results[selected_idx]
                        
                        location = {
                            'latitude': result.get('latitude'),
                            'longitude': result.get('longitude'),
                            'city': result.get('name'),
                            'region': result.get('admin1', ''),
                            'country': result.get('country')
                        }
                        
                        st.session_state.last_location = location
                        
                        with st.spinner("Fetching weather data..."):
                            weather_data = get_weather(location['latitude'], location['longitude'])
                            st.session_state.weather_data = (location, weather_data)
                        
                        # Clear search results after selection
                        st.session_state.search_results = None
                        st.rerun()
                else:
                    # Only one result, use it directly
                    result = results[0]
                    st.success(f"Found: {result.get('name')}, {result.get('admin1', '')}, {result.get('country')}")
                    
                    if st.button("Get Weather", use_container_width=True, type="primary"):
                        location = {
                            'latitude': result.get('latitude'),
                            'longitude': result.get('longitude'),
                            'city': result.get('name'),
                            'region': result.get('admin1', ''),
                            'country': result.get('country')
                        }
                        
                        st.session_state.last_location = location
                        
                        with st.spinner("Fetching weather data..."):
                            weather_data = get_weather(location['latitude'], location['longitude'])
                            st.session_state.weather_data = (location, weather_data)
                        
                        # Clear search results after selection
                        st.session_state.search_results = None
                        st.rerun()
        
        st.markdown("---")
        st.markdown("### 🔑 API Configuration")
        st.markdown("<p style='font-size: 0.85em; color: #aaa;'>Optional: Enter your Groq API key for AI features</p>", unsafe_allow_html=True)
        groq_key_input = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="Enter your Groq API key (optional)",
            help="Get your free API key from https://console.groq.com/keys",
            key="groq_api_key_input"
        )
        if groq_key_input:
            st.session_state.groq_api_key = groq_key_input
            st.success("✅ Groq API key configured!")
        
        st.markdown("---")
        st.markdown("### 💡 Tips")
        st.markdown("""
        <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);'>
        • Search by city name (e.g., "London")<br>
        • Use "City, Country" for specific results<br>
        • Toggle between °F/°C and mph/km/h<br>
        • Click refresh for latest data
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    if st.session_state.weather_data:
        location, weather_data = st.session_state.weather_data
        
        if weather_data:
            # Add weather model comparison tabs
            st.markdown("### 🌞 Matt's Weather App")
            
            # Determine subtitle color based on temperature
            current_temp = weather_data.get('current', {}).get('temperature_2m') if weather_data else None
            if current_temp is not None and 76 <= current_temp <= 95:
                subtitle_color = "#263238"  # Dark gray for warm backgrounds
            else:
                subtitle_color = "#aaa"  # Light gray for cool backgrounds
            
            st.markdown(f"<p style='color: {subtitle_color}; font-size: 0.9em; margin-bottom: 20px;'>Compare forecasts from different global weather models</p>", unsafe_allow_html=True)
            
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Best Match (Auto)", 
                "🌐 ECMWF (European)",
                "🌎 GFS (NOAA)", 
                "⭐ ICON (German)",
                "☁️ Visual Crossing"
            ])
            
            with tab1:
                display_weather(location, weather_data, model_key='best_match')
            
            with tab2:
                # Dynamic description color based on temperature
                desc_color = "#263238" if current_temp is not None and 76 <= current_temp <= 95 else "#888"
                st.markdown(f"<p style='color: {desc_color}; font-size: 0.85em; font-style: italic;'>ECMWF IFS 0.25° - European Centre for Medium-Range Weather Forecasts (High accuracy, global coverage)</p>", unsafe_allow_html=True)
                with st.spinner("Loading ECMWF model data..."):
                    ecmwf_data = get_weather(location['latitude'], location['longitude'], model='ecmwf_ifs025')
                    if ecmwf_data:
                        display_weather(location, ecmwf_data, model_key='ecmwf')
                    else:
                        st.error("Unable to load ECMWF model data")
            
            with tab3:
                # Dynamic description color based on temperature
                desc_color = "#263238" if current_temp is not None and 76 <= current_temp <= 95 else "#888"
                st.markdown(f"<p style='color: {desc_color}; font-size: 0.85em; font-style: italic;'>GFS - NOAA Global Forecast System (Best for North America, 4x daily updates)</p>", unsafe_allow_html=True)
                with st.spinner("Loading GFS model data..."):
                    gfs_data = get_weather(location['latitude'], location['longitude'], model='gfs_global')
                    if gfs_data:
                        display_weather(location, gfs_data, model_key='gfs')
                    else:
                        st.error("Unable to load GFS model data")
            
            with tab4:
                # Dynamic description color based on temperature
                desc_color = "#263238" if current_temp is not None and 76 <= current_temp <= 95 else "#888"
                st.markdown(f"<p style='color: {desc_color}; font-size: 0.85em; font-style: italic;'>ICON - German Weather Service (High resolution, updated 4x daily)</p>", unsafe_allow_html=True)
                with st.spinner("Loading ICON model data..."):
                    icon_data = get_weather(location['latitude'], location['longitude'], model='icon_global')
                    if icon_data:
                        display_weather(location, icon_data, model_key='icon')
                    else:
                        st.error("Unable to load ICON model data")
            
            with tab5:
                # Dynamic description color based on temperature
                desc_color = "#263238" if current_temp is not None and 76 <= current_temp <= 95 else "#888"
                st.markdown(f"<p style='color: {desc_color}; font-size: 0.85em; font-style: italic;'>Visual Crossing - Professional weather API with natural language descriptions and detailed hourly forecasts</p>", unsafe_allow_html=True)
                with st.spinner("Loading Visual Crossing data..."):
                    vc_data = get_visual_crossing_forecast(location['latitude'], location['longitude'])
                    if vc_data:
                        display_weather(location, vc_data, model_key='visual_crossing')
                    else:
                        st.error("Unable to load Visual Crossing data")
            
            # Add spacing before radar
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # Display radar with tabs at bottom (outside weather model tabs, always visible)
            st.markdown("### 🗺️ Weather Radar")
            radar_tab1, radar_tab2, radar_tab3 = st.tabs(["�️ Multi-Layer Radar", "�🌧️ RainViewer Radar", "🌤️ Visual Crossing Map"])
            
            with radar_tab1:
                # Dynamic description color based on temperature
                desc_color = "#263238" if current_temp is not None and 76 <= current_temp <= 95 else "#888"
                st.markdown(f"<p style='color: {desc_color}; font-size: 0.85em; font-style: italic;'>Windy.com interactive weather map with multiple layers</p>", unsafe_allow_html=True)
                display_windy_radar(location, current_temp)
            
            with radar_tab2:
                # Dynamic description color based on temperature
                desc_color = "#263238" if current_temp is not None and 76 <= current_temp <= 95 else "#888"
                st.markdown(f"<p style='color: {desc_color}; font-size: 0.85em; font-style: italic;'>Animated radar: 2 hours past + 30 min forecast</p>", unsafe_allow_html=True)
                display_radar(location, current_temp)
            
            with radar_tab3:
                # Dynamic description color based on temperature
                desc_color = "#263238" if current_temp is not None and 76 <= current_temp <= 95 else "#888"
                st.markdown(f"<p style='color: {desc_color}; font-size: 0.85em; font-style: italic;'>Animated precipitation radar with current conditions</p>", unsafe_allow_html=True)
                display_visual_crossing_radar(location, current_temp)
        else:
            st.error("Could not fetch weather data. Please try again.")
    else:
        # Welcome message
        st.markdown("""
        <div style='text-align: center; padding: 50px; background: rgba(30, 30, 45, 0.9); border-radius: 20px; margin: 50px auto; max-width: 600px; border: 1px solid rgba(100, 100, 150, 0.3);'>
            <h2 style='color: #00d4ff; text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);'>🌤️</h2>
            <p style='color: #bbb; font-size: 18px; margin-top: 20px;'>
                Get started by searching for a location in the sidebar or use your current location.
            </p>
            <p style='color: #888; font-size: 14px; margin-top: 30px;'>
                ☀️ Real-time weather data<br>
                🌍 Search any location worldwide<br>
                🔄 Multiple unit conversions<br>
                📱 Responsive design
            </p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

