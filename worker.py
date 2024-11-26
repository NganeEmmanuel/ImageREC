import grpc
from concurrent import futures
import threading
import time
import image_processing_pb2
import image_processing_pb2_grpc


class WorkerServiceServicer(image_processing_pb2_grpc.WorkerServiceServicer):
    def __init__(self, worker_id):
        self.worker_id = worker_id

    def ProcessChunk(self, request, context):
        # Simulate image processing logic
        chunk_data = request.chunk_data
        print(f"{self.worker_id} - Processing chunk of size: {len(chunk_data)} bytes")

        # Return a response with the processed chunk data and worker ID
        return image_processing_pb2.ChunkResponse(
            result=f"Processed chunk of size {len(chunk_data)} bytes",
            worker_id=self.worker_id
        )


def serve_worker(port, worker_id):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_processing_pb2_grpc.add_WorkerServiceServicer_to_server(WorkerServiceServicer(worker_id), server)
    server.add_insecure_port(f'[::]:{port}')
    print(f"{worker_id} - Worker server started on port {port}")
    server.start()
    try:
        while True:
            time.sleep(86400)  # Keep the server running
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    # Define ports and worker IDs
    worker_details = [
        {"port": 50051, "worker_id": "Worker-50051"},
        {"port": 50052, "worker_id": "Worker-50052"}
    ]

    # Start each worker in a separate thread
    threads = []
    for worker in worker_details:
        t = threading.Thread(target=serve_worker, args=(worker["port"], worker["worker_id"]))
        t.start()
        threads.append(t)

    # Keep the main thread alive to monitor the workers
    for t in threads:
        t.join()
