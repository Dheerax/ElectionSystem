import requests
import logging

logger = logging.getLogger(__name__)


def fetch_location(ip, lat=None, lon=None):
    try:
        # If GPS coordinates are provided, try reverse geocoding first
        if lat is not None and lon is not None:
            headers = {
                'User-Agent': 'SmartElectionSystem/1.0 (Student Project)'
            }
            # Nominatim API for reverse geocoding
            rev_url = f'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}'
            r_gps = requests.get(rev_url, headers=headers, timeout=7)
            if r_gps.status_code == 200:
                data = r_gps.json()
                address = data.get('address', {})
                # Try to get city, town, or village
                city = address.get('city') or address.get('town') or address.get('village') or ''
                state = address.get('state', '')
                
                if city or state:
                    loc_str = f"{city}, {state}".strip(", ")
                    return f"{loc_str} (GPS)"
                    
        # Fallback to IP-based location if GPS fails or isn't provided
        if ip in ('127.0.0.1', '::1', 'localhost'):
            return 'Local/Dev'
            
        r = requests.get(f'http://ip-api.com/json/{ip}', timeout=7)
        data = r.json()
        if data.get('status') == 'success':
            city = data.get('city', '')
            region = data.get('regionName', '')
            return f"{city}, {region}".strip(', ')
        return ip
    except Exception as e:
        logger.error(f"Location fetch failed for IP {ip} / Lat {lat} / Lon {lon}: {e}")
        return ip
