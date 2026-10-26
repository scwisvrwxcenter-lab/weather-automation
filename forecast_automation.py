from datetime import datetime
import json
import requests
from shapely.geometry import Point, shape
from zoneinfo import ZoneInfo

# Defined locations: Lancaster, Madison, and Milwaukee
LOCATIONS = {
    "Lancaster_WI": {
        "name": "Lancaster, WI",
        "lat": 42.8485,
        "lon": -90.7104,
        "region": "South-Western Grant County",
    },
    "Madison_WI": {
        "name": "Madison, WI",
        "lat": 43.0731,
        "lon": -89.4012,
        "region": "South-Central Dane County",
    },
    "Milwaukee_WI": {
        "name": "Milwaukee, WI",
        "lat": 43.0389,
        "lon": -87.9065,
        "region": "South-Eastern Milwaukee County",
    },
}


def wmo_to_condition(code):
  """Maps WMO weather interpretation codes to readable weather conditions."""
  if code == 0:
    return "Sunny"
  elif code in [1, 2]:
    return "Partly Sunny"
  elif code == 3:
    return "Cloudy"
  elif code in [45, 48]:
    return "Foggy"
  elif code in [51, 53, 55, 56, 57]:
    return "Drizzle"
  elif code in [61, 63, 65, 66, 67, 80, 81, 82]:
    return "Rainy"
  elif code in [71, 73, 75, 77, 85, 86]:
    return "Snowy"
  elif code in [95, 96, 99]:
    return "Stormy"
  return "Fair"


def fetch_7day_forecast(lat, lon):
  """Fetches a 7-day daily weather outlook from Open-Meteo in Central Time."""
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
  """Checks whether lat/lon falls inside active SPC Day 1 categorical risk polygon.

  Maps SPC severe weather categories to a 5-point scale (1/5 to 5/5).
  Defaults to '0/5 Risk' if no active risk covers the location.
  """
  spc_url = (
      "https://www.spc.noaa.gov/products/outlook/day1otlk_cat.lyr.geojson"
  )
  point = Point(lon, lat)  # Point order in GeoJSON geometry is (lon, lat)

  # Standard 5-Level SPC Categorical Risk Scale
  risk_map = {
      "MRGL": "1/5 Risk",  # Level 1: Marginal
      "SLGT": "2/5 Risk",  # Level 2: Slight
      "ENH": "3/5 Risk",  # Level 3: Enhanced
      "MDT": "4/5 Risk",  # Level 4: Moderate
      "HIGH": "5/5 Risk",  # Level 5: High
  }

  try:
    res = requests.get(spc_url, timeout=10)
    if res.status_code == 200:
      geojson = res.json()
      highest_risk = "0/5 Risk"
      highest_level = 0

      for feature in geojson.get("features", []):
        properties = feature.get("properties", {})
        label = str(properties.get("LABEL", "")).upper()

        # Spatial check: verifies if coordinates are inside polygon geometry
        polygon = shape(feature.get("geometry"))
        if polygon.contains(point):
          for code, risk_text in risk_map.items():
            if code in label:
              level = int(risk_text.split("/")[0])
              if level > highest_level:
                highest_level = level
                highest_risk = risk_text

      return highest_risk
  except Exception as e:
    print(f"Error checking SPC risk: {e}")

  return "0/5 Risk"


def generate_daily_report():
  ct_zone = ZoneInfo("America/Chicago")
  current_time_ct = datetime.now(ct_zone)

  master_data = {
      "updated_at": current_time_ct.isoformat(),
      "date_range": current_time_ct.strftime("%m/%d"),
      "forecasts": {},
  }

  for key, info in LOCATIONS.items():
    data = fetch_7day_forecast(info["lat"], info["lon"])
    daily = data.get("daily", {})

    dates = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    precip_probs = daily.get("precipitation_probability_max", [])
    weather_codes = daily.get("weather_code", [])

    if dates:
      start_dt = datetime.strptime(dates[0], "%Y-%m-%d")
      end_dt = datetime.strptime(dates[-1], "%Y-%m-%d")
      master_data["date_range"] = (
          f"{start_dt.strftime('%m/%d')}-{end_dt.strftime('%m/%d')}"
      )

    weekly_days = []
    spc_risk = fetch_spc_risk(info["lat"], info["lon"])

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
          "risk_level": spc_risk if i == 0 else "0/5 Risk",
      })

    master_data["forecasts"][key] = {
        "display_name": info["name"],
        "region_description": info["region"],
        "days": weekly_days,
    }

  with open("daily_forecast_cache.json", "w") as f:
    json.dump(master_data, f, indent=4)

  print(
      "Successfully generated 7-day Central Time forecast cache with fixed 5-point"
      " SPC risk scale!"
  )


if __name__ == "__main__":
  generate_daily_report()
