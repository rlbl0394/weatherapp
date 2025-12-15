# 🌤️ W## ✨ Features

- 🌍 **Global Weather Data** - Search any location worldwide
- 📍 **Auto-Location Detection** - Automatically detect your current location
- 📅 **Daily Weather Outlook** - Professional natural language weather descriptions (powered by Visual Crossing)
- 🌧️ **Animated Weather Radar** - Real-time precipitation radar with past & future forecasts
- 🚨 **Weather Alerts & Warnings** - Real-time severe weather alerts from National Weather Service (US)
- 🌐 **Multiple Weather Models** - Compare ECMWF, GFS, and ICON forecasts
- 📊 **72-Hour Forecast** - Extended hourly forecast with precipitation amounts and probabilities
- ⚡ **Precipitation Alerts** - Get notified of upcoming rain, snow, or storms
- 🌡️ **Unit Conversion** - Toggle between °F/°C and mph/km/h
- 🎨 **Beautiful Dark Mode UI** - Modern gradient design with smooth animations
- 🔄 **Real-time Updates** - Get the latest weather data instantly
- 📱 **Responsive Design** - Works perfectly on desktop and mobile
- 🆓 **Ready to Use** - Configured with API keys, works immediately
A beautiful, real-time weather application built with Streamlit that provides current weather information for any location worldwide.

![Weather App](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)

## ✨ Features

- 🌍 **Global Weather Data** - Search any location worldwide
- 📍 **Auto-Location Detection** - Automatically detect your current location
- �️ **Animated Weather Radar** - Real-time precipitation radar with past & future forecasts
- 🌐 **Multiple Weather Models** - Compare ECMWF, GFS, and ICON forecasts
- 📊 **24-Hour Forecast** - Scrollable hourly forecast with precipitation probabilities
- ⚡ **Precipitation Alerts** - Get notified of upcoming rain, snow, or storms
- �🌡️ **Unit Conversion** - Toggle between °F/°C and mph/km/h
- 🎨 **Beautiful Dark Mode UI** - Modern gradient design with smooth animations
- 🔄 **Real-time Updates** - Get the latest weather data instantly
- 📱 **Responsive Design** - Works perfectly on desktop and mobile
- 🆓 **No API Key Required** - Uses free Open-Meteo API

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

- **Streamlit** - Web application framework
- **Open-Meteo API** - Free weather data API (ECMWF, GFS, ICON models)
- **National Weather Service API** - Real-time weather alerts and warnings (US)
- **RainViewer API** - Animated weather radar with precipitation forecasts
- **Leaflet.js** - Interactive map visualization
- **ipapi.co** - IP-based geolocation
- **Python 3.8+** - Programming language

## 📦 Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/weather-app.git
cd weather-app
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

5. Run the app:
```bash
streamlit run weather_streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## 🌐 Deploying to Streamlit Cloud

1. **Fork or Push to GitHub**
   - Push this repository to your GitHub account

2. **Sign in to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account

3. **Create New App**
   - Click "New app"
   - Select your repository
   - Choose `weather_streamlit_app.py` as the main file
   - Click "Deploy"

4. **Your app is live!**
   - URL will be: `https://yourusername-weather-app-streamlit.app`

## 📋 Project Structure

```
weather-app/
├── weather_streamlit_app.py    # Main Streamlit application
├── weather.py                  # Original CLI version
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git ignore file
├── .streamlit/
│   └── config.toml            # Streamlit configuration
└── README.md                  # This file
```

## 🎯 Usage

### Search by Location
1. Enter a city name in the sidebar
2. Click "Get Weather"
3. Select from multiple results if applicable
4. View real-time weather data

### Auto-Detect Location
1. Select "Use Current Location" in the sidebar
2. Click "Detect Location"
3. Allow browser location permissions
4. View weather for your current location

### Convert Units
- Click **°F ⇄ °C** to toggle temperature units
- Click **mph ⇄ km/h** to toggle wind speed units
- Click **🔄 Refresh** to update weather data

## 📊 Weather Data Includes

- 🌡️ **Temperature** - Current temperature with unit conversion
- 💧 **Humidity** - Relative humidity percentage
- 💨 **Wind Speed** - Current wind speed with unit conversion
- ☁️ **Conditions** - Current weather conditions (clear, cloudy, rain, etc.)
- 📍 **Coordinates** - Latitude and longitude
- 🕐 **Update Time** - Last data refresh timestamp

## 🎨 Dark Mode Theme

The app features a beautiful dark mode design with:
- Deep blue gradient background
- Glowing cyan temperature display
- Smooth floating animations
- Gradient detail cards
- Enhanced contrast and readability

## 🔧 Configuration

### Streamlit Configuration
The app includes a `.streamlit/config.toml` file with optimized settings:
- Dark theme enabled
- Improved performance
- Responsive layout

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

- Weather data provided by [Open-Meteo](https://open-meteo.com/)
- Geolocation by [ipapi.co](https://ipapi.co/)
- Built with [Streamlit](https://streamlit.io/)


**Made with ❤️ using Streamlit**

⭐ Star this repo if you find it useful!
