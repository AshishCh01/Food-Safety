"""Static reference data for Maharashtra's 6 divisions and 36 districts.

Used by seed_districts.py and by tests. Keeping this as data (not
per-district code paths) matches the architectural rule that the system
must support all districts through data, not hard-coded logic.
"""

DIVISIONS = [
    {"name": "Konkan", "code": "KON"},
    {"name": "Pune", "code": "PUN"},
    {"name": "Nashik", "code": "NAS"},
    {"name": "Chhatrapati Sambhajinagar", "code": "AUR"},
    {"name": "Amravati", "code": "AMR"},
    {"name": "Nagpur", "code": "NAG"},
]

# Each entry: (district name, district code, division code, centroid latitude, centroid longitude)
#
# Coordinates are the approximate district-headquarters location, not a
# surveyed polygon centroid - the project has no district boundary shapefile
# yet. They are used only for nearest-district resolution of a reported
# citizen location (see app/services/district_service.py); see
# docs/DEVELOPMENT_ROADMAP.md Phase 5 follow-up notes for replacing this with
# true point-in-polygon lookup once real boundary geometry is available.
DISTRICTS = [
    # Konkan division
    ("Mumbai City", "MUM", "KON", 18.9388, 72.8354),
    ("Mumbai Suburban", "MSB", "KON", 19.0596, 72.8295),
    ("Thane", "THN", "KON", 19.2183, 72.9781),
    ("Palghar", "PAL", "KON", 19.6970, 72.7650),
    ("Raigad", "RAI", "KON", 18.5158, 73.1822),
    ("Ratnagiri", "RTG", "KON", 16.9902, 73.3120),
    ("Sindhudurg", "SDG", "KON", 16.3667, 73.6833),
    # Pune division
    ("Pune", "PUN", "PUN", 18.5204, 73.8567),
    ("Satara", "SAT", "PUN", 17.6805, 74.0183),
    ("Sangli", "SAN", "PUN", 16.8524, 74.5815),
    ("Solapur", "SOL", "PUN", 17.6599, 75.9064),
    ("Kolhapur", "KOL", "PUN", 16.7050, 74.2433),
    # Nashik division
    ("Nashik", "NAS", "NAS", 19.9975, 73.7898),
    ("Dhule", "DHU", "NAS", 20.9042, 74.7749),
    ("Nandurbar", "NDB", "NAS", 21.3702, 74.2400),
    ("Jalgaon", "JAL", "NAS", 21.0077, 75.5626),
    ("Ahmednagar", "AHM", "NAS", 19.0952, 74.7496),
    # Chhatrapati Sambhajinagar (Aurangabad) division
    ("Chhatrapati Sambhajinagar", "CSN", "AUR", 19.8762, 75.3433),
    ("Jalna", "JLN", "AUR", 19.8410, 75.8864),
    ("Beed", "BEE", "AUR", 18.9894, 75.7601),
    ("Latur", "LAT", "AUR", 18.4088, 76.5604),
    ("Dharashiv", "DHS", "AUR", 18.1860, 76.0419),
    ("Nanded", "NAD", "AUR", 19.1383, 77.3210),
    ("Parbhani", "PAR", "AUR", 19.2704, 76.7601),
    ("Hingoli", "HIN", "AUR", 19.7173, 77.1497),
    # Amravati division
    ("Amravati", "AMR", "AMR", 20.9374, 77.7796),
    ("Akola", "AKO", "AMR", 20.7002, 77.0082),
    ("Washim", "WAS", "AMR", 20.1097, 77.1333),
    ("Buldhana", "BUL", "AMR", 20.5292, 76.1809),
    ("Yavatmal", "YAV", "AMR", 20.3888, 78.1204),
    # Nagpur division
    ("Nagpur", "NGP", "NAG", 21.1458, 79.0882),
    ("Wardha", "WAR", "NAG", 20.7453, 78.6022),
    ("Bhandara", "BHA", "NAG", 21.1667, 79.6500),
    ("Gondia", "GON", "NAG", 21.4602, 80.1922),
    ("Chandrapur", "CHA", "NAG", 19.9615, 79.2961),
    ("Gadchiroli", "GAD", "NAG", 20.1809, 80.0021),
]

assert len(DIVISIONS) == 6
assert len(DISTRICTS) == 36
assert len({d["code"] for d in DIVISIONS}) == 6
assert len({code for _, code, _, _, _ in DISTRICTS}) == 36
