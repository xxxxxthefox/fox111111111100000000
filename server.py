from flask import Flask, jsonify
from flask_cors import CORS
import hashlib
import requests
import random
from urllib.parse import quote
import os
import time

app = Flask(__name__)
CORS(app)

# ---------------- PROXY CONFIG -----------------
PROXIES_LIST = [
    "ndpjmktu:1c10epyq976i@142.111.48.253:7030",
    "ndpjmktu:1c10epyq976i@31.59.20.176:6754",
    "ndpjmktu:1c10epyq976i@23.95.150.145:6114",
    "ndpjmktu:1c10epyq976i@198.23.239.134:6540",
    "ndpjmktu:1c10epyq976i@107.172.163.27:6543",
    "ndpjmktu:1c10epyq976i@198.105.121.200:6462",
    "ndpjmktu:1c10epyq976i@64.137.96.74:6641",
    "ndpjmktu:1c10epyq976i@84.247.60.125:6095",
    "ndpjmktu:1c10epyq976i@216.10.27.159:6837",
    "ndpjmktu:1c10epyq976i@142.111.67.146:5611",
]

TEST_URL = "https://httpbin.org/ip"

def check_proxy(proxy):
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    try:
        r = requests.get(TEST_URL, proxies=proxies, timeout=10)
        if r.status_code == 200:
            return True, r.json()['origin']
    except:
        pass
    return False, None

def get_working_proxies():
    working = []
    for proxy in PROXIES_LIST:
        status, ip = check_proxy(proxy)
        if status:
            working.append(proxy)
    return working

# ---------------- YOLLA CONFIG -----------------
TARGET_URL = "https://api.yollacalls.com/register"

ORDER = [
    'country',
    'device[ad_id]',
    'device[android_id]',
    'device[app_version_code]',
    'device[device_id]',
    'device[emulator]',
    'device[hardware]',
    'device[language]',
    'device[model]',
    'device[platform]',
    'device[product]',
    'device[push_token]',
    'device[rooted]',
    'device[system_version]',
    'device[timezone]',
    'key',
    'language',
    'phone',
    'verify_by'
]

HEADERS_TEMPLATE = {
    'User-Agent': "com.yollacalls/4.71 (Redmi Note 8 Pro; Android 11; ar_EG)",
    'Connection': "Keep-Alive",
    'Accept': "application/json",
    'Accept-Encoding': "gzip",
    'Accept-Charset': "UTF-8",
    'Accept-Language': "ar",
}

def detect_country(phone):
    if phone.startswith("+20"):
        return "EG"
    if phone.startswith("+966"):
        return "SA"
    if phone.startswith("+971"):
        return "AE"
    if phone.startswith("+965"):
        return "KW"
    if phone.startswith("+974"):
        return "QA"
    if phone.startswith("+973"):
        return "BH"
    if phone.startswith("+968"):
        return "OM"
    return "EG"

def generate_signature(payload):
    parts = []
    for key in ORDER:
        value = payload.get(key, "")
        parts.append(f"{quote(key, safe='')}={quote(str(value), safe='')}")
    raw = "&".join(parts)
    return hashlib.md5(raw.encode()).hexdigest().upper()

def random_hex(n):
    return ''.join(random.choices('0123456789abcdef', k=n))

def send_yolla(phone):
    # فحص البروكسيات قبل كل استخدام
    working_proxies = get_working_proxies()
    if not working_proxies:
        return {"error": "لا توجد بروكسيات شغالة"}

    country = detect_country(phone)

    payload = {
        'country': country,
        'device[hardware]': "mt6785",
        'device[app_version_code]': "5058",
        'device[model]': "Redmi Note 8 Pro",
        'device[timezone]': "GMT+3",
        'language': "ar",
        'device[language]': "ar",
        'device[ad_id]': f"7dcd0b0f-3f97-43ab-9ba9-d77042{random_hex(6)}",
        'device[rooted]': "false",
        'device[product]': "begonia",
        'device[android_id]': f"b6410ded6f{random_hex(6)}",
        'verify_by': "callback",
        'device[platform]': "android",
        'device[device_id]': f"ea5993fb3414f9acca6865494aee64f528{random_hex(6)}",
        'device[push_token]': "e6_GD6n7QTKluGzRJLAczv:APA91bFfT7qdKKe_1Cr6gtTVEy55T-IoTSUB1VFQsglGhlDjbEvsHXjvYgW9103jVJnv7rAL2NpakCgc8Rv1tZ4E1VFTix8a5yRYAqlwmqb9oiUF2K_Gz4s",
        'device[system_version]': "11",
        'device[emulator]': "false",
        'key': "X0oMqlskLqp0",
        'phone': phone
    }

    payload['sign'] = generate_signature(payload)
    headers = HEADERS_TEMPLATE.copy()
    headers['Device-id'] = payload['device[device_id]']

    # اختيار بروكسي عشوائي من البروكسيات الشغالة
    proxy = random.choice(working_proxies)
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}

    try:
        r = requests.post(TARGET_URL, data=payload, headers=headers, timeout=15, proxies=proxies)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ---------------- API ROUTE -----------------
@app.route("/<country_code>/<phone_number>", methods=["GET"])
def api(country_code, phone_number):
    phone = f"+{country_code}{phone_number}"
    result = send_yolla(phone)
    return jsonify({
        "phone": phone,
        "country": detect_country(phone),
        "response": result
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
