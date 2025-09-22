from flask import Flask, request, jsonify
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# --- Simple redirect resolver ---
def get_final_url(domain: str):
    try:
        if not domain.startswith("http"):
            domain = "http://" + domain

        options = Options()
        options.add_argument("--headless=new")  # true headless for Chrome >=109
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        driver = webdriver.Chrome(options=options)
        driver.get(domain)
        final_url = driver.current_url
        driver.quit()
        return final_url
    except Exception as e:
        return f"Error: {e}"

# --- Flask routes ---
@app.route('/')
def home():
    return "Domain Redirect Checker API is running!"

@app.route("/check", methods=["GET"])
def check_domain_route():
    domain = request.args.get("domain")
    if not domain:
        return jsonify({"error": "Please provide a domain parameter"}), 400
    final_url = get_final_url(domain)
    return jsonify({"domain": domain, "final_url": final_url})

if __name__ == "__main__":
    app.run(debug=True)
