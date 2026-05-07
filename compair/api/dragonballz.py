import random

from flask import Blueprint, jsonify

dragonballz_api = Blueprint("dragonballz_api", __name__, url_prefix='/api')

DRAGON_BALL_REGIONS = [
    {"name": "forest",    "lat": (35.0, 50.0),  "lon": (100.0, 140.0)},
    {"name": "desert",    "lat": (20.0, 35.0),  "lon": (-10.0, 30.0)},
    {"name": "tundra",    "lat": (60.0, 75.0),  "lon": (-150.0, -60.0)},
    {"name": "jungle",    "lat": (-10.0, 10.0), "lon": (-70.0, -50.0)},
    {"name": "islands",   "lat": (-20.0, 5.0),  "lon": (120.0, 160.0)},
    {"name": "mountains", "lat": (27.0, 35.0),  "lon": (75.0, 95.0)},
    {"name": "savanna",   "lat": (-15.0, 5.0),  "lon": (15.0, 40.0)},
]


@dragonballz_api.route('/dragonballz', methods=['GET'])
def dragonballz():
    region = random.choice(DRAGON_BALL_REGIONS)
    latitude = random.uniform(*region['lat'])
    longitude = random.uniform(*region['lon'])

    return jsonify({
        'latitude': latitude,
        'longitude': longitude,
        'region': region['name'],
    })
