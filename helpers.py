import requests
import logging

logger = logging.getLogger(__name__)


def fetch_location(ip):
    try:
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
        logger.error(f"Location fetch failed for {ip}: {e}")
        return ip
