import socket
import json
import ssl
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
 
class RecipeClientGUI:
    
   
    def __init__(self, root):
        self.root = root
        self.root.title("Recipe Discovery System")
        self.root.geometry("900x700")
       
        self.host = 'localhost'
        self.port = 12345
        self.use_ssl = True
        self.socket = None
        self.username = ""
        self.ssl_context = None
        self.connected = False
       
        self.current_recipes = []
       
        self.setup_gui()
       
    def setup_gui(self):
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
       
        self.connection_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.connection_frame, text='Connection')
        self.setup_connection_tab()
       
        self.recipes_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.recipes_frame, text='Browse Recipes')
        self.setup_recipes_tab()
       
        self.reference_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reference_frame, text='Reference Lists')
        self.setup_reference_tab()
       
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.details_frame, text='Recipe Details')
        self.setup_details_tab()
       
        self.status_bar = tk.Label(self.root, text="Not connected", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
       
    def setup_connection_tab(self):
        frame = ttk.LabelFrame(self.connection_frame, text="Server Connection", padding=20)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
       
        ttk.Label(frame, text="Username:").grid(row=0, column=0, sticky='w', pady=5)
        self.username_entry = ttk.Entry(frame, width=30)
        self.username_entry.grid(row=0, column=1, pady=5, padx=5)
        self.username_entry.insert(0, "user1")
       
        ttk.Label(frame, text="Host:").grid(row=1, column=0, sticky='w', pady=5)
        self.host_entry = ttk.Entry(frame, width=30)
        self.host_entry.grid(row=1, column=1, pady=5, padx=5)
        self.host_entry.insert(0, "localhost")
       
        ttk.Label(frame, text="Port:").grid(row=2, column=0, sticky='w', pady=5)
        self.port_entry = ttk.Entry(frame, width=30)
        self.port_entry.grid(row=2, column=1, pady=5, padx=5)
        self.port_entry.insert(0, "12345")
       
        self.ssl_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Use SSL/TLS", variable=self.ssl_var).grid(row=3, column=0, columnspan=2, pady=5)
       
    
        self.connect_btn = ttk.Button(frame, text="Connect", command=self.connect_to_server)
        self.connect_btn.grid(row=4, column=0, columnspan=2, pady=10)
       
        self.disconnect_btn = ttk.Button(frame, text="Disconnect", command=self.disconnect_from_server, state='disabled')
        self.disconnect_btn.grid(row=5, column=0, columnspan=2, pady=5)
       
        self.connection_info = scrolledtext.ScrolledText(frame, height=15, width=60, state='disabled')
        self.connection_info.grid(row=6, column=0, columnspan=2, pady=10)
       
    def setup_recipes_tab(self):
       
        left_frame = ttk.Frame(self.recipes_frame)
        left_frame.pack(side='left', fill='both', padx=10, pady=10)
       
        search_frame = ttk.LabelFrame(left_frame, text="Search by Name", padding=10)
        search_frame.pack(fill='x', pady=5)
       
        self.search_entry = ttk.Entry(search_frame, width=25)
        self.search_entry.pack(pady=5)
        ttk.Button(search_frame, text="Search", command=self.search_by_name).pack(pady=5)
       
        category_frame = ttk.LabelFrame(left_frame, text="Filter by Category", padding=10)
        category_frame.pack(fill='x', pady=5)
       
        self.category_var = tk.StringVar()
        categories = ['Beef', 'Chicken', 'Seafood', 'Vegetarian', 'Dessert', 'Pasta', 'Breakfast']
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, values=categories, state='readonly', width=22)
        self.category_combo.pack(pady=5)
        self.category_combo.current(0)
        ttk.Button(category_frame, text="Filter", command=self.filter_by_category).pack(pady=5)
       
        area_frame = ttk.LabelFrame(left_frame, text="Filter by Area", padding=10)
        area_frame.pack(fill='x', pady=5)
       
        self.area_var = tk.StringVar()
        areas = ['Italian', 'Indian', 'Mexican', 'Japanese', 'Moroccan', 'British', 'American', 'Thai']
        self.area_combo = ttk.Combobox(area_frame, textvariable=self.area_var, values=areas, state='readonly', width=22)
        self.area_combo.pack(pady=5)
        self.area_combo.current(0)
        ttk.Button(area_frame, text="Filter", command=self.filter_by_area).pack(pady=5)
       
        ingredient_frame = ttk.LabelFrame(left_frame, text="Filter by Ingredient", padding=10)
        ingredient_frame.pack(fill='x', pady=5)
       
        self.ingredient_entry = ttk.Entry(ingredient_frame, width=25)
        self.ingredient_entry.pack(pady=5)
        ttk.Button(ingredient_frame, text="Filter", command=self.filter_by_ingredient).pack(pady=5)
       
        random_frame = ttk.LabelFrame(left_frame, text="Random Recipe", padding=10)
        random_frame.pack(fill='x', pady=5)
        ttk.Button(random_frame, text="Get Random Recipe", command=self.get_random_recipe).pack(pady=5)
       
        right_frame = ttk.Frame(self.recipes_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)
       
        ttk.Label(right_frame, text="Recipe Results", font=('Arial', 12, 'bold')).pack(pady=5)
       
        list_frame = ttk.Frame(right_frame)
        list_frame.pack(fill='both', expand=True)
       
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
       
        self.recipe_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=('Arial', 10))
        self.recipe_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.recipe_listbox.yview)
       
        ttk.Button(right_frame, text="View Recipe Details", command=self.view_recipe_details).pack(pady=10)
       
    def setup_reference_tab(self):
        btn_frame = ttk.Frame(self.reference_frame)
        btn_frame.pack(side='top', fill='x', padx=10, pady=10)
       
        ttk.Button(btn_frame, text="List Categories", command=self.list_categories).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="List Areas", command=self.list_areas).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="List Ingredients", command=self.list_ingredients).pack(side='left', padx=5)
       
        results_frame = ttk.Frame(self.reference_frame)
        results_frame.pack(fill='both', expand=True, padx=10, pady=10)
       
        ttk.Label(results_frame, text="Reference List Results", font=('Arial', 12, 'bold')).pack(pady=5)
       
        self.reference_text = scrolledtext.ScrolledText(results_frame, height=30, width=80, font=('Arial', 10))
        self.reference_text.pack(fill='both', expand=True)
       
    def setup_details_tab(self):
        self.details_text = scrolledtext.ScrolledText(self.details_frame, height=35, width=90, font=('Arial', 10), wrap=tk.WORD)
        self.details_text.pack(fill='both', expand=True, padx=10, pady=10)
       
    def setup_ssl(self):
        try:
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
            self.log_connection("[SSL] SSL/TLS enabled")
            return True
        except Exception as e:
            self.log_connection(f"[SSL] Failed to setup SSL: {e}")
            return False
           
    def connect_to_server(self):
        if self.connected:
            messagebox.showwarning("Already Connected", "Already connected to server")
            return
           
        self.username = self.username_entry.get().strip()
        self.host = self.host_entry.get().strip()
       
        try:
            self.port = int(self.port_entry.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Port", "Port must be a number")
            return
           
        if not self.username:
            messagebox.showerror("Username Required", "Please enter a username")
            return
           
        self.use_ssl = self.ssl_var.get()
       
        thread = threading.Thread(target=self._connect_thread, daemon=True)
        thread.start()
       
    def _connect_thread(self):
        try:
            self.log_connection(f"Connecting to {self.host}:{self.port}...")
           
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
           
            if self.use_ssl:
                if self.setup_ssl():
                    try:
                        self.socket = self.ssl_context.wrap_socket(raw_socket, server_hostname=self.host)
                        self.log_connection("[SSL] Secure connection established")
                    except ssl.SSLError as e:
                        self.log_connection(f"[SSL] SSL handshake failed: {e}")
                        self.log_connection("[SSL] Falling back to non-SSL")
                        self.socket = raw_socket
                        self.use_ssl = False
                else:
                    self.socket = raw_socket
            else:
                self.socket = raw_socket
               
            self.socket.connect((self.host, self.port))
            self.socket.send(self.username.encode('utf-8'))
           
            self.connected = True
            ssl_status = "(SSL/TLS)" if self.use_ssl else "(No SSL)"
            self.log_connection(f"Connected as {self.username} {ssl_status}")
           
            self.root.after(0, self._update_connection_ui, True)
           
        except ConnectionRefusedError:
            self.log_connection("Connection refused. Is the server running?")
            self.root.after(0, messagebox.showerror, "Connection Failed", "Connection refused")
        except Exception as e:
            self.log_connection(f"Connection failed: {e}")
            self.root.after(0, messagebox.showerror, "Connection Failed", str(e))
           
    def disconnect_from_server(self):
        if self.socket:
            try:
                self.socket.close()
                self.log_connection("Disconnected from server")
            except:
                pass
        self.connected = False
        self.socket = None
        self._update_connection_ui(False)
       
    def _update_connection_ui(self, connected):
        if connected:
            self.connect_btn.config(state='disabled')
            self.disconnect_btn.config(state='normal')
            self.status_bar.config(text=f"Connected to {self.host}:{self.port} as {self.username}")
        else:
            self.connect_btn.config(state='normal')
            self.disconnect_btn.config(state='disabled')
            self.status_bar.config(text="Not connected")
           
    def log_connection(self, message):
        self.connection_info.config(state='normal')
        self.connection_info.insert(tk.END, message + "\n")
        self.connection_info.see(tk.END)
        self.connection_info.config(state='disabled')
       
    def send_request(self, request_data):
        if not self.connected or not self.socket:
            messagebox.showerror("Not Connected", "Please connect to server first")
            return None
           
        try:
            request_json = json.dumps(request_data)
            self.socket.send(request_json.encode('utf-8'))
           
            response_data = self.socket.recv(8192)
            response = json.loads(response_data.decode('utf-8'))
            return response
           
        except Exception as e:
            messagebox.showerror("Request Failed", f"Request failed: {e}")
            self.disconnect_from_server()
            return None
           
    def search_by_name(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showwarning("No Keyword", "Please enter a search keyword")
            return
           
        request = {
            'type': 'search_name',
            'params': {'keyword': keyword}
        }
       
        response = self.send_request(request)
        if response:
            self.display_recipe_list(response)
           
    def filter_by_category(self):
        category = self.category_var.get()
       
        request = {
            'type': 'filter_category',
            'params': {'category': category}
        }
       
        response = self.send_request(request)
        if response:
            self.display_recipe_list(response)
           
    def filter_by_area(self):
        area = self.area_var.get()
       
        request = {
            'type': 'filter_area',
            'params': {'area': area}
        }
       
        response = self.send_request(request)
        if response:
            self.display_recipe_list(response)
           
    def filter_by_ingredient(self):
        ingredient = self.ingredient_entry.get().strip().replace(' ', '_')
        if not ingredient:
            messagebox.showwarning("No Ingredient", "Please enter an ingredient")
            return
           
        request = {
            'type': 'filter_ingredient',
            'params': {'ingredient': ingredient}
        }
       
        response = self.send_request(request)
        if response:
            self.display_recipe_list(response)
           
    def get_random_recipe(self):
        request = {'type': 'random'}
       
        response = self.send_request(request)
        if response:
            if response.get('type') == 'recipe_details':
                self.display_recipe_details(response.get('data', {}))
                self.notebook.select(self.details_frame)
            elif response.get('type') == 'error':
                messagebox.showerror("Error", response.get('message'))
               
    def display_recipe_list(self, response):
        if response.get('type') == 'error':
            messagebox.showerror("Error", response.get('message'))
            return
           
        recipes = response.get('data', [])
        self.current_recipes = recipes
       
        self.recipe_listbox.delete(0, tk.END)
       
        if not recipes:
            self.recipe_listbox.insert(tk.END, "No recipes found")
            return
           
        for recipe in recipes:
            self.recipe_listbox.insert(tk.END, f"{recipe['id']}. {recipe['name']}")
           
        messagebox.showinfo("Results", f"Found {len(recipes)} recipes")
       
    def view_recipe_details(self):
        """View details of selected recipe"""
        selection = self.recipe_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a recipe from the list")
            return
           
        index = selection[0]
        if index >= len(self.current_recipes):
            return
           
        recipe = self.current_recipes[index]
        meal_id = recipe['meal_id']
       
        request = {
            'type': 'recipe_details',
            'params': {'meal_id': meal_id}
        }
       
        response = self.send_request(request)
        if response and response.get('type') == 'recipe_details':
            self.display_recipe_details(response.get('data', {}))
            self.notebook.select(self.details_frame)
        elif response and response.get('type') == 'error':
            messagebox.showerror("Error", response.get('message'))
           
    def display_recipe_details(self, data):
        """Display full recipe details"""
        self.details_text.delete('1.0', tk.END)
       
        details = f"""
{'='*80}
RECIPE DETAILS
{'='*80}
 
Name: {data.get('name', 'N/A')}
Category: {data.get('category', 'N/A')}
Area: {data.get('area', 'N/A')}
Tags: {data.get('tags', 'N/A')}
 
INGREDIENTS:
"""
        for ingredient in data.get('ingredients', []):
            details += f"  • {ingredient}\n"
           
        details += f"""
INSTRUCTIONS:
{data.get('instructions', 'N/A')}
 
LINKS:
YouTube: {data.get('youtube', 'N/A')}
Source: {data.get('source', 'N/A')}
 
{'='*80}
"""
       
        self.details_text.insert('1.0', details)
       
    def list_categories(self):
        request = {'type': 'list_categories'}
        response = self.send_request(request)
        if response:
            self.display_reference_list(response, "CATEGORIES")
           
    def list_areas(self):
        """List all areas"""
        request = {'type': 'list_areas'}
        response = self.send_request(request)
        if response:
            self.display_reference_list(response, "AREAS")
           
    def list_ingredients(self):
        request = {'type': 'list_ingredients'}
        response = self.send_request(request)
        if response:
            self.display_reference_list(response, "INGREDIENTS")
           
    def display_reference_list(self, response, title):
        self.reference_text.delete('1.0', tk.END)
       
        items = response.get('data', [])
       
        output = f"""
{'='*80}
{title}
{'='*80}
 
"""       
        if not items:
            output += "No items found\n"
        else:
            for i, item in enumerate(items, 1):
                name = item.get('name', 'Unknown')
                desc = item.get('description', '')
                if desc:
                    output += f"{i}. {name} - {desc}\n"
                else:
                    output += f"{i}. {name}\n"
                   
        output += f"\nTotal: {len(items)} items\n"
        output += "="*80 + "\n"
       
        self.reference_text.insert('1.0', output)
        self.notebook.select(self.reference_frame)
 
def main():
    
    root = tk.Tk()
    app = RecipeClientGUI(root)
    root.mainloop()
 
if __name__ == "__main__":
    main()