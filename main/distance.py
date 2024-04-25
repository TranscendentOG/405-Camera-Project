from math import sin, cos, atan, atan2, pi

RAD2DEG = 180 / pi
DEG2RAD = 1 / RAD2DEG

R = (6378137.0 + 6356752.314245) / 2  # m, An average radius of earth, average of semi- major and minor axes of WGS84

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

    psi1 = d_lat * DEG2RAD  # rad
    lambda1 = d_lon * DEG2RAD  # rad

    psi2 = a_lat * DEG2RAD  # rad
    lambda2 = a_lon * DEG2RAD  # rad
    
    y = sin(lambda2-lambda1)*cos(psi2)
    x = cos(psi1)*sin(psi2) - sin(psi1)*cos(psi2)*cos(lambda2-lambda1)
    
    theta = atan2(y,x)
    
    bearing = (theta*180/pi + 360) % 360

    return bearing

if __name__ == "__main__":
        
    bearing = find_bearing(d_lat=45.630, d_lon=-122.610, a_lat=45.722076, a_lon=-122.565017)
    print(bearing)