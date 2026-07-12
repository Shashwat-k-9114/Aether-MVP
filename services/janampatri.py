"""
Aether — Janampatri Generation Service (Accurate, Local)
------------------------------------------------
Computes real planetary positions locally using the Swiss Ephemeris
(pyswisseph) — no external API, no rate limits, no network dependency
for the astronomical calculation itself. Geopy + TimezoneFinder are
still used to turn a place name into coordinates / UTC offset.

Uses the Lahiri ayanamsa (the standard for Vedic/sidereal astrology)
and a whole-sign house system, which is what most Janampatri tools use.
"""

import pytz
import swisseph as swe
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

swe.set_sid_mode(swe.SIDM_LAHIRI)

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,  # Ketu is derived (Rahu + 180°)
}

# Geocoder cache to avoid hitting rate limits
_geocode_cache = {}
_tzf = TimezoneFinder()


def _get_location_data(place: str) -> tuple:
    """
    Convert place name to (latitude, longitude, utc_offset_hours).
    Caches results to avoid repeated API calls.
    """
    if place in _geocode_cache:
        return _geocode_cache[place]

    geolocator = Nominatim(user_agent="aether_app")
    try:
        location = geolocator.geocode(place, timeout=10)
        if not location:
            raise ValueError(f"Could not geocode: {place}")

        lat, lon = location.latitude, location.longitude

        tz_name = _tzf.timezone_at(lat=lat, lng=lon)
        if not tz_name:
            tz_name = "Asia/Kolkata"  # fallback

        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        offset_hours = now.utcoffset().total_seconds() / 3600

        result = (lat, lon, offset_hours)
        _geocode_cache[place] = result
        return result

    except Exception as e:
        print(f"Geocoding failed for '{place}': {e}. Falling back to IST.")
        return (19.0760, 72.8777, 5.5)  # Mumbai coordinates + IST


def _sign_for_longitude(longitude: float) -> tuple:
    """Given a sidereal longitude (0-360), return (sign_name, degree_in_sign)."""
    longitude = longitude % 360
    index = int(longitude // 30)
    degree_in_sign = longitude % 30
    return ZODIAC_SIGNS[index], degree_in_sign


def _nakshatra_for_longitude(moon_longitude: float) -> str:
    """Given the Moon's sidereal longitude, return 'Name - Pada'."""
    moon_longitude = moon_longitude % 360
    nak_size = 360 / 27  # 13°20' each
    index = int(moon_longitude // nak_size)
    pada = int((moon_longitude % nak_size) // (nak_size / 4)) + 1
    return f"{NAKSHATRAS[index]} - {pada}"


def generate_janampatri(date_of_birth: str, time_of_birth: str, place_of_birth: str) -> dict:
    """
    Generate an astronomically accurate birth chart using the Swiss
    Ephemeris, computed entirely locally.
    """
    # 1. Parse birth details
    dob = datetime.strptime(date_of_birth, "%Y-%m-%d")

    if time_of_birth:
        tob = datetime.strptime(time_of_birth, "%H:%M").time()
        birth_dt = datetime.combine(dob, tob)
    else:
        birth_dt = datetime.combine(dob, datetime.min.time().replace(hour=12))
        print(f"Warning: Birth time missing for {place_of_birth}. Using 12:00 PM.")

    # 2. Get coordinates and timezone
    lat, lon, utc_offset = _get_location_data(place_of_birth)

    # 3. Convert local birth time to a Julian Day in Universal Time
    decimal_hour_local = birth_dt.hour + birth_dt.minute / 60.0
    decimal_hour_ut = decimal_hour_local - utc_offset
    jd_ut = swe.julday(birth_dt.year, birth_dt.month, birth_dt.day, decimal_hour_ut)

    # 4. Ascendant + whole-sign houses
    _cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, hsys=b"W", flags=swe.FLG_SIDEREAL)
    ascendant_longitude = ascmc[0]
    ascendant, _ = _sign_for_longitude(ascendant_longitude)
    ascendant_sign_index = int(ascendant_longitude % 360 // 30)

    # 5. Planetary positions
    planetary_positions = []
    planet_longitudes = {}

    for name, planet_id in PLANET_IDS.items():
        longitude = swe.calc_ut(jd_ut, planet_id, swe.FLG_SIDEREAL)[0][0]
        planet_longitudes[name] = longitude

    # Ketu is always exactly opposite Rahu
    planet_longitudes["Ketu"] = (planet_longitudes["Rahu"] + 180) % 360

    for name, longitude in planet_longitudes.items():
        sign, degree_in_sign = _sign_for_longitude(longitude)
        sign_index = int(longitude % 360 // 30)
        house_num = ((sign_index - ascendant_sign_index) % 12) + 1

        planetary_positions.append({
            "planet": name,
            "sign": sign,
            "house": f"House {house_num}",
            "degrees": round(degree_in_sign, 2),
        })

    # Keep a stable, conventional planet order (Sun..Ketu) rather than dict order
    order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    planetary_positions.sort(key=lambda p: order.index(p["planet"]))

    moon_sign = next(p["sign"] for p in planetary_positions if p["planet"] == "Moon")
    sun_sign = next(p["sign"] for p in planetary_positions if p["planet"] == "Sun")
    nakshatra = _nakshatra_for_longitude(planet_longitudes["Moon"])

    # --- Dominant planet (highest degree in its sign) ---
    dominant = max(planetary_positions, key=lambda x: x["degrees"])
    dominant_planet = dominant["planet"]

    # --- Doshas (based on elemental balance of planets) ---
    sign_element_map = {
        "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
        "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
        "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
        "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
    }

    elements_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    for p in planetary_positions:
        sign = p["sign"]
        if sign in sign_element_map:
            elements_count[sign_element_map[sign]] += 1

    total = sum(elements_count.values()) or 1
    doshas = {
        "Vata": round((elements_count["Air"] / total) * 100, 1),
        "Pitta": round(((elements_count["Fire"] + elements_count["Water"]) / total) * 100, 1),
        "Kapha": round(((elements_count["Earth"] + elements_count["Water"]) / total) * 100, 1)
    }

    # --- Elements (same as above) ---
    elements = {
        "Fire": round((elements_count["Fire"] / total) * 100, 1),
        "Earth": round((elements_count["Earth"] / total) * 100, 1),
        "Air": round((elements_count["Air"] / total) * 100, 1),
        "Water": round((elements_count["Water"] / total) * 100, 1)
    }

    # --- Lucky numbers (based on dominant planet's number) ---
    planet_num_map = {
        "Sun": 1, "Moon": 2, "Jupiter": 3, "Rahu": 4,
        "Mercury": 5, "Venus": 6, "Ketu": 7, "Saturn": 8, "Mars": 9
    }
    base_num = planet_num_map.get(dominant_planet, 1)
    lucky_numbers = [n for n in [base_num, base_num+10, base_num+20, base_num+30] if n <= 50]

    # --- Lucky colors ---
    planet_color_map = {
        "Sun": "Gold", "Moon": "Silver", "Mars": "Deep Red",
        "Mercury": "Emerald", "Jupiter": "Amber", "Venus": "Rose Quartz",
        "Saturn": "Indigo", "Rahu": "Violet", "Ketu": "Deep Teal"
    }
    lucky_colors = [planet_color_map.get(dominant_planet, "Violet"), "Indigo", "Gold"]

    # --- Strengths & Challenges (based on dominant element) ---
    dominant_element = max(elements, key=elements.get)
    strength_map = {
        "Fire": ["Natural leadership and initiative", "Courage to face challenges", "Passionate about growth"],
        "Earth": ["Grounding presence", "Reliable and patient", "Practical problem solver"],
        "Air": ["Excellent communication", "Quick learning ability", "Adaptable mindset"],
        "Water": ["Deep emotional intuition", "Empathetic listener", "Creative imagination"]
    }
    challenge_map = {
        "Fire": ["Tendency to rush into decisions", "Can be impatient with slow progress"],
        "Earth": ["May resist necessary change", "Sometimes holds onto things too tightly"],
        "Air": ["Can overthink and get lost in possibilities", "Sometimes struggles to ground ideas"],
        "Water": ["May absorb others' emotions too deeply", "Tendency to avoid direct conflict"]
    }
    strengths = strength_map.get(dominant_element, ["Natural empathy", "Strong intuition"])
    challenges = challenge_map.get(dominant_element, ["Occasional overthinking", "Difficulty with boundaries"])

    return {
        "moon_sign": moon_sign,
        "sun_sign": sun_sign,
        "ascendant": ascendant,
        "nakshatra": nakshatra,
        "dominant_planet": dominant_planet,
        "planetary_positions": planetary_positions,
        "doshas": doshas,
        "elements": elements,
        "lucky_numbers": lucky_numbers,
        "lucky_colors": lucky_colors,
        "strengths": strengths,
        "challenges": challenges,
    }