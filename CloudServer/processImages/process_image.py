import os
import asyncio
from uuid import uuid4


import image_processing_pb2
from CloudServer.database_manager import database_handler
from CloudServer.remote_object_handler.remote_object_handler import download_image_async

# Define the directory for saving images
IMAGE_STORAGE_DIR = os.path.join(os.getcwd(), "CloudServer/images")


async def handle_image_download(images, request_id):
    """Handles image download for remote images and processes byte data images.

    Args:
        images (list): List of images to download or process.
        request_id (str): Request ID.

    Returns:
        List of tuples containing the image path and byte data or error details.
    """
    tasks = []
    results = []

    for image in images:
        if image.location != "local":
            # Create a task to download the image from the URL
            task = download_image_async(image.image_url, f"{request_id}_{image.image_id}", IMAGE_STORAGE_DIR)
            tasks.append(task)
        else:
            # Process image in byte data directly
            image_path = os.path.join(IMAGE_STORAGE_DIR, f"{request_id}_{image.image_id}.jpg")
            try:
                # Save the byte data to a file
                with open(image_path, 'wb') as file:
                    file.write(image.image_data)
                results.append((image_path, image.image_data))
            except Exception as e:
                results.append((None, str(e)))

    # Gather the results of all download tasks
    download_results = await asyncio.gather(*tasks, return_exceptions=True)
    results.extend(download_results)

    return results


async def handle_request_async(shared_state, request_id, images, model_name, action_type, user_email):
    try:
        # Download images asynchronously
        download_results = await handle_image_download(images, request_id)

        # Prepare the data for the queue
        processed_images = []
        for idx, result in enumerate(download_results):
            if isinstance(result, tuple):
                file_path, content = result
                image_metadata = {
                    "id": images[idx].image_id,
                    "size": len(content),
                    "path": file_path,
                    "image_bytes": content,
                }
                processed_images.append(image_metadata)

        # Add to request state
        async with shared_state.state_lock:
            shared_state.request_state[request_id] = {"status": "queued", "result": None}

        # Add to processing queue
        await shared_state.request_queue.put((request_id, processed_images, model_name, action_type, user_email))
        print(f"Request {request_id} added to the queue.")

    except Exception as e:
        print(f"Error handling request {request_id}: {e}")
        async with shared_state.state_lock:
            shared_state.request_state[request_id] = {"status": "failed", "error": str(e)}


async def process_image(shared_state, request, context):
    request_id = str(uuid4())
    images = request.images

    # Add request to the database immediately
    database_handler.add_request(request_id, request.user.email, request.model_name, request.action_type)

    # Response to client immediately with request_id
    response = image_processing_pb2.ProcessImageResponse(request_id=request_id)

    # Start asynchronous image download and processing
    await asyncio.create_task(handle_request_async(shared_state, request_id, images, request.model_name, request.action_type, request.user.email))

    return response
