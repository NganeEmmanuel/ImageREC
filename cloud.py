from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_request():
    data = request.json  # Receive JSON payload
    message = data.get('message', 'No message received')
    response = f"Server processed: {message}"
    return jsonify({'response': response})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
