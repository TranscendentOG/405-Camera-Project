from math import sin, cos, atan, atan2, pi

RAD2DEG = 180 / pi
DEG2RAD = 1 / RAD2DEG

R = (6378137.0 + 6356752.314245) / 2  # m, An average radius of earth, average of semi- major and minor axes of WGS84

d_alt = 309 * 0.3048  # m, Height of Justin and JP's neighborhood, https://en-us.topographic-map.com/


def find_pitch(d_lat, d_lon, d_alt, a_lat, a_lon, a_alt):
    """Returns the angle from the horizon to the aircraft, assuming a flat earth."""
    
    
    alt_delta = a_alt - d_alt  # m
    lat_delta = (d_lat - a_lat) * DEG2RAD  # degrees
    lon_delta = (d_lon - a_lon) * DEG2RAD  # degrees

    L = ((R * sin(lat_delta)) ** 2 + (R * sin(lon_delta)) ** 2) ** 0.5  # m, Flat earth distance from the device to the plane

    pitch = atan(alt_delta / L) * RAD2DEG  # degrees

    return pitch


def find_bearing(d_lat, d_lon, a_lat, a_lon):
    """Find the bearing between the device (d_lat, d_lon) and aircraft (a_lat, a_lon). Returns the difference in angle, in degrees, clockwise starting at the north."""
    # https://math.stackexchange.com/questions/2573800/derivation-of-formula-for-heading-to-another-point-lat-long

    psi_1 = d_lat * DEG2RAD  # rad
    lambda_1 = d_lon * DEG2RAD  # rad

    psi_2 = a_lat * DEG2RAD  # rad
    lambda_2 = a_lon * DEG2RAD  # rad

    lambda_delta = lambda_2 - lambda_1

    x = sin(lambda_delta) * cos(lambda_2)
    y = cos(psi_1) * sin(psi_2) - sin(psi_1) * cos(psi_2) * cos(lambda_delta)
    bearing = atan2(x, y) * RAD2DEG  # Degrees, Bearing, clockwise from the north

    return bearing
