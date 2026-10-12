import json
from datetime import datetime
import requests

# 1. Define your target locations (Name, Latitude, Longitude)
LOCATIONS = {
    "Lancaster, WI": {"lat": 42.8485, "lon": -90.7104},
    "Madison, WI": {"lat": 43.0731, "lon": -89.4012},
    "Milwaukee, WI": {"lat": 43.0389, "lon": -87.9065},
}


def fetch_hrrr_forecast(lat, lon):
  """Fetches HRRR hourly forecast data via Open-Meteo API"""
  url = "https://api.open-meteo.com/v1/forecast"
  params = {
      "latitude": lat,
      "longitude": lon,
      "hourly": ["temperature_2m", "precipitation_probability", "weather_code"],
      "models": "hrrr_seamless",  # Uses high-res HRRR/NAM blend framework
      "forecast_days": 2,
  }

  response = requests.get(url, params=params, timeout=10)
  response.raise_for_status()
  return response.json()


def fetch_spc_risk():
  """Fetches current SPC convective outlook risk areas (Example GeoJSON feed)"""
  # NOAA SPC public GIS/GeoJSON endpoint for day 1 convective outlook
  spc_url = (
      "https://www.spc.noaa.gov/products/outlook/day1otlk_cat.lyr.geojson"
  )
  try:
    res = requests.get(spc_url, timeout=10)
    if res.status_code == 200:
      return res.json()
  except Exception:
    pass
  return {"note": "No active convective layer or feed unreachable"}


def generate_daily_report():
  master_data = {"updated_at": datetime.utcnow().isoformat(), "forecasts": {}}

  for name, coords in LOCATIONS.items():
    data = fetch_hrrr_forecast(coords["lat"], coords["lon"])

    # Extract the next 24 hours slice
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])[:24]
    temps = hourly.get("temperature_2m", [])[:24]
    precip_probs = hourly.get("precipitation_probability", [])[:24]

    master_data["forecasts"][name] = {
        "time_slice": times,
        "temperature_2m": temps,
        "precipitation_probability": precip_probs,
        "high_temp": max(temps) if temps else None,
        "low_temp": min(temps) if temps else None,
    }

  # Pull SPC data context
  master_data["spc_outlook"] = fetch_spc_risk()

  # Save output to a JSON file (which your website or Facebook poster will read)
  with open("daily_forecast_cache.json", "w") as f:
    json.dump(master_data, f, indent=4)

  print("Successfully generated daily forecast data package!")


if __name__ == "__main__":
  generate_daily_report()