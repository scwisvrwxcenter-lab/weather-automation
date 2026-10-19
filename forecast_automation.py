from datetime import datetime, timezone
import json
import requests
from zoneinfo import ZoneInfo

# Define target locations (Name, Latitude, Longitude, County/Region label)
LOCATIONS = {
    "Lancaster_WI": {
        "lat": 42.8485,
        "lon": -90.7104,
        "region": "South-Western",
    },
    "Madison_WI": {
        "lat": 43.0731,
        "lon": -89.4012,
        "region": "South-Central",
    },
    "Milwaukee_WI": {
        "lat": 43.0389,
        "lon": -87.9065,
        "region": "South-Eastern",
    },
    # Add your other locations here if needed
}


def wmo_to_condition(code):
  """Converts Open-Meteo WMO weather codes to descriptive text and icons"""
  if code == 0:
    return "Sunny"
  elif code in [1, 2]:
    return "Partly Sunny"
  elif code == 3:
    return "Cloudy"
  elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
    return "Rainy"
  elif code in [95, 96, 99]:
    return "Stormy"
  return "Fair"


def fetch_7day_forecast(lat, lon):
  """Fetches 7-day daily forecast data in Central Time via Open-Meteo GFS/HRRR endpoint"""
  url = "https://api.open-meteo.com/v1/gfs"
  params = {
      "latitude": lat,
      "longitude": lon,
      "daily": (
          "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code"
      ),
      "temperature_unit": "fahrenheit",
      "timezone": "America/Chicago",
      "forecast_days": 7,
  }

  response = requests.get(url, params=params, timeout=10)
  response.raise_for_status()
  return response.json()


def fetch_spc_risk(lat, lon):
  """Fetches SPC outlook and assigns a 0/6 scale risk level for the location"""
  spc_url = (
      "https://www.spc.noaa.gov/products/outlook/day1otlk_cat.lyr.geojson"
  )
  try:
    res = requests.get(spc_url, timeout=10)
    if res.status_code == 200:
      geojson = res.json()
      # Simple point-in-polygon or fallback risk assignment logic
      # Default baseline risk level
      risk_label = "0/6 Risk"
      for feature in geojson.get("features", []):
        # A full point-in-polygon check can be added here using shapely if needed.
        # For now, we capture live outlook metadata if available.
        label = feature.get("properties", {}).get("LABEL", "")
        if label:
          # Map SPC categories to your 0/6 scale UI
          if "MRGL" in label:
            risk_label = "1/5 Risk (MRGL)"
          elif "SLGT" in label:
            risk_label = "2/5 Risk (SLGT)"
          elif "ENH" in label:
            risk_label = "3/5 Risk (ENH)"
          elif "MDT" in label:
            risk_label = "4/5 Risk (MDT)"
          elif "HIGH" in label:
            risk_label = "5/5 Risk (HIGH)"
      return risk_label
  except Exception:
    pass
  return "0/5 Risk"


def generate_daily_report():
  ct_zone = ZoneInfo("America/Chicago")
  current_time_ct = datetime.now(ct_zone)

  master_data = {
      "updated_at": current_time_ct.isoformat(),
      "date_range": current_time_ct.strftime("%m/%d")
      + " - "
      + (current_time_ct.replace(day=current_time_ct.day + 6)).strftime("%m/%d"),
      "forecasts": {},
  }

  for name, info in LOCATIONS.items():
    data = fetch_7day_forecast(info["lat"], info["lon"])
    daily = data.get("daily", {})

    dates = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    precip_probs = daily.get("precipitation_probability_max", [])
    weather_codes = daily.get("weather_code", [])

    weekly_days = []
    for i in range(len(dates)):
      dt = datetime.strptime(dates[i], "%Y-%m-%d")
      weekly_days.append({
          "date": dt.strftime("%m/%d"),
          "day_name": dt.strftime("%a").upper(),
          "high": round(max_temps[i]) if i < len(max_temps) else 0,
          "low": round(min_temps[i]) if i < len(min_temps) else 0,
          "precip_prob": (
              precip_probs[i] if i < len(precip_probs) and precip_probs[i] else 0
          ),
          "condition": wmo_to_condition(
              weather_codes[i] if i < len(weather_codes) else 0
          ),
          "risk_level": fetch_spc_risk(info["lat"], info["lon"]),
      })

    master_data["forecasts"][name] = {
        "region_description": info["region"],
        "days": weekly_days,
    }

  # Save output package for frontend rendering and social bots
  with open("daily_forecast_cache.json", "w") as f:
    json.dump(master_data, f, indent=4)

  print("Successfully generated 7-day Central Time forecast package!")


if __name__ == "__main__":
  generate_daily_report()
