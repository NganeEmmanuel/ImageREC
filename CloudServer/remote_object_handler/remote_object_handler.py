import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import aiohttp


def download_image(url, file_name, save_path, timeout=10, max_retries=3, backoff_factor=0.3):
    """
    Downloads an image from a URL, saves it to a specified path, and returns its content as bytes.

    Args:
        url (str): URL of the image to download.
        file_name (str): Name to assign to the downloaded file (without creating subdirectories).
        save_path (str): Directory to save the downloaded file.
        timeout (int): Timeout for the request in seconds.
        max_retries (int): Maximum number of retry attempts for transient errors.
        backoff_factor (float): Factor to control delay between retries.

    Returns:
        tuple: (bool, bytes or str) where bool indicates success or failure,
               bytes contains the image data if successful, and str provides error details if any.
    """
    session = requests.Session()
    retries = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET"]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))

    try:
        # Ensure the save directory exists
        os.makedirs(save_path, exist_ok=True)

        # Generate the full path to save the file (ensure it's directly at the save_path)
        file_path = os.path.join(save_path, f"{file_name}.jpg")
        print(f"Downloading {url} to {file_path}")

        # Get the response
        response = session.get(url, timeout=timeout)
        response.raise_for_status()

        # Validate Content-Type to ensure it's an image
        content_type = response.headers.get("Content-Type", "").lower()
        if not content_type.startswith("image/"):
            return False, f"URL does not point to a valid image. Content-Type: {content_type}"

        # Save the file at the correct path
        with open(file_path, 'wb') as f:
            f.write(response.content)

        # Return the image content as bytes
        return response.content
    except requests.RequestException as e:
        return False, str(e)  # Return error details
    finally:
        session.close()


async def download_image_async(url, file_name, save_path):
    """
    Asynchronously downloads an image from a URL, saves it to a specified path, and returns its content.

    Args:
        url (str): URL of the image to download.
        file_name (str): Name to assign to the downloaded file (without creating subdirectories).
        save_path (str): Directory to save the downloaded file.

    Results:
    tuple: (bool, bytes or str) where bool indicates success or failure,

    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200 and response.content_type.startswith('image/'):
                content = await response.read()
                os.makedirs(save_path, exist_ok=True)
                file_path = os.path.join(save_path, f"{file_name}.jpg")
                with open(file_path, 'wb') as f:
                    f.write(content)
                return file_path, content
            else:
                raise ValueError("URL does not point to a valid image.")
