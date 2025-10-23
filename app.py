import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    raise RuntimeError("Set OPENWEATHER_API_KEY in .env")

app = Flask(__name__)

OW_BASE = "https://api.openweathermap.org/data/2.5"


def fetch_current(city: str, units: str = "metric"):
    r = requests.get(f"{OW_BASE}/weather", params={
        "q": city,
        "appid": API_KEY,
        "units": units,
    }, timeout=12)
    r.raise_for_status()
    d = r.json()
    return {
        "city": d.get("name"),
        "country": d.get("sys", {}).get("country"),
        "temp": d.get("main", {}).get("temp"),
        "feels_like": d.get("main", {}).get("feels_like"),
        "humidity": d.get("main", {}).get("humidity"),
        "pressure": d.get("main", {}).get("pressure"),
        "wind_speed": d.get("wind", {}).get("speed"),
        "description": d.get("weather", [{}])[0].get("description"),
        "icon": d.get("weather", [{}])[0].get("icon"),
    }


def fetch_forecast(city: str, units: str = "metric"):
    r = requests.get(f"{OW_BASE}/forecast", params={
        "q": city,
        "appid": API_KEY,
        "units": units,
    }, timeout=12)
    r.raise_for_status()
    d = r.json()
    items = d.get("list", [])
    daily = {}
    for it in items:
        dt_txt = it.get("dt_txt", "")
        date = dt_txt.split(" ")[0]
        hour = dt_txt.split(" ")[1] if " " in dt_txt else "00:00:00"
        if date not in daily or hour == "12:00:00":
            daily[date] = {
                "date": date,
                "temp": it.get("main", {}).get("temp"),
                "temp_min": it.get("main", {}).get("temp_min"),
                "temp_max": it.get("main", {}).get("temp_max"),
                "description": it.get("weather", [{}])[0].get("description"),
                "icon": it.get("weather", [{}])[0].get("icon"),
            }
    forecast = list(sorted(daily.values(), key=lambda x: x["date"]))[:5]
    return forecast


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/weather")
def api_weather():
    city = request.args.get("city", "").strip()
    units = request.args.get("units", "metric")
    if not city:
        return jsonify({"error": "city is required"}), 400
    try:
        current = fetch_current(city, units)
        forecast = fetch_forecast(city, units)
        return jsonify({
            "units": units,
            "current": current,
            "forecast": forecast,
        })
    except requests.HTTPError as e:
        code = getattr(e.response, "status_code", 500)
        try:
            msg = e.response.json().get("message")
        except Exception:
            msg = str(e)
        return jsonify({"error": msg or "request failed"}), code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
