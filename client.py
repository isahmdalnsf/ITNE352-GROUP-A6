import socket
import json
import ssl
 
class RecipeClient:
    """
    RecipeClient Class - Connects to server and handles user interactions
    """
   
    def __init__(self, host='localhost', port=12345, use_ssl=True):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.socket = None
        self.username = ""
        self.ssl_context = None
       
        if self.use_ssl:
            self.setup_ssl()
   
    def setup_ssl(self):
        """Setup SSL context for secure connections"""
        try:
            self.ssl_context = ssl.create_default_context()
            # For self-signed certificates, disable verification (for testing only)
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
            print("[SSL] SSL/TLS enabled (certificate verification disabled for testing)")
        except Exception as e:
            print(f"[SSL] Failed to setup SSL: {e}")
            self.use_ssl = False
   
    def connect(self):
        """Establish connection to the recipe server"""
        try:
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
           
            # Wrap socket with SSL if enabled
            if self.use_ssl and self.ssl_context:
                try:
                    self.socket = self.ssl_context.wrap_socket(raw_socket, server_hostname=self.host)
                    print("[SSL] Secure connection established")
                except ssl.SSLError as e:
                    print(f"[SSL] SSL handshake failed: {e}")
                    print("[SSL] Falling back to non-SSL connection")
                    self.socket = raw_socket
                    self.use_ssl = False
            else:
                self.socket = raw_socket
           
            self.socket.connect((self.host, self.port))
           
            if not self.username:
                self.username = input("Enter your username: ")
           
            # Send username to server
            self.socket.send(self.username.encode('utf-8'))
           
            ssl_status = "(SSL/TLS)" if self.use_ssl else "(No SSL)"
            print(f"\nConnected to Recipe Server as {self.username} {ssl_status}")
            return True
           
        except ConnectionRefusedError:
            print("Connection refused. Is the server running?")
            return False
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
   
    def send_request(self, request_data):
        """Send request to server and receive response"""
        try:
            request_json = json.dumps(request_data)
            self.socket.send(request_json.encode('utf-8'))
           
            response_data = self.socket.recv(8192)
            response = json.loads(response_data.decode('utf-8'))
            return response
               
        except ConnectionResetError:
            print("Connection lost")
            return None
        except BrokenPipeError:
            print("Connection broken")
            return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None
   
    def display_main_menu(self):
        """Display main menu"""
        print("\n" + "="*50)
        print("RECIPE DISCOVERY SYSTEM - MAIN MENU")
        print("="*50)
        print("1. Browse recipes")
        print("2. Reference lists")
        print("3. Quit")
        print("="*50)
        return input("Select option (1-3): ").strip()
   
    def display_recipes_menu(self):
        """Display recipes menu"""
        print("\n" + "="*50)
        print("RECIPES MENU")
        print("="*50)
        print("1. Search by name")
        print("2. Filter by category")
        print("3. Filter by area")
        print("4. Filter by main ingredient")
        print("5. Random recipe")
        print("6. Back to main menu")
        print("="*50)
        return input("Select option (1-6): ").strip()
   
    def display_reference_menu(self):
        """Display reference menu"""
        print("\n" + "="*50)
        print("REFERENCE MENU")
        print("="*50)
        print("1. List all categories")
        print("2. List all areas")
        print("3. List all ingredients")
        print("4. Back to main menu")
        print("="*50)
        return input("Select option (1-4): ").strip()
   
    def handle_search_by_name(self):
        """Handle search by name"""
        print("\nSEARCH BY NAME")
        keyword = input("Enter recipe name keyword: ").strip()
       
        if not keyword:
            print("No keyword entered")
            return
       
        request = {
            'type': 'search_name',
            'params': {'keyword': keyword}
        }
       
        response = self.send_request(request)
        if response:
            if response.get('type') == 'error':
                print(f"Error: {response.get('message')}")
            else:
                self.display_recipe_list(response)
   
    def handle_filter_by_category(self):
        """Handle filter by category"""
        print("\nFILTER BY CATEGORY")
        categories = ['Beef', 'Chicken', 'Seafood', 'Vegetarian', 'Dessert', 'Pasta', 'Breakfast']
       
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat}")
       
        try:
            choice = int(input("Select category (1-7): "))
            if 1 <= choice <= 7:
                category = categories[choice-1]
               
                request = {
                    'type': 'filter_category',
                    'params': {'category': category}
                }
               
                response = self.send_request(request)
                if response:
                    if response.get('type') == 'error':
                        print(f"Error: {response.get('message')}")
                    else:
                        self.display_recipe_list(response)
            else:
                print("Invalid selection")
        except ValueError:
            print("Invalid input")
   
    def handle_filter_by_area(self):
        """Handle filter by area"""
        print("\nFILTER BY AREA")
        areas = ['Italian', 'Indian', 'Mexican', 'Japanese', 'Moroccan', 'British', 'American', 'Thai']
       
        for i, area in enumerate(areas, 1):
            print(f"  {i}. {area}")
       
        try:
            choice = int(input("Select area (1-8): "))
            if 1 <= choice <= 8:
                area = areas[choice-1]
               
                request = {
                    'type': 'filter_area',
                    'params': {'area': area}
                }
               
                response = self.send_request(request)
                if response:
                    if response.get('type') == 'error':
                        print(f"Error: {response.get('message')}")
                    else:
                        self.display_recipe_list(response)
            else:
                print("Invalid selection")
        except ValueError:
            print("Invalid input")
   
    def handle_filter_by_ingredient(self):
        print("\nFILTER BY INGREDIENT")
        ingredient = input("Enter ingredient name: ").strip().replace(' ', '_')
       
        if not ingredient:
            print("No ingredient entered")
            return
       
        request = {
            'type': 'filter_ingredient',
            'params': {'ingredient': ingredient}
        }
       
        response = self.send_request(request)
        if response:
            if response.get('type') == 'error':
                print(f"Error: {response.get('message')}")
            else:
                self.display_recipe_list(response)
   
    def handle_random_recipe(self):
        print("\nGETTING RANDOM RECIPE...")
       
        request = {'type': 'random'}
       
        response = self.send_request(request)
        if response:
            if response.get('type') == 'error':
                print(f"Error: {response.get('message')}")
            elif response.get('type') == 'recipe_details':
                self.display_recipe_details(response.get('data', {}))
   
    def display_recipe_list(self, response):
        """Display list of recipes"""
        print("\n" + "="*80)
        print("RECIPE RESULTS")
        print("="*80)
       
        recipes = response.get('data', [])
       
        if not recipes:
            print("No recipes found")
            return
       
        for recipe in recipes:
            print(f"\n{recipe['id']}. {recipe['name']}")
            print(f"   Meal ID: {recipe['meal_id']}")
            print("-" * 80)
       
        print(f"\nTotal: {len(recipes)} recipes")
        print("="*80)
       
        while True:
            choice = input("\nEnter recipe number for details (or 'back' to return): ").strip().lower()
           
            if choice == 'back':
                break
           
            try:
                recipe_id = int(choice)
                if 0 <= recipe_id < len(recipes):
                    meal_id = recipes[recipe_id]['meal_id']
                    self.request_recipe_details(meal_id)
                    break
                else:
                    print(f"Invalid recipe number. Please enter 0-{len(recipes)-1}")
            except ValueError:
                print("Please enter a valid number or 'back'")
   
    def request_recipe_details(self, meal_id):
        """Request full recipe details"""
        request = {
            'type': 'recipe_details',
            'params': {'meal_id': meal_id}
        }
       
        response = self.send_request(request)
       
        if response and response.get('type') == 'recipe_details':
            self.display_recipe_details(response.get('data', {}))
        elif response and response.get('type') == 'error':
            print(f"Error: {response.get('message')}")
   
    def display_recipe_details(self, data):
        """Display full recipe details"""
        print("\n" + "="*80)
        print("RECIPE DETAILS")
        print("="*80)
        print(f"Name: {data.get('name', 'N/A')}")
        print(f"Category: {data.get('category', 'N/A')}")
        print(f"Area: {data.get('area', 'N/A')}")
        print(f"Tags: {data.get('tags', 'N/A')}")
       
        print(f"\nIngredients:")
        for ingredient in data.get('ingredients', []):
            print(f"  - {ingredient}")
       
        print(f"\nInstructions:")
        print(f"{data.get('instructions', 'N/A')}")
       
        print(f"\nYouTube: {data.get('youtube', 'N/A')}")
        print(f"Source: {data.get('source', 'N/A')}")
        print("="*80)
   
    def handle_list_categories(self):
        """Handle list categories request"""
        request = {'type': 'list_categories'}
       
        response = self.send_request(request)
        if response:
            self.display_reference_list(response, "CATEGORIES")
   
    def handle_list_areas(self):
        """Handle list areas request"""
        request = {'type': 'list_areas'}
       
        response = self.send_request(request)
        if response:
            self.display_reference_list(response, "AREAS")
   
    def handle_list_ingredients(self):
        """Handle list ingredients request"""
        request = {'type': 'list_ingredients'}
       
        response = self.send_request(request)
        if response:
            self.display_reference_list(response, "INGREDIENTS")
   
    def display_reference_list(self, response, title):
        """Display reference list"""
        print("\n" + "="*80)
        print(title)
        print("="*80)
       
        items = response.get('data', [])
       
        if not items:
            print("No items found")
            return
       
        for i, item in enumerate(items, 1):
            name = item.get('name', 'Unknown')
            desc = item.get('description', '')
            if desc:
                print(f"{i}. {name} - {desc}")
            else:
                print(f"{i}. {name}")
       
        print(f"\nTotal: {len(items)} items")
        print("="*80)
   
    def run(self):
        print("Starting Recipe Client...")
       
        if not self.connect():
            return
           
        try:
            while True:
                choice = self.display_main_menu()
               
                if choice == '1':
                    while True:
                        recipes_choice = self.display_recipes_menu()
                        if recipes_choice == '6':
                            break
               
                        elif recipes_choice == '1':
                            self.handle_search_by_name()
                        elif recipes_choice == '2':
                            self.handle_filter_by_category()
                        elif recipes_choice == '3':
                            self.handle_filter_by_area()
                        elif recipes_choice == '4':
                            self.handle_filter_by_ingredient()
                        elif recipes_choice == '5':
                            self.handle_random_recipe()
                        else:
                            print("Invalid option. Please select 1-6.")
                       
                elif choice == '2':
                    while True:
                        ref_choice = self.display_reference_menu()
                        if ref_choice == '4':
                            break
                        elif ref_choice == '1':
                            self.handle_list_categories()
                        elif ref_choice == '2':
                            self.handle_list_areas()
                        elif ref_choice == '3':
                            self.handle_list_ingredients()
                        else:
                            print("Invalid option. Please select 1-4.")
                           
                elif choice == '3':
                    print("\nGoodbye!")
                    break
                else:
                    print("Invalid option. Please select 1-3.")
                   
        except KeyboardInterrupt:
            print("\nClient shutdown requested")
        finally:
            if self.socket:
                try:
                    self.socket.close()
                    print("Connection closed")
                except:
                    pass
 
def main():
    import argparse
   
    parser = argparse.ArgumentParser(description='Recipe Discovery Client')
    parser.add_argument('--host', default='localhost', help='Server hostname')
    parser.add_argument('--port', type=int, default=12345, help='Server port')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL/TLS encryption')
   
    args = parser.parse_args()
   
    client = RecipeClient(
        host=args.host,
        port=args.port,
        use_ssl=not args.no_ssl
    )
    client.run()
 
if __name__ == "__main__":
    main()
