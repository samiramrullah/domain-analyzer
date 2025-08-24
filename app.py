#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from flask import Flask, request, jsonify
import re
import requests
from urllib.parse import urlparse
import threading
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- Pre-check filters ---
UNWANTED_TLDS = [".cn", ".ru"]

# --- Keywords for classification ---
FOR_SALE_KEYWORDS = [
    "buy this domain", "domain for sale", "this domain is for sale",
    "acquire this domain", "make an offer", "bid now"
]
ACTIVE_SITE_KEYWORDS = [
    "cart", "checkout", "shop now", "products", "services",
    "marketplace", "about us", "contact", "login"
]

# --- Domain validation ---
def is_valid_domain(domain: str):
    parsed = urlparse(domain if "://" in domain else "http://" + domain)
    domain_name = parsed.netloc or parsed.path
    if not domain_name:
        return False, None
    for tld in UNWANTED_TLDS:
        if domain_name.endswith(tld):
            return False, None
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain_name):
        return False, None
    regex = re.compile(
        r"^(?=.{1,253}$)(?!-)([A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$"
    )
    if not regex.match(domain_name):
        return False, None
    return True, domain_name

# --- RDAP check ---
def check_domain_rdap(domain: str):
    try:
        url = f"https://rdap.org/domain/{domain}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 404:
            return "Available", "Domain available for registration"
        elif resp.status_code == 200:
            return "Registered", "Domain already registered"
        else:
            return "Unknown", f"RDAP returned {resp.status_code}"
    except Exception as e:
        return "Unknown", f"RDAP error: {e}"

# --- Content classifier ---
def classify_content(domain: str):
    try:
        resp = requests.get(
            "http://" + domain,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True  # follow redirects
        )
        content = resp.text.lower()
        final_url = resp.url  # where it actually ended up
        # print(content)
    except Exception as e:
        # Registered but fetch failed => default to Fail
        return "Fail", f"Registered domain, but page fetch failed ({e})"
    # ✅ Check Brandpa redirect rule
    if final_url.startswith("https://brandpa.com/names/"):
        return "Pass", "Pass as it is available for sale on Brandpa"

    # 1. For-sale keywords
    if any(kw in content for kw in FOR_SALE_KEYWORDS):
        return "Pass", "Domain sale language detected"

    # 2. Parse HTML for structure
    soup = BeautifulSoup(content, "html.parser")
    links = soup.find_all("a")
    navs = soup.find_all("nav")

    # 3. Expanded keywords for active sites
    ACTIVE_KEYWORDS = ACTIVE_SITE_KEYWORDS + [
        "categories", "deals", "sign in", "sign up", "register", "my account"
    ]

    if any(kw in content for kw in ACTIVE_KEYWORDS):
        return "Fail", "Active website content detected"

    # 4. Heuristic: many links or nav menus → active site
    if len(links) > 20 or len(navs) > 0:
        return "Fail", f"Active site detected (links={len(links)}, navs={len(navs)})"
    return "Manual Review", "Unclear signals, requires human review"

# --- Main pipeline ---
def analyze_domain(input_domain: str):
    valid, domain = is_valid_domain(input_domain)
    if not valid:
        return {"url": input_domain, "status": "Fail", "reason": "Invalid or unwanted domain"}
    rdap_status, rdap_reason = check_domain_rdap(domain)
    if rdap_status == "Available":
        return {"url": domain, "status": "Pass", "reason": rdap_reason}
    elif rdap_status == "Registered":
        cls_status, cls_reason = classify_content(domain)
        return {"url": domain, "status": cls_status, "reason": cls_reason}
    else:
        return {"url": domain, "status": "Manual Review", "reason": rdap_reason}

# --- Flask routes ---
@app.route('/')
def home():
    return "Domain Checker API is running!"

@app.route("/check", methods=["GET"])
def check_domain_route():
    domain = request.args.get("domain")
    if not domain:
        return jsonify({"error": "Please provide a domain parameter"}), 400
    result = analyze_domain(domain)
    return jsonify(result)

# --- Run Flask server in a thread for Jupyter ---
def run_app():
    app.run(debug=True, use_reloader=False)

thread = threading.Thread(target=run_app)
thread.start()


# In[ ]:




