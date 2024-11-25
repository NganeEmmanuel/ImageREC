from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/process', methods=['POST'])
def process_chunk():
    data = request.json
    image_chunk = data.get("image_chunk", None)
    if not image_chunk:
        return jsonify({"error": "No image chunk provided"}), 400

    # Simulate processing
    result = f"Processed chunk: {image_chunk[:10]}..."  # Mock processing
    return jsonify({"result": result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)  # Change port for each worker
