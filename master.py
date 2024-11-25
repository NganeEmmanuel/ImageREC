from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Worker node addresses (can be expanded dynamically in a real setup)
WORKER_NODES = ["http://localhost:5001", "http://localhost:5002"]

@app.route('/process', methods=['POST'])
def process_request():
    data = request.json
    print(f"Received data: {data}")  # Debugging line
    image_data = data.get("image", None)
    if not image_data:
        return jsonify({"error": "No image data provided"}), 400

    # Simulate task splitting (for simplicity, send the same data to all workers)
    responses = []
    for worker in WORKER_NODES:
        print(f"Sending data to worker: {worker}")  # Debugging line
        try:
            response = requests.post(f"{worker}/process", json={"image_chunk": image_data}, timeout=5)
            responses.append(response.json())
        except requests.exceptions.RequestException as e:
            responses.append({"error": f"Worker {worker} not reachable", "details": str(e)})

    aggregated_response = {"worker_responses": responses}
    print(f"Aggregated response: {aggregated_response}")  # Debugging line
    return jsonify(aggregated_response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
