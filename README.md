# � Matt's Weather App

A beautiful, intelligent weather application built with Streamlit featuring AI-powered insights, dynamic backgrounds, and real-time weather data for any location worldwide.

![Weather App](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)

## ✨ Features

### 🤖 AI-Powered Intelligence
- **⚡ AI Weather Overview** - Ultra-fast weather analysis powered by Groq's Llama 3.3 70B
- **💬 AI Weather Chatbot** - Ask questions about weather with confident, assertive responses
- **✈️ AI Travel Weather Compare** - Smart comparison between locations for travel planning
- **🎯 Assertive Recommendations** - Confident weather advice based on professional-grade data

### 🎨 Dynamic User Experience
- **🌈 Temperature-Based Backgrounds** - App changes colors based on weather (ice blue → orange → deep red)
- **📱 Adaptive Text Colors** - Perfect readability on all backgrounds (automatic contrast adjustment)
- **🌞 Enhanced Sun Times Display** - Sunrise, sunset, day length, and twilight information
- **💫 Smooth Animations** - Floating weather icons and gradient transitions

### 🌍 Weather Data & Forecasting
- **🌐 Multiple Weather Models** - Compare ECMWF (European), GFS (NOAA), ICON (German), and Visual Crossing forecasts
- **📊 72-Hour Forecast** - Extended hourly forecast with precipitation amounts and probabilities
- **⚡ Precipitation Alerts** - Smart notifications for upcoming rain, snow, or storms
- **🚨 Weather Alerts** - Real-time severe weather warnings from National Weather Service (US)

### 🗺️ Advanced Radar Systems
- **🌬️ Multi-Layer Interactive Radar** - Powered by Windy.com with customizable layers
- **🌧️ Animated Precipitation Radar** - RainViewer with 2 hours past + 30 min forecast
- **☁️ Visual Crossing Radar** - Alternative precipitation visualization

### 🛠️ User Convenience
- **📍 Smart Location Search** - Intelligent ranking for exact city matches
- **🔍 Auto-Location Detection** - Browser-based GPS positioning
- **🌡️ Unit Conversion** - Toggle between °F/°C and mph/km/h instantly
- **🔑 Public Deployment Ready** - API key input in sidebar for public hosting
- **📱 Responsive Design** - Works perfectly on desktop and mobile
- **🆓 No API Key Required** - Free Open-Meteo API (Groq API optional for AI features)

## 🚀 Live Demo

Visit the live app: [Your App URL will be here after deployment]

## 📸 Screenshots

### Main Weather View
- Beautiful dark mode interface
- Animated weather icons
- Real-time temperature display
- Humidity and wind speed metrics

### Location Search
- Search by city name
- Multiple location results
- Auto-detection option

## 🛠️ Technologies Used

- **Streamlit** - Web application framework with modern UI
- **Groq AI** - Ultra-fast AI inference (Llama 3.3 70B model)
- **Open-Meteo API** - Free weather data (ECMWF, GFS, ICON models)
- **National Weather Service API** - Real-time weather alerts (US)
- **RainViewer API** - Animated precipitation radar
- **Windy.com** - Interactive multi-layer weather maps
- **Leaflet.js** - Interactive map visualization
- **ipapi.co** - IP-based geolocation fallback
- **Python 3.8+** - Core programming language

## 📦 Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/weatherapp.git
cd weatherapp
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - **Windows**: `venv\Scripts\activate`
   - **Mac/Linux**: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. (Optional) Configure Groq API for AI features:
   - Get a free API key from [Groq Console](https://console.groq.com/keys)
   - Create a `.env` file in the project root:
   ```
   GROQ_API_KEY=your_api_key_here
   ```
   - Or enter the API key in the sidebar when running the app

6. Run the app:
```bash
streamlit run weather_streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## 🌐 Deploying to Streamlit Cloud

1. **Fork or Push to GitHub**
   - Push this repository to your GitHub account
   - **Important**: Do NOT include `.env` file in your repository (already in `.gitignore`)

2. **Sign in to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account

3. **Create New App**
   - Click "New app"
   - Select your repository
   - Choose `weather_streamlit_app.py` as the main file
   - Click "Deploy"

4. **Configure API Keys (Optional for AI features)**
   - Users can enter their Groq API key directly in the sidebar
   - Or configure secrets in Streamlit Cloud settings
   - Get free API key: [Groq Console](https://console.groq.com/keys)

5. **Your app is live!**
   - URL will be: `https://yourusername-weatherapp.streamlit.app`

## 📋 Project Structure

```
weatherapp/
├── weather_streamlit_app.py    # Main Streamlit application
├── weather.py                  # Original CLI version
├── requirements.txt            # Python dependencies
├── .env                        # API keys (NOT in git - local only)
├── .env.example               # Example environment file
├── .gitignore                 # Git ignore file
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── LICENSE                    # MIT License
└── README.md                  # This file
```

## 🎯 Usage

### Search by Location
1. Enter a city name in the sidebar (e.g., "Manila" or "Manila, Philippines")
2. Click "Search Location"
3. Select from results if multiple matches
4. View weather across multiple model tabs

### Auto-Detect Location
1. Select "📍 Use Current Location" in the sidebar
2. Click "Detect Location"
3. Allow browser location permissions
4. Weather loads automatically

### Use AI Features
1. **AI Overview**: Expand "⚡ AI Weather Overview" for instant AI analysis
2. **AI Chatbot**: Expand "💬 AI Weather Chatbot" to ask questions
3. **Travel Compare**: Expand "✈️ AI Travel Weather Compare" to compare destinations
4. **Add API Key**: Enter Groq API key in sidebar (optional, for AI features)

### Explore Weather Models
- **📊 Best Match**: Auto-selected optimal model for your location
- **🌐 ECMWF**: European model (high accuracy, global coverage)
- **🌎 GFS**: NOAA model (best for North America)
- **⭐ ICON**: German model (high resolution)
- **☁️ Visual Crossing**: Alternative professional weather data

### View Weather Radars
- **🌬️ Multi-Layer Radar**: Interactive Windy.com map with customizable layers
- **🌧️ RainViewer Radar**: Animated precipitation with past & forecast
- **☁️ Visual Crossing Map**: Alternative radar view

## 📊 Weather Data Includes

### Current Conditions
- 🌡️ **Temperature** - With dynamic color-coded backgrounds based on temperature
- 💧 **Humidity** - Relative humidity percentage
- 💨 **Wind Speed** - Current wind speed with unit conversion
- ☁️ **Conditions** - Detailed weather conditions with time-appropriate emojis (day/night)
- 📍 **Coordinates** - Precise latitude and longitude

### Extended Information
- 🌅 **Sun Times** - Sunrise, sunset, day length, first/last light
- 🌈 **UV Index** - Color-coded UV level with safety recommendations
- 📊 **72-Hour Forecast** - Hourly predictions with precipitation probability
- 🌧️ **Precipitation Alerts** - Smart notifications for upcoming rain/snow
- 🚨 **Weather Alerts** - Severe weather warnings (US locations)

### AI Insights
- 🤖 **Weather Pattern Analysis** - Why certain weather conditions are occurring
- 👔 **Outfit Recommendations** - What to wear based on conditions
- 🎯 **Activity Suggestions** - Indoor/outdoor activity recommendations
- ✈️ **Travel Advice** - Smart comparisons between locations

## 🎨 Design Features

### Dynamic Temperature-Based Backgrounds
The app automatically changes background colors based on temperature:
- ❄️ **≤32°F** - Ice blue gradient (freezing conditions)
- 🧊 **33-50°F** - Cool blue tones (cold weather)
- 🌊 **51-68°F** - Mild blue-purple (comfortable)
- 🌿 **69-75°F** - Blue-green gradient (pleasant)
- 🌅 **76-85°F** - Orange-yellow (warm weather)
- 🔥 **86-95°F** - Red-orange (hot conditions)
- 🌡️ **≥96°F** - Deep red (extreme heat)

### Adaptive Text Colors
- Automatic contrast adjustment for readability
- Dark text on warm backgrounds (76-95°F)
- Light text on cool backgrounds
- All UI elements adapt dynamically

### Enhanced Visual Elements
- Glowing temperature display with color-matched shadows
- Smooth floating animations on weather icons
- Gradient detail cards with dynamic colors
- High-contrast sun times display
- Professional color schemes throughout

## 🔧 Configuration

### Streamlit Configuration
Optimized `.streamlit/config.toml` settings:
- Dark theme enabled by default
- Improved performance and caching
- Responsive layout for all devices

### API Configuration
**Local Development:**
- Create `.env` file with your API keys
- API keys automatically loaded from environment
- Works seamlessly without manual input

**Public Deployment:**
- Users enter their own Groq API key in sidebar
- No `.env` file needed in deployment
- Each user uses their own API quota
- Secure password field for API key input

### Environment Variables
```bash
GROQ_API_KEY=your_groq_api_key_here  # Optional, for AI features
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Weather data provided by [Open-Meteo](https://open-meteo.com/) - Free global weather API
- AI inference powered by [Groq](https://groq.com/) - Ultra-fast LLM processing
- Weather alerts from [National Weather Service](https://www.weather.gov/) - US severe weather warnings
- Radar data from [RainViewer](https://www.rainviewer.com/) - Real-time precipitation visualization
- Interactive maps by [Windy.com](https://www.windy.com/) - Professional weather platform
- Geolocation by [ipapi.co](https://ipapi.co/) - IP-based location detection
- Built with [Streamlit](https://streamlit.io/) - Modern Python web framework

## 🌟 Key Highlights

- **🆓 Free to Use** - No API key required for basic weather features
- **🤖 AI-Powered** - Optional Groq integration for intelligent insights
- **🎨 Beautiful UI** - Temperature-responsive design with adaptive colors
- **🌍 Global Coverage** - Weather data for any location worldwide
- **📱 Mobile-Ready** - Fully responsive on all devices
- **⚡ Lightning Fast** - Groq AI provides responses in milliseconds
- **🔒 Privacy-Focused** - API keys never stored, only in session
- **🚀 Deploy Anywhere** - Ready for Streamlit Cloud or any hosting platform

## 📧 Contact

Project Link: [https://github.com/rlbl0394/weatherapp](https://github.com/rlbl0394//weatherapp)

---

**Made with ❤️ using Streamlit + Groq AI**

⭐ Star this repo if you find it useful!

## 💡 Tips for Best Experience

- 🔑 Add your Groq API key for AI features (free tier available)
- 🌍 Try different weather models to see forecast variations
- 🗺️ Explore all three radar options for comprehensive view
- 💬 Ask the AI chatbot specific questions about weather patterns
- ✈️ Use travel comparison when planning trips
- 📱 Works great on mobile - add to home screen for quick access
