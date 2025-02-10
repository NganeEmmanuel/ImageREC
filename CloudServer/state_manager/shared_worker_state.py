from threading import Lock
from queue import Queue


class SharedWorkerState:
    def __init__(self):
        self.worker_registry = {}  # Maps worker_id to worker information (including VM data)
        self.available_workers = Queue()
        self.worker_lock = Lock()

        # Constants
        self.BASE_WORKER_PORT = 50052
        self.MAX_WORKERS = 10
        self.MIN_WORKERS = 2
        self.WORKER_IDLE_TIMEOUT = 360

        # New VM registry (tracks the VM ID and status)
        self.vm_registry = {}  # Maps VM ID to VM status
        self.worker_host_registry = {} # Store the worker hosts

    def register_worker(self, worker_id, vm_id, tag, address):
        """ Register a worker and associate it with a VM """
        with self.worker_lock:
            worker_info = {
                "worker_id": worker_id,
                "tag": tag,
                "address": address,
                "vm_id": vm_id,
                "vm_status": "running",  # Initially mark as running
            }
            self.worker_registry[worker_id] = worker_info
            self.available_workers.put(worker_info)  # Add the worker to the available pool
            self.vm_registry[vm_id] = "running"  # Mark the VM as running

    def remove_worker(self, worker_id):
        """ Remove a worker from the registry and free up the associated VM """
        with self.worker_lock:
            if worker_id in self.worker_registry:
                vm_id = self.worker_registry[worker_id]["vm_id"]
                del self.worker_registry[worker_id]
                self.available_workers.queue = [worker for worker in self.available_workers.queue if worker["worker_id"] != worker_id]  # Remove from queue
                self.vm_registry[vm_id] = "stopped"  # Mark the VM as stopped

    def get_worker_info(self, worker_id):
        """ Retrieve information about a specific worker """
        with self.worker_lock:
            return self.worker_registry.get(worker_id)

    def get_vm_status(self, vm_id):
        """ Retrieve the status of a specific VM """
        with self.worker_lock:
            return self.vm_registry.get(vm_id, "unknown")

    def scale_workers(self, current_worker_count):
        """ Scale the number of workers based on current workload """
        with self.worker_lock:
            if current_worker_count < self.MIN_WORKERS:
                self._add_workers(self.MIN_WORKERS - current_worker_count)
            elif current_worker_count > self.MAX_WORKERS:
                self._remove_workers(current_worker_count - self.MAX_WORKERS)

    def _add_workers(self, num_workers):
        """ Add new workers dynamically """
        for _ in range(num_workers):
            # Logic for creating new VM and starting worker will go here
            worker_id = f"worker_{len(self.worker_registry) + 1}"  # For example
            vm_id = f"vm_{len(self.vm_registry) + 1}"
            self.register_worker(worker_id, vm_id, "default_tag", f"127.0.0.{len(self.worker_registry) + 1}")

    def _remove_workers(self, num_workers):
        """ Remove workers dynamically """
        for _ in range(num_workers):
            if not self.available_workers.empty():
                worker_info = self.available_workers.get()
                self.remove_worker(worker_info["worker_id"])
