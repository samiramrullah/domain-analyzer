from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- Simple redirect resolver ---
def get_final_url(domain: str):
    try:
        if not domain.startswith("http"):
            domain = "http://" + domain
        resp = requests.get(domain, timeout=10, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        return resp.url
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
