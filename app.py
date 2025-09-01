from flask import Flask, request, jsonify
from extractor import EnhancedMetaExtractor

app = Flask(__name__)

@app.route("/extract", methods=["GET"])
def extract_meta():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    extractor = EnhancedMetaExtractor()
    result = extractor.fetch_meta_data(url)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9001, debug=False)
