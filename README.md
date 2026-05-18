# ITNE352-GROUP-A6
THIS IS FOR ITNE352 PYTHON PROJETC SECTION 1 AND THE INTRUCTOR IS DR MOHAMMED ALMIER 
Name isa hamad nesuf id 202300103
ABDULAZIZ MOHAMMED ID :202307787
# Recipe Discovery System – Client/Server Project

## Project Description

A multithreaded client–server application built in Python that allows clients to discover and browse food recipes using the [TheMealDB API](https://www.themealdb.com). The server manages multiple simultaneous client connections, maintains a reference cache loaded at startup, and fetches recipe data on demand. The client provides an interactive menu-driven interface to search and filter recipes by name, category, area, or ingredient.

---

## Semester

**S2 2025–2026** | ITNE352: Network Programming

---

## Group

| Field         | Details              |
|---------------|----------------------|
| Group Name    | Group A6     |
| Course Code   | ITNE352              |
| Section       | [1]       |
| Student 1     | [ISA HAMAD NESUF] – [202300103]        |
| Student 2     | [ABDULAZIZ MOHAMMED ] – [202307787]        |

---

## Table of Contents

1. [Project Description](#project-description)
2. [Semester](#semester)
3. [Group](#group)
4. [Requirements](#requirements)
5. [How To Run](#how-to-run)
6. [The Scripts](#the-scripts)
7. [Additional Concept](#additional-concept)
8. [Acknowledgments](#acknowledgments)
9. [Conclusion](#conclusion)
10. [Resources](#resources)

---

## Requirements

### Prerequisites

- Python 3.8 or higher
- Internet connection (to reach TheMealDB API)

### Dependencies

Install required libraries using pip:

```bash
pip install requests
```

No other third-party libraries are required. The project uses Python's built-in `socket`, `threading`, `json`, and `os` modules.

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ITNE352-Project-GroupX.git
   cd ITNE352-Project-GroupX
   ```

2. Ensure Python 3.8+ is installed:
   ```bash
   python --version
   ```

3. Install dependencies:
   ```bash
   pip install requests
   ```

---

## How To Run

### 1. Start the Server

```bash
python server.py
```

- The server will load the reference cache (categories, areas, ingredients) from TheMealDB on startup.
- It will write the cache to `reference_<group_ID>.json`.
- It will then start listening for incoming client connections on `localhost` port `12345`.

### 2. Start the Client

Open a new terminal window and run:

```bash
python client.py
```

- You will be prompted to enter your username.
- The main menu will appear with the following options:
  1. Browse Recipes
  2. Reference Lists
  3. Quit

### 3. Navigating the Menus

**Main Menu → Browse Recipes:**
```
1. Search by name
2. Filter by category
3. Filter by area
4. Filter by ingredient
5. Random recipe
6. Back to main menu
```

**Main Menu → Reference Lists:**
```
1. List all categories
2. List all areas
3. List all ingredients
4. Back to main menu
```

### 4. Stopping the Server

Press `Ctrl+C` in the server terminal to shut it down.

---

## The Scripts

### `server.py`

The server script is the core of the system. Its main responsibilities are:

- **Startup cache:** On launch, it fetches the three reference lists (categories, areas, ingredients) from TheMealDB and stores them in memory.
- **Multi-client support:** Uses Python's `threading` module to handle at least 3 simultaneous client connections.
- **Request handling:** Routes each client request to either the cache or a live TheMealDB API call depending on the request type.
- **File logging:** Saves every recipe response to a JSON file named `<client_name>_<option>_<group_ID>.json`.

**Key functions:**

```python
def load_reference_cache():
    """Fetches categories, areas, and ingredients from TheMealDB at startup."""

def handle_client(conn, addr):
    """Runs in a separate thread for each connected client."""

def fetch_recipes(option, param):
    """Contacts the appropriate TheMealDB endpoint based on the request type."""
```

**Packages used:** `socket`, `threading`, `json`, `requests`, `os`

---

### `client.py`

The client script provides the interactive interface for the user. Its main responsibilities are:

- **Connection:** Establishes a TCP connection with the server and sends the username.
- **Menu navigation:** Displays the main menu, recipes menu, and reference menu.
- **Input validation:** Validates categories, areas, and ingredients against the permitted values before sending a request.
- **Results display:** Presents lists and full recipe details in a clean, readable format.

**Key functions:**

```python
def connect_to_server():
    """Creates a TCP socket and connects to the server."""

def display_main_menu():
    """Displays the main menu and handles user selection."""

def display_recipe_details(recipe):
    """Formats and prints the full details of a selected recipe."""
```

**Packages used:** `socket`, `json`

---

## Additional Concept

### [Insert Your Chosen Concept Here]

> Replace this section with your chosen additional concept from the list below:
> - TLS/SSL Security
> - Object-Oriented Programming
> - Graphical User Interface (GUI)
> - Non-blocking I/O with `selectors`
> - Length-prefixed message framing
> - UDP-based service discovery

**Description:**
Provide a brief explanation of the concept and why you chose it.

**Implementation:**
Describe how it is implemented in your code. Include a relevant code snippet:

```python
# Example snippet
```

---

## Acknowledgments

- [TheMealDB](https://www.themealdb.com) for providing the free recipe API.
- Dr. Mohammed Almeer for the project guidelines and support.
- University of Bahrain, College of IT, Department of Computer Engineering.

---

## Conclusion

This project provided hands-on experience building a real-world client–server application in Python. We applied core networking concepts including TCP sockets, multithreading, and REST API integration. The hybrid data-handling approach — a startup reference cache for static data combined with on-demand API fetching for dynamic recipe queries — proved to be an effective design pattern that balances efficiency and accuracy. Through this project, we strengthened our understanding of network programming, collaborative development using GitHub, and software design principles.
