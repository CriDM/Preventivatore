import urllib.request
import urllib.error
import json
import base64
import time
from typing import List, Dict

def fetch_woocommerce_products(url: str, consumer_key: str, consumer_secret: str, update_callback=None) -> List[Dict]:
    """
    Fetches products from a WooCommerce REST API using Basic Auth.
    Returns a list of dictionaries with product details.
    Uses basic pagination.
    """
    base_url = url.rstrip('/')
    if not base_url.startswith('http'):
        base_url = 'https://' + base_url

    api_url = f"{base_url}/wp-json/wc/v3/products"

    auth_string = f"{consumer_key}:{consumer_secret}"
    auth_bytes = auth_string.encode('utf-8')
    base64_auth = base64.b64encode(auth_bytes).decode('utf-8')

    headers = {
        'Authorization': f'Basic {base64_auth}',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    products = []
    page = 1
    per_page = 50

    while True:
        try:
            req_url = f"{api_url}?page={page}&per_page={per_page}"
            if update_callback:
                update_callback(f"Scaricando pagina {page}...")

            req = urllib.request.Request(req_url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    if update_callback:
                        update_callback(f"Errore HTTP: {response.status}")
                    break

                data = json.loads(response.read().decode('utf-8'))

                if not data:
                    break # No more products

                for item in data:
                    # Simplify the structure for our cache
                    try:
                        price = float(item.get('price') or 0.0)
                    except (ValueError, TypeError):
                        price = 0.0

                    products.append({
                        'id': item.get('id'),
                        'name': item.get('name', ''),
                        'price': price,
                        'tax_status': item.get('tax_status', 'taxable'),
                        'tax_class': item.get('tax_class', '')
                    })

                if len(data) < per_page:
                    break # Last page

                page += 1

        except urllib.error.URLError as e:
            if update_callback:
                update_callback(f"Errore di rete: {str(e)}")
            break
        except json.JSONDecodeError:
            if update_callback:
                update_callback("Errore nel parsing della risposta del server.")
            break
        except Exception as e:
            if update_callback:
                update_callback(f"Errore inatteso: {str(e)}")
            break

    if update_callback:
        update_callback(f"Completato! Trovati {len(products)} prodotti.")

    return products

if __name__ == '__main__':
    pass
