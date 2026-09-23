# training1_utils.py
import math

def project_point(x, y, z, view, azimuth=45, elevation=30):
    scale = 10.0  
    ox, oy = 200, 200 

    if view == "front":    
        return (y * scale + ox, -z * scale + oy)
    elif view == "side":   
        return (x * scale + ox, -z * scale + oy)  
    elif view == "top":    
        return (x * scale + ox, y * scale + oy)   
    
    elif view in ["iso", "isometric"]:
        rad_a = math.radians(azimuth)
        rad_e = math.radians(elevation)

        x_rot = x * math.cos(rad_a) - y * math.sin(rad_a)
        y_rot = x * math.sin(rad_a) + y * math.cos(rad_a)
        z_display = y_rot * math.sin(rad_e) + z * math.cos(rad_e)
        x_display = x_rot

        return (x_display * scale + ox, -z_display * scale + oy)