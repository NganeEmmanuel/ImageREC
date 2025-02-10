import sys
import os

import grpc
import random
import subprocess
from concurrent import futures
from threading import Thread

import image_processing_pb2_grpc


class VirtualMachine:
    def __init__(self, app_name, vm_id, ram=8, cpu=4, storage=80):
        """
        Simulates a virtual machine with defined resources.

        Args:
            app_name (str): The name of the application.
            vm_id (str): Unique identifier for the VM.
            ram (int): Amount of RAM in GB.
            cpu (int): Number of CPU cores.
            storage (int): Storage in GB.
        """
        self.app_name = app_name
        self.vm_id = vm_id
        self.ram = ram
        self.cpu = cpu
        self.storage = storage
        self.status = "stopped"
        self.ip_address = self.assign_ip()
        self.applications = []

    def assign_ip(self):
        """Assigns a random IP address for networking simulation."""
        return f"192.168.1.{random.randint(2, 254)}"

    def start_vm(self):
        """Starts the VM and assigns resources."""
        if self.status == "running":
            print(f"VM {self.vm_id} is already running.")
            return
        self.status = "running"
        print(f"VM {self.vm_id} started with {self.cpu} CPUs, {self.ram}GB RAM, {self.storage}GB Storage.")

    def stop_vm(self, worker_address, shared_worker_state):
        """Stops the VM and releases resources."""
        if self.status == "stopped":
            print(f"VM {self.vm_id} is already stopped.")
            return
        print(f"Stopping worker at {worker_address}...")

        # Kill worker process
        with shared_worker_state.worker_lock:
            process = shared_worker_state.worker_registry[worker_address]["process"]
            process.terminate()
            del shared_worker_state.worker_registry[worker_address]

        print(f"Worker at {worker_address} stopped successfully.")
        print(f"Stopping worker at {worker_address}...")
        self.status = "stopped"
        print(f"VM {self.vm_id} stopped.")

    def start_worker_application(self, action_type, model_requested, port, model_path, worker_address):
        """Simulates running an application inside the VM."""
        if self.status != "running":
            print(f"Cannot start {self.app_name}. VM {self.vm_id} is not running.")
            return
        self.applications.append(self.app_name)

        print(f"Starting new worker at {worker_address}...")

        python_executable = sys.executable
        worker_script = os.path.abspath("worker.py")

        process = subprocess.Popen(
            [python_executable, worker_script, str(port), self.vm_id, model_requested, action_type, model_path]
        )

        print(f"Worker application {self.app_name} started in VM {self.vm_id}.")
        return process

    def stop_application(self, app_name):
        """Stops a running application inside the VM."""
        if app_name in self.applications:
            self.applications.remove(app_name)
            print(f"Application {app_name} stopped in VM {self.vm_id}.")
        else:
            print(f"Application {app_name} not found in VM {self.vm_id}.")

    def health_check(self):
        """Simulates a health check with a 10% failure rate."""
        return self.status

    def get_status(self):
        """Returns VM status and running applications."""
        return {
            "vm_id": self.vm_id,
            "status": self.status,
            "ip_address": self.ip_address,
            "cpu": self.cpu,
            "ram": self.ram,
            "storage": self.storage,
            "running_apps": self.applications
        }

    def run_master_application(self, auto_scaling_process, request_process, service_servicer_class, shared_worker_state,
                               app_name, port):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        image_processing_pb2_grpc.add_MasterServiceServicer_to_server(service_servicer_class(), server)
        server.add_insecure_port(f"[::]:{port}")

        # start master application processes for autoscaling and processing request
        Thread(target=request_process, daemon=True).start()
        Thread(target=auto_scaling_process, args=(shared_worker_state,), daemon=True).start()

        # Add the master application to the application registry of the VM
        self.applications.append(app_name)

        print(f"Master server started on port {port}")
        server.start()
        server.wait_for_termination()
