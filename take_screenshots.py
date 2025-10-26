import os
import http.server
import socketserver
import threading
import time
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException

# --- Configuration ---
HOST = "localhost"
PORT = 8000
BASE_URL = f"http://{HOST}:{PORT}"
HTML_DIRECTORY = "html"  # Directory to serve
SCREENSHOTS_FOLDER = "screenshots" # Output folder for images
SELECTORS = {
    "selector1": "practice-select",
    "selector2": "fips-select",
}

def start_server(directory):
    """Starts a simple HTTP server in a daemon thread."""
    
    # Custom handler to serve from the specified directory
    class DirectoryHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        httpd = socketserver.TCPServer((HOST, PORT), DirectoryHandler)
        print(f"Serving directory '{directory}' at {BASE_URL}")
        
        # Start the server in a thread that will exit when the main script exits
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        
        return httpd, server_thread
    except OSError as e:
        print(f"Error starting server on port {PORT}: {e}")
        print("Please check if the port is already in use.")
        return None, None

def take_screenshots():
    """Launches browser, iterates selectors, and takes screenshots."""
    
    # Ensure the output directory exists
    os.makedirs(SCREENSHOTS_FOLDER, exist_ok=True)

    # --- Setup Headless Options ---
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox") # Often needed for headless in containers
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    
    # Use a 'with' statement for clean setup and teardown of the browser
    # This automatically calls driver.quit()
    try:
        # Pass the options to the Chrome driver
        with webdriver.Chrome(options=options) as driver:
            print("WebDriver launched in headless mode.")
            driver.get(BASE_URL)
                        
            # Give the page a moment to load, especially for local files
            time.sleep(0.5) 

            # Find the select elements
            try:
                select_el1 = Select(driver.find_element(by="id", value=SELECTORS["selector1"]))
                select_el2 = Select(driver.find_element(by="id", value=SELECTORS["selector2"]))
            except NoSuchElementException as e:
                print(f"Error: Could not find one of the select elements: {e.Name}")
                print(f"Please check your HTML and selector IDs.")
                return

            # Get all options from the dropdowns
            options1 = [opt.get_attribute("value") for opt in select_el1.options]
            options2 = [opt.get_attribute("value") for opt in select_el2.options]

            print(f"Found {len(options1)} options for #_practice-select.")
            print(f"Found {len(options2)} options for #fips-select.")
            print(f"Total combinations to capture: {len(options1) * len(options2)}")

            # Loop through every possible combination
            count = 0
            for val1 in options1:
                # Select the option
                select_el1.select_by_value(val1)
                
                for val2 in options2:
                    # Select the second option
                    select_el2.select_by_value(val2)
                    
                    # Give a tiny pause for any potential JS rendering
                    time.sleep(0.05) 
                    
                    # Create a clean filename
                    # We replace potentially problematic characters just in case
                    filename1 = val1.replace("/", "-").replace("\\", "-")
                    filename2 = val2.replace("/", "-").replace("\\", "-")
                    
                    filepath = os.path.join(SCREENSHOTS_FOLDER, f"{filename1}_{filename2}.png")
                    
                    try:
                        # Use Chrome DevTools Protocol (CDP) to capture full page
                        result = driver.execute_cdp_cmd(
                            "Page.captureScreenshot",
                            {
                                "format": "png",
                                "captureBeyondViewport": True
                            }
                        )
                        
                        # The result is base64 encoded, so we decode it
                        png_data = base64.b64decode(result['data'])
                        
                        # Write the decoded data to the file
                        with open(filepath, "wb") as f:
                            f.write(png_data)
                        
                        count += 1
                        print(f"({count}) Saved: {filepath}")
                    
                    except Exception as e:
                        print(f"Error saving full-page screenshot {filepath}: {e}")
                        print("This feature requires Selenium 4+ and a compatible Chrome/ChromeDriver.")

            print(f"\nDone! Saved {count} screenshots to '{SCREENSHOTS_FOLDER}'.")

    except Exception as e:
        print(f"An error occurred during browser automation: {e}")
        print("Please ensure you have 'chromedriver' installed and in your system's PATH.")

def main():
    # Start the web server
    httpd, server_thread = start_server(HTML_DIRECTORY)
    
    if httpd is None:
        return # Exit if server couldn't start
        
    # Give the server a moment to start up
    time.sleep(1) 
    
    # Run the screenshot process
    take_screenshots()
    
    # Tell the server to stop
    print("Shutting down web server...")
    httpd.shutdown()
    # Wait for the server thread to fully stop
    server_thread.join()
    
    # The script will now exit, and the daemon server thread will be terminated.
    print("Script finished.")

if __name__ == "__main__":
    main()
