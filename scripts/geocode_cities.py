"""Geocode Indian cities for BoBBreach Leaflet map.
Uses geonamescache for known cities, Nominatim (OSM) as fallback.
"""
import json, time, re, sys
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# Load city->IFSC mapping
with open("/home/workspace/BoBBreach/data/cities.json") as f:
    cities_raw = json.load(f)  # {city_name: [ifsc_list]}

# Load branches for state info
with open("/home/workspace/BoBBreach/data/branches.min.json") as f:
    branches = json.load(f)  # [{i: ifsc, b: branch, c: city, s: state, t: type}]

# Build city->state mapping from branch data
city_state = {}
for b in branches:
    city = b["c"]
    state = b["s"]
    if city not in city_state:
        city_state[city] = state

# Count branches per city
city_counts = {}
for b in branches:
    city = b["c"]
    city_counts[city] = city_counts.get(city, 0) + 1

# Quick Indian city coordinate mapping (major cities we know precisely)
KNOWN_COORDS = {
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.7041, 77.1025),
    "Bangalore": (12.9716, 77.5946),
    "Bengaluru": (12.9716, 77.5946),
    "Hyderabad": (17.3850, 78.4867),
    "Ahmedabad": (23.0225, 72.5714),
    "Ahmadabad": (23.0225, 72.5714),
    "Chennai": (13.0827, 80.2707),
    "Madras": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Calcutta": (22.5726, 88.3639),
    "Pune": (18.5204, 73.8567),
    "Jaipur": (26.9124, 75.7873),
    "Lucknow": (26.8467, 80.9462),
    "Surat": (21.1702, 72.8311),
    "Kanpur": (26.4499, 80.3319),
    "Nagpur": (21.1458, 79.0882),
    "Indore": (22.7196, 75.8577),
    "Bhopal": (23.2599, 77.4126),
    "Visakhapatnam": (17.6868, 83.2185),
    "Vizianagaram": (18.1067, 83.3955),
    "Patna": (25.5941, 85.1376),
    "Vadodara": (22.3072, 73.1812),
    "Baroda": (22.3072, 73.1812),
    "Ghaziabad": (28.6692, 77.4538),
    "Ludhiana": (30.9010, 75.8573),
    "Agra": (27.1767, 78.0081),
    "Nashik": (19.9975, 73.7898),
    "Nasik": (19.9975, 73.7898),
    "Faridabad": (28.4089, 77.3178),
    "Meerut": (28.9845, 77.7064),
    "Rajkot": (22.3039, 70.8022),
    "Varanasi": (25.3176, 82.9739),
    "Srinagar": (34.0837, 74.7973),
    "Aurangabad": (19.8762, 75.3433),
    "Dhanbad": (23.7957, 86.4304),
    "Amritsar": (31.6340, 74.8723),
    "Navi Mumbai": (19.0330, 73.0297),
    "Allahabad": (25.4358, 81.8463),
    "Prayagraj": (25.4358, 81.8463),
    "Ranchi": (23.3441, 85.3096),
    "Howrah": (22.5958, 88.2636),
    "Coimbatore": (11.0168, 76.9558),
    "Jabalpur": (23.1815, 79.9864),
    "Gwalior": (26.2183, 78.1828),
    "Vijayawada": (16.5062, 80.6480),
    "Jodhpur": (26.2389, 73.0243),
    "Madurai": (9.9252, 78.1198),
    "Raipur": (21.2514, 81.6296),
    "Kota": (25.2138, 75.8648),
    "Guwahati": (26.1445, 91.7362),
    "Chandigarh": (30.7333, 76.7794),
    "Thiruvananthapuram": (8.5241, 76.9366),
    "Trivandrum": (8.5241, 76.9366),
    "Mysore": (12.2958, 76.6394),
    "Mysuru": (12.2958, 76.6394),
    "Bhubaneswar": (20.2961, 85.8245),
    "Salem": (11.6643, 78.1460),
    "Tiruchirappalli": (10.7905, 78.7047),
    "Trichy": (10.7905, 78.7047),
    "Kochi": (9.9312, 76.2673),
    "Cochin": (9.9312, 76.2673),
    "Kozhikode": (11.2588, 75.7804),
    "Calicut": (11.2588, 75.7804),
    "Jamshedpur": (22.8046, 86.2029),
    "Dehradun": (30.3165, 78.0322),
    "Udaipur": (24.5854, 73.7125),
    "Mangalore": (12.9141, 74.8560),
    "Mangaluru": (12.9141, 74.8560),
    "Warangal": (17.9784, 79.5941),
    "Gaya": (24.7955, 84.9994),
    "Tirupati": (13.6288, 79.4192),
    "Gorakhpur": (26.7606, 83.3732),
    "Mathura": (27.4924, 77.6737),
    "Kollam": (8.8932, 76.6141),
    "Cuttack": (20.4625, 85.8830),
    "Jalandhar": (31.3260, 75.5762),
    "Ajmer": (26.4499, 74.6399),
    "Thrissur": (10.5276, 76.2144),
    "Alwar": (27.5662, 76.6102),
    "Bikaner": (28.0229, 73.3119),
    "Bhiwandi": (19.2952, 73.0589),
    "Muzaffarpur": (26.1225, 85.3908),
    "Bhilai": (21.1938, 81.3509),
    "Noida": (28.5355, 77.3910),
    "Saharanpur": (29.9679, 77.5451),
    "Guntur": (16.3067, 80.4365),
    "Bareilly": (28.3670, 79.4304),
    "Moradabad": (28.8386, 78.7733),
    "Kolhapur": (16.7050, 74.2433),
    "Shimla": (31.1048, 77.1734),
    "Siliguri": (26.7271, 88.3953),
    "Panaji": (15.4909, 73.8278),
    "Imphal": (24.8170, 93.9368),
    "Shillong": (25.5788, 91.8933),
    "Agartala": (23.8315, 91.2868),
    "Aizawl": (23.7271, 92.7176),
    "Aizawal": (23.7271, 92.7176),
    "Kohima": (25.6751, 94.1086),
    "Gangtok": (27.3389, 88.6065),
    "Itanagar": (27.0844, 93.6053),
    "Dispur": (26.1392, 91.7909),
    "Thane": (19.2183, 72.9781),
    "Tirunelveli": (8.7139, 77.7567),
    "Nellore": (14.4426, 79.9865),
    "Rohtak": (28.8955, 76.6066),
    "Haldwani": (29.2225, 79.5286),
    "Hisar": (29.1492, 75.7217),
    "Hissar": (29.1492, 75.7217),
    "Karnal": (29.6857, 76.9905),
    "Panipat": (29.3909, 76.9635),
    "Sonipat": (28.9931, 77.0151),
    "Yamunanagar": (30.1290, 77.2674),
    "Ujjain": (23.1765, 75.7885),
    "Sagar": (23.8388, 78.7378),
    "Rourkela": (22.2604, 84.8536),
    "Puri": (19.8134, 85.8315),
    "Berhampur": (19.3121, 84.7930),
    "Brahmapur": (19.3121, 84.7930),
    "Sambalpur": (21.4669, 83.9812),
    "Kakinada": (16.9591, 82.2381),
    "Rajahmundry": (17.0005, 81.8040),
    "Eluru": (16.7101, 81.0951),
    "Machilipatnam": (16.1875, 81.1383),
    "Ongole": (15.5039, 80.0522),
    "Anantapur": (14.6880, 77.5975),
    "Anantapuram": (14.6880, 77.5975),
    "Kurnool": (15.8281, 78.0373),
    "Tirupur": (11.1085, 77.3411),
    "Erode": (11.3410, 77.7172),
    "Vellore": (12.9165, 79.1325),
    "Tuticorin": (8.7642, 78.1348),
    "Thoothukudi": (8.7642, 78.1348),
    "Dindigul": (10.3673, 77.9803),
    "Nagercoil": (8.1833, 77.4119),
    "Kannur": (11.8745, 75.3704),
    "Kasaragod": (12.4923, 74.9895),
    "Palakkad": (10.7867, 76.6548),
    "Alappuzha": (9.4981, 76.3388),
    "Alapuzzha": (9.4981, 76.3388),
    "Port Blair": (11.6234, 92.7265),
    "Silvassa": (20.2740, 72.9983),
    "Daman": (20.4283, 72.8397),
    "Diu": (20.7151, 70.9876),
    "Kavaratti": (10.5590, 72.6368),
    "Leh": (34.1526, 77.5771),
    "Kargil": (34.5539, 76.1349),
    "Haridwar": (29.9457, 78.1642),
    "Rishikesh": (30.0869, 78.2676),
    "Ayodhya": (26.7921, 82.1985),
    "Dwarka": (22.2442, 68.9685),
    "Somnath": (20.8829, 70.3973),
    "Rameswaram": (9.2876, 79.3129),
    "Tiruvannamalai": (12.2253, 79.0747),
    "Chidambaram": (11.3961, 79.7049),
    "Kanchipuram": (12.8342, 79.7036),
    "Kumbakonam": (10.9617, 79.3881),
    "Mayiladuthurai": (11.1000, 79.6500),
    "Sirkazhi": (11.2333, 79.7333),
    "Nagapattinam": (10.7692, 79.8386),
    "Thanjavur": (10.7870, 79.1380),
    "Tanjore": (10.7870, 79.1380),
    "Pattukkottai": (10.4333, 79.3167),
    "Pudukkottai": (10.3833, 78.8167),
    "Sivaganga": (9.8667, 78.4833),
    "Ramanathapuram": (9.3667, 78.8333),
    "Thenkasi": (8.9667, 77.3000),
    "Thiruvananthapuram": (8.5241, 76.9366),
    "Kanyakumari": (8.0803, 77.5419),
    "Neyveli": (11.5333, 79.4833),
    "Villupuram": (11.9333, 79.4833),
    "Cuddalore": (11.7500, 79.7500),
    "Ariyalur": (11.1333, 79.0833),
    "Perambalur": (11.2333, 78.8833),
    "Karur": (10.9500, 78.0833),
    "Namakkal": (11.2167, 78.1667),
    "Dharmapuri": (12.1167, 78.1667),
    "Krishnagiri": (12.5167, 78.2167),
    "Hosur": (12.7333, 77.8167),
    "Ranipet": (12.9333, 79.3333),
    "Tiruvallur": (13.1500, 79.9000),
    "Gummidipoondi": (13.4000, 80.1167),
    "Adambakkam": (13.0011, 80.1794),
    "Ambattur": (13.1143, 80.1548),
    "Avadi": (13.1155, 80.1011),
    "Tambaram": (12.9249, 80.1000),
    "Chromepet": (12.9516, 80.1400),
    "Pallavaram": (12.9683, 80.1500),
    "Chengalpattu": (12.6833, 79.9833),
    "Kanchipuram": (12.8342, 79.7036),
    "Tindivanam": (12.2333, 79.6500),
    "Karaikal": (10.9167, 79.8333),
    "Puducherry": (11.9417, 79.8083),
    "Pondicherry": (11.9417, 79.8083),
    "Mahe": (11.7000, 75.5333),
    "Jalpaiguri": (26.5167, 88.7333),
    "Malda": (25.0167, 88.1500),
    "Murshidabad": (24.1833, 88.2667),
    "Baharampur": (24.1000, 88.2500),
    "Krishnanagar": (23.4000, 88.5000),
    "Barasat": (22.6833, 88.4500),
    "Barrackpore": (22.7667, 88.3667),
    "Dum Dum": (22.6167, 88.4333),
    "Kalyani": (22.9833, 88.4333),
    "Habra": (22.8333, 88.6333),
    "Basirhat": (22.6500, 88.8667),
    "Bongaon": (23.0500, 88.8167),
    "Nabadwip": (23.4167, 88.3667),
    "Katwa": (23.6500, 88.1333),
    "Bardhaman": (23.2333, 87.8667),
    "Durgapur": (23.5500, 87.3167),
    "Asansol": (23.6833, 86.9667),
    "Bankura": (23.2333, 87.0667),
    "Midnapore": (22.4167, 87.3167),
    "Kharagpur": (22.3300, 87.3200),
    "Purulia": (23.3333, 86.3667),
    "Contai": (21.7833, 87.7500),
    "Haldia": (22.0667, 88.0667),
    "Raiganj": (25.6167, 88.1167),
    "Balurghat": (25.2167, 88.7667),
    "Cooch Behar": (26.3167, 89.4333),
    "Alipurduar": (26.4833, 89.5167),
    "Darjeeling": (27.0500, 88.2667),
    "Baharampur": (24.1000, 88.2500),
    "Dehri": (24.8667, 84.1833),
    "Sasaram": (24.9500, 84.0167),
    "Buxar": (25.5667, 83.9833),
    "Motihari": (26.6500, 84.9167),
    "Bettiah": (26.8000, 84.5000),
    "Chapra": (25.7833, 84.7333),
    "Siwan": (26.2167, 84.3667),
    "Gopalganj": (26.4667, 84.4333),
    "Munger": (25.3833, 86.4667),
    "Bhagalpur": (25.2500, 87.0167),
    "Saharsa": (25.8833, 86.6000),
    "Supaul": (25.9333, 86.2500),
    "Purnia": (25.7833, 87.4667),
    "Araria": (26.1500, 87.5167),
    "Kishanganj": (26.1000, 87.9500),
    "Katihar": (25.5333, 87.5833),
    "Begusarai": (25.4167, 86.1333),
    "Khagaria": (25.5000, 86.4667),
    "Sitamarhi": (26.6000, 85.4833),
    "Sheohar": (26.5167, 85.3000),
    "Darbhanga": (26.1667, 85.9000),
    "Samastipur": (25.8667, 85.7833),
    "Muzaffarpur": (26.1225, 85.3908),
    "Vaishali": (25.9833, 85.1167),
    "Patna": (25.5941, 85.1376),
    "Nalanda": (25.1833, 85.5167),
    "Nawada": (24.8833, 85.5333),
    "Jamui": (24.9167, 86.2167),
    "Jehanabad": (25.2167, 84.9833),
    "Arwal": (25.2500, 84.6667),
    "AurangabadBR": (24.7500, 84.3667),
    "Gaya": (24.7955, 84.9994),
    "Rohtas": (24.9500, 84.0167),
    "Kaimur": (25.0500, 83.6167),
    "Bhabua": (25.0500, 83.6167),
    "Lakhisarai": (25.1667, 86.0833),
    "Sheikhpura": (25.1333, 85.8500),
    "Nalanda": (25.1833, 85.5167),
    "Madhubani": (26.3667, 86.0833),
    "Supaul": (25.9333, 86.2500),
    "Bank": (23.2333, 87.0667),
    "Greater Mumbai": (19.0760, 72.8777),
    "Greater Noida": (28.4961, 77.5360),
    "Gautam Buddha Nagar": (28.4961, 77.5360),
    "North Delhi": (28.7041, 77.1025),
    "South Delhi": (28.7041, 77.1025),
    "East Delhi": (28.7041, 77.1025),
    "West Delhi": (28.7041, 77.1025),
    "Central Delhi": (28.7041, 77.1025),
    "New Delhi": (28.6139, 77.2090),
    "Shahdara": (28.6833, 77.2833),
    "Jabalpur": (23.1815, 79.9864),
    "Jahangirpur": (28.1833, 77.7167),
    "Jalna": (19.8333, 75.8833),
    "Jhalawar": (24.5833, 76.1500),
    "Junagadh": (21.5167, 70.4667),
    "Kalahandi": (19.8833, 83.1167),
    "Kamrup": (26.1333, 91.7833),
    "Kanchipuram": (12.8342, 79.7036),
    "Kangra": (32.1000, 76.2667),
    "Kannauj": (27.0500, 79.9167),
    "Kapurthala": (31.3833, 75.3833),
    "Karauli": (26.4833, 77.0167),
    "Karbi Anglong": (26.2333, 92.7167),
    "Kargil": (34.5539, 76.1349),
    "Karnal": (29.6857, 76.9905),
    "Kasaragod": (12.4923, 74.9895),
    "Kathua": (32.3667, 75.5167),
    "Kaushambi": (25.5333, 81.3833),
    "Kendrapara": (20.5000, 86.4167),
    "Keonjhar": (21.6333, 85.5833),
    "Khagaria": (25.5000, 86.4667),
    "Khammam": (17.2500, 80.1500),
    "Khandwa": (21.8167, 76.3333),
    "Khargone": (21.8167, 75.6167),
    "Kheda": (22.7500, 72.6833),
    "Koderma": (24.4667, 85.6000),
    "Kokrajhar": (26.4000, 90.2667),
    "Kolar": (13.1333, 78.1333),
    "Kolkata": (22.5726, 88.3639),
    "Kulgam": (33.6333, 75.0167),
    "Kullu": (31.9667, 77.1000),
    "Kupwara": (34.5167, 74.2500),
    "Kurnool": (15.8281, 78.0373),
    "Kurukshetra": (29.9667, 76.8333),
    "Lakhimpur": (27.2333, 94.1167),
    "Lalitpur": (24.6833, 78.4167),
    "Latehar": (23.7500, 84.5000),
    "Latur": (18.4000, 76.5833),
    "Lawngtlai": (22.5333, 92.9000),
    "Lohardaga": (23.4333, 84.6833),
    "Lakhisarai": (25.1667, 86.0833),
}

geolocator = Nominatim(user_agent="bobbreach-leaflet-v1")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1, max_retries=2)

cities = list(cities_raw.keys())
result = {}
total = len(cities)

for idx, city in enumerate(cities):
    # Check known coords first
    if city in KNOWN_COORDS:
        result[city] = KNOWN_COORDS[city]
        sys.stdout.write(f"\r[{idx+1}/{total}] {city} (known) ✓")
        sys.stdout.flush()
        continue

    state = city_state.get(city, "")
    query = f"{city}, {state}, India" if state else f"{city}, India"

    try:
        location = geocode(query)
        if location:
            result[city] = (round(location.latitude, 5), round(location.longitude, 5))
            sys.stdout.write(f"\r[{idx+1}/{total}] {city}, {state} ✓")
        else:
            # Try without state
            location = geocode(f"{city}, India")
            if location:
                result[city] = (round(location.latitude, 5), round(location.longitude, 5))
                sys.stdout.write(f"\r[{idx+1}/{total}] {city} (no state) ✓")
            else:
                result[city] = None
                sys.stdout.write(f"\r[{idx+1}/{total}] {city}, {state} ✗")
        sys.stdout.flush()
    except Exception as e:
        result[city] = None
        sys.stdout.write(f"\r[{idx+1}/{total}] {city} ERROR: {e}")
        sys.stdout.flush()

print(f"\n\nGeocoded {sum(1 for v in result.values() if v)}/{total} cities")

# Simplify: compress as [lat, lng] arrays, null for missing
output = {}
for city, coords in result.items():
    if coords:
        output[city] = {"l": coords[0], "n": coords[1]}
    else:
        output[city] = None

with open("/home/workspace/BoBBreach/data/coords.min.json", "w") as f:
    json.dump(output, f, separators=(",", ":"))

print(f"Saved to data/coords.min.json ({len(output)} cities)")
