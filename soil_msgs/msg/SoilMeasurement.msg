# Header for timestamp and frame
std_msgs/Header header

# GPS position
float64 latitude
float64 longitude
float64 altitude

# Soil measurements
float32 ph
float32 moisture
float32 temperature
float32 ec

# GPS fix quality (mirrors NavSatStatus)
int8 gps_status

# Lime recommendation
string recommendation
