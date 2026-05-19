import socket
import threading
import json
import requests
import ssl
from datetime import datetime
 
class RecipeServer:
    
   
    def __init__(self, host='localhost', port=12345, group_id='group1', use_ssl=True):
      
       
        self.host = host
        self.port = port
        self.group_id = group_id
        self.use_ssl = use_ssl
        self.socket = None
        self.base_url = "https://www.themealdb.com/api/json/v1/1"
        self.clients = []
        self.running = False
       
        # Reference cache (loaded at startup)
        self.categories_cache = []
        self.areas_cache = []
        self.ingredients_cache = []
        self.cache_lock = threading.Lock()
       
        # SSL context
        self.ssl_context = None
        if self.use_ssl:
            self.setup_ssl()
   
    def setup_ssl(self):
        try:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.ssl_context.load_cert_chain(certfile='server.crt', keyfile='server.key')
            print("[SSL] SSL/TLS enabled")
        except FileNotFoundError:
            print("[SSL] Certificate files not found. Generating self-signed certificate...")
            self.generate_self_signed_cert()
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.ssl_context.load_cert_chain(certfile='server.crt', keyfile='server.key')
            print("[SSL] Self-signed certificate generated and loaded")
        except Exception as e:
            print(f"[SSL] Failed to setup SSL: {e}")
            self.use_ssl = False
   
    def generate_self_signed_cert(self):
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            import datetime
           
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
           
            # Generate certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"State"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, u"City"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Recipe Server"),
                x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
            ])
           
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(u"localhost"),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
           
            with open("server.key", "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))
           
            with open("server.crt", "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
               
            print("[SSL] Certificate files created: server.crt, server.key")
           
        except ImportError:
            print("[SSL] cryptography library not installed. Install with: pip install cryptography")
            print("[SSL] Falling back to non-SSL mode")
            self.use_ssl = False
        except Exception as e:
            print(f"[SSL] Failed to generate certificate: {e}")
            self.use_ssl = False
   
    def load_reference_cache(self):
        print("[CACHE] Loading reference cache from TheMealDB...")
       
        try:
            response = requests.get(f"{self.base_url}/list.php?c=list", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.categories_cache = data.get('meals', [])
                print(f"[CACHE] Loaded {len(self.categories_cache)} categories")
           
            response = requests.get(f"{self.base_url}/list.php?a=list", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.areas_cache = data.get('meals', [])
                print(f"[CACHE] Loaded {len(self.areas_cache)} areas")
           
            response = requests.get(f"{self.base_url}/list.php?i=list", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.ingredients_cache = data.get('meals', [])
                print(f"[CACHE] Loaded {len(self.ingredients_cache)} ingredients")
           
            self.save_reference_cache()
            print("[CACHE] Reference cache loaded successfully")
            return True
           
        except Exception as e:
            print(f"[CACHE] Failed to load reference cache: {e}")
            return False
   
    def save_reference_cache(self):
        try:
            cache_data = {
                'categories': self.categories_cache,
                'areas': self.areas_cache,
                'ingredients': self.ingredients_cache[:50]  
            }
           
            filename = f"reference_{self.group_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            print(f"[CACHE] Reference cache saved to {filename}")
           
        except Exception as e:
            print(f"[CACHE] Failed to save reference cache: {e}")
   
    def start_server(self):
        """Start the server and begin listening for connections"""
        if not self.load_reference_cache():
            print("[ERROR] Failed to load reference cache. Server cannot start.")
            return False
       
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
           
            ssl_status = "with SSL/TLS" if self.use_ssl else "without SSL/TLS"
            print(f"\n[SERVER] Recipe Server started on {self.host}:{self.port} {ssl_status}")
            print("[SERVER] Waiting for client connections...\n")
           
            while self.running:
                try:
                    client_socket, client_address = self.socket.accept()
                   
                    if self.use_ssl and self.ssl_context:
                        try:
                            client_socket = self.ssl_context.wrap_socket(client_socket, server_side=True)
                            print(f"[SSL] Secure connection established with {client_address}")
                        except ssl.SSLError as e:
                            print(f"[SSL] SSL handshake failed with {client_address}: {e}")
                            client_socket.close()
                            continue
                   
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                   
                except Exception as e:
                    if self.running:
                        print(f"[ERROR] Error accepting connection: {e}")
                       
        except Exception as e:
            print(f"[ERROR] Failed to start server: {e}")
            return False
           
        return True
   
    def handle_client(self, client_socket, client_address):
        """Handle individual client connections"""
        username = ""
       
        try:
            username = client_socket.recv(1024).decode('utf-8').strip()
            print(f"[CONNECTION] New client connected: {username} from {client_address}")
           
            self.clients.append({
                'socket': client_socket,
                'address': client_address,
                'username': username,
                'connected_at': datetime.now()
            })
           
            while True:
                data = client_socket.recv(4096)
               
                if not data:
                    break
               
                request = json.loads(data.decode('utf-8'))
                request_type = request.get('type', 'unknown')
               
                print(f"[REQUEST] Client: {username} | Type: {request_type} | Params: {request.get('params', {})}")
               
                response = self.process_request(request, username)
                response_json = json.dumps(response)
                client_socket.send(response_json.encode('utf-8'))
                   
        except ConnectionResetError:
            print(f"[DISCONNECT] Client {username} disconnected unexpectedly")
        except Exception as e:
            print(f"[ERROR] Error handling client {username}: {e}")
        finally:
            self.remove_client(client_socket)
            try:
                client_socket.close()
                print(f"[DISCONNECT] Connection closed: {username}")
            except:
                pass
   
    def remove_client(self, client_socket):
        """Remove client from active clients list"""
        self.clients = [c for c in self.clients if c['socket'] != client_socket]
   
    def process_request(self, request, username):
        """Process client requests and return appropriate responses"""
        request_type = request.get('type')
       
        if request_type == 'search_name':
            return self.handle_search_by_name(request, username)
        elif request_type == 'filter_category':
            return self.handle_filter_by_category(request, username)
        elif request_type == 'filter_area':
            return self.handle_filter_by_area(request, username)
        elif request_type == 'filter_ingredient':
            return self.handle_filter_by_ingredient(request, username)
        elif request_type == 'random':
            return self.handle_random_recipe(request, username)
        elif request_type == 'recipe_details':
            return self.handle_recipe_details(request, username)
        elif request_type == 'list_categories':
            return self.handle_list_categories()
        elif request_type == 'list_areas':
            return self.handle_list_areas()
        elif request_type == 'list_ingredients':
            return self.handle_list_ingredients()
        else:
            return {'type': 'error', 'message': f'Unknown request type: {request_type}'}
   
    def handle_search_by_name(self, request, username):
        """Search recipes by name"""
        print(f"[SOURCE] Fetching from TheMealDB API")
       
        try:
            keyword = request.get('params', {}).get('keyword', '')
            url = f"{self.base_url}/search.php?s={keyword}"
           
            response = requests.get(url, timeout=10)
           
            if response.status_code == 200:
                data = response.json()
                meals = data.get('meals', []) or []
               
                self.save_recipe_data(username, 'search_name', data)
               
                brief_list = []
                for i, meal in enumerate(meals[:15]):
                    brief_list.append({
                        'id': i,
                        'meal_id': meal.get('idMeal'),
                        'name': meal.get('strMeal'),
                        'thumbnail': meal.get('strMealThumb')
                    })
               
                return {
                    'type': 'recipe_list',
                    'data': brief_list,
                    'full_data': meals[:15],
                    'total': len(brief_list)
                }
            else:
                return {'type': 'error', 'message': f'API request failed: {response.status_code}'}
               
        except Exception as e:
            return {'type': 'error', 'message': f'Server error: {str(e)}'}
   
    def handle_filter_by_category(self, request, username):
        """Filter recipes by category"""
        print(f"[SOURCE] Fetching from TheMealDB API")
       
        try:
            category = request.get('params', {}).get('category', '')
            url = f"{self.base_url}/filter.php?c={category}"
           
            response = requests.get(url, timeout=10)
           
            if response.status_code == 200:
                data = response.json()
                meals = data.get('meals', []) or []
               
                self.save_recipe_data(username, 'filter_category', data)
               
                brief_list = []
                for i, meal in enumerate(meals[:15]):
                    brief_list.append({
                        'id': i,
                        'meal_id': meal.get('idMeal'),
                        'name': meal.get('strMeal'),
                        'thumbnail': meal.get('strMealThumb')
                    })
               
                return {
                    'type': 'recipe_list',
                    'data': brief_list,
                    'full_data': meals[:15],
                    'total': len(brief_list)
                }
            else:
                return {'type': 'error', 'message': f'API request failed: {response.status_code}'}
               
        except Exception as e:
            return {'type': 'error', 'message': f'Server error: {str(e)}'}
   
    def handle_filter_by_area(self, request, username):
        print(f"[SOURCE] Fetching from TheMealDB API")
       
        try:
            area = request.get('params', {}).get('area', '')
            url = f"{self.base_url}/filter.php?a={area}"
           
            response = requests.get(url, timeout=10)
           
            if response.status_code == 200:
                data = response.json()
                meals = data.get('meals', []) or []
               
                self.save_recipe_data(username, 'filter_area', data)
               
                brief_list = []
                for i, meal in enumerate(meals[:15]):
                    brief_list.append({
                        'id': i,
                        'meal_id': meal.get('idMeal'),
                        'name': meal.get('strMeal'),
                        'thumbnail': meal.get('strMealThumb')
                    })
               
                return {
                    'type': 'recipe_list',
                    'data': brief_list,
                    'full_data': meals[:15],
                    'total': len(brief_list)
                }
            else:
                return {'type': 'error', 'message': f'API request failed: {response.status_code}'}
               
        except Exception as e:
            return {'type': 'error', 'message': f'Server error: {str(e)}'}
   
    def handle_filter_by_ingredient(self, request, username):
        """Filter recipes by main ingredient"""
        print(f"[SOURCE] Fetching from TheMealDB API")
       
        try:
            ingredient = request.get('params', {}).get('ingredient', '')
            url = f"{self.base_url}/filter.php?i={ingredient}"
           
            response = requests.get(url, timeout=10)
           
            if response.status_code == 200:
                data = response.json()
                meals = data.get('meals', []) or []
               
                self.save_recipe_data(username, 'filter_ingredient', data)
               
                brief_list = []
                for i, meal in enumerate(meals[:15]):
                    brief_list.append({
                        'id': i,
                        'meal_id': meal.get('idMeal'),
                        'name': meal.get('strMeal'),
                        'thumbnail': meal.get('strMealThumb')
                    })
               
                return {
                    'type': 'recipe_list',
                    'data': brief_list,
                    'full_data': meals[:15],
                    'total': len(brief_list)
                }
            else:
                return {'type': 'error', 'message': f'API request failed: {response.status_code}'}
               
        except Exception as e:
            return {'type': 'error', 'message': f'Server error: {str(e)}'}
   
    def handle_random_recipe(self, request, username):
        print(f"[SOURCE] Fetching from TheMealDB API")
       
        try:
            url = f"{self.base_url}/random.php"
           
            response = requests.get(url, timeout=10)
           
            if response.status_code == 200:
                data = response.json()
                meals = data.get('meals', [])
               
                self.save_recipe_data(username, 'random', data)
               
                if meals:
                    meal = meals[0]
                    return {
                        'type': 'recipe_details',
                        'data': self.format_full_recipe(meal)
                    }
                else:
                    return {'type': 'error', 'message': 'No recipe found'}
            else:
                return {'type': 'error', 'message': f'API request failed: {response.status_code}'}
               
        except Exception as e:
            return {'type': 'error', 'message': f'Server error: {str(e)}'}
   
    def handle_recipe_details(self, request, username):
        """Get full details for a specific recipe"""
        print(f"[SOURCE] Fetching from TheMealDB API")
       
        try:
            meal_id = request.get('params', {}).get('meal_id', '')
            url = f"{self.base_url}/lookup.php?i={meal_id}"
           
            response = requests.get(url, timeout=10)
           
            if response.status_code == 200:
                data = response.json()
                meals = data.get('meals', [])
               
                self.save_recipe_data(username, 'recipe_details', data)
               
                if meals:
                    meal = meals[0]
                    return {
                        'type': 'recipe_details',
                        'data': self.format_full_recipe(meal)
                    }
                else:
                    return {'type': 'error', 'message': 'Recipe not found'}
            else:
                return {'type': 'error', 'message': f'API request failed: {response.status_code}'}
               
        except Exception as e:
            return {'type': 'error', 'message': f'Server error: {str(e)}'}
   
    def format_full_recipe(self, meal):
        """Format full recipe details"""
        ingredients = []
        for i in range(1, 21):
            ingredient = meal.get(f'strIngredient{i}', '')
            measure = meal.get(f'strMeasure{i}', '')
            if ingredient and ingredient.strip():
                ingredients.append(f"{measure.strip()} {ingredient.strip()}")
       
        return {
            'name': meal.get('strMeal', 'Unknown'),
            'category': meal.get('strCategory', 'Unknown'),
            'area': meal.get('strArea', 'Unknown'),
            'instructions': meal.get('strInstructions', 'No instructions available'),
            'ingredients': ingredients,
            'youtube': meal.get('strYoutube', 'N/A'),
            'source': meal.get('strSource', 'N/A'),
            'tags': meal.get('strTags', 'N/A'),
            'thumbnail': meal.get('strMealThumb', '')
        }
   
    def handle_list_categories(self):
        """Return categories from cache"""
        print(f"[SOURCE] Serving from cache")
       
        with self.cache_lock:
            formatted = [{'name': cat.get('strCategory', ''),
                         'description': ''} for cat in self.categories_cache]
       
        return {
            'type': 'reference_list',
            'data': formatted,
            'total': len(formatted)
        }
   
    def handle_list_areas(self):
        """Return areas from cache"""
        print(f"[SOURCE] Serving from cache")
       
        with self.cache_lock:
            formatted = [{'name': area.get('strArea', '')} for area in self.areas_cache]
       
        return {
            'type': 'reference_list',
            'data': formatted,
            'total': len(formatted)
        }
   
    def handle_list_ingredients(self):
        """Return ingredients from cache"""
        print(f"[SOURCE] Serving from cache")
       
        with self.cache_lock:
            formatted = [{'name': ing.get('strIngredient', '')} for ing in self.ingredients_cache]
       
        return {
            'type': 'reference_list',
            'data': formatted,
            'total': len(formatted)
        }
   
    def save_recipe_data(self, username, option, data):
        """Save recipe data to JSON file"""
        try:
            filename = f"{username}_{option}_{self.group_id}.json"
           
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
               
        except Exception as e:
            print(f"[ERROR] Failed to save recipe data: {e}")
   
    def stop_server(self):
        """Stop the server and close all connections"""
        print("\n[SERVER] Shutting down server...")
        self.running = False
       
        # Close all client connections
        for client in self.clients:
            try:
                client['socket'].close()
            except:
                pass
       
        # Close server socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
       
        print("[SERVER] Server stopped")
 
def main():
    """Main function to start the recipe server"""
    import argparse
   
    parser = argparse.ArgumentParser(description='Recipe Discovery Server')
    parser.add_argument('--group-id', default='group1', help='Group identifier')
    parser.add_argument('--port', type=int, default=12345, help='Server port')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL/TLS encryption')
   
    args = parser.parse_args()
   
    server = RecipeServer(
        group_id=args.group_id,
        port=args.port,
        use_ssl=not args.no_ssl
    )
   
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n[SERVER] Server shutdown requested")
    finally:
        server.stop_server()
 
if __name__ == "__main__":
    main()
 
 
