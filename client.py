import requests

def send_image():
    url = "http://localhost:5000/process"  # Master node URL

    # Read image file and send its content (for testing, using a sample image)
    try:
        with open("repair1.jpg", "rb") as image_file:
            image_data = image_file.read()

        # Send the image data as a POST request to the master node
        response = requests.post(url, json={"image": image_data.hex()})  # Using .hex() to convert binary data to a string
        print(f"Response from master node: {response.json()}")

    except FileNotFoundError:
        print("Error: Image file not found.")
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with master node: {e}")

if __name__ == "__main__":
    send_image()
