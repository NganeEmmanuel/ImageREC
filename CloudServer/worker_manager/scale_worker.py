import time
import grpc

import image_processing_pb2
import image_processing_pb2_grpc
from CloudServer.model_manager.model_manger import get_model_path
from CloudServer.virtualization.virtual_machine import VirtualMachine


def check_worker_ready(worker_address, timeout=15):
    """
    Waits for a worker to signal readiness by sending a HealthCheck.
    """
    print(f"Checking readiness of worker at {worker_address}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with grpc.insecure_channel(worker_address) as channel:
                stub = image_processing_pb2_grpc.WorkerServiceStub(channel)
                stub.HealthCheck(image_processing_pb2.HealthRequest())
                print(f"Worker {worker_address} is ready.")
                return True
        except grpc.RpcError:
            time.sleep(1)
    print(f"Worker {worker_address} failed to respond.")
    return False


def start_worker(shared_worker_state, port, model_requested, action_type):
    """
    Start a worker process in a new VM at the specified port.
    """
    worker_id = f"worker_{port}"
    app_name = f"worker_{model_requested}"
    model_path = get_model_path(model_requested)  # gets the path to the appropriate model
    worker_address = f"localhost:{port}"

    # Create a new VM using the VirtualMachine class
    vm = VirtualMachine(app_name, worker_id)

    # Ge worker host for worker VMs
    worker_host = shared_worker_state.worker_host_registry[2]["worker_host"]
    worker_host.allocate_vm(vm) # add vm to worker host
    vm.start_vm()  # Start VM and load application within the VM
    process = vm.start_worker_application(
        action_type,model_requested,port, model_path, worker_address
    )  # start worker app in VM and load the model

    # Wait a short time to allow the worker to initialize and respond to health checks
    time.sleep(6)

    if check_worker_ready(worker_address):
        with shared_worker_state.worker_lock:
            shared_worker_state.worker_registry[worker_address] = {
                "vm": vm,  # Store the VM instance
                "process": process, # store worker process within VM
                "last_active": time.time(),
                "model_name": model_requested,  # This is the tag. Used during monitoring to start up the workers with
                # the appropriate models
                "action_type": action_type
            }
            shared_worker_state.available_workers.put(worker_address)
        print(f"Worker at {worker_address} is ready.")
    else:
        print(f"Failed to start worker at {worker_address}.")


def stop_worker(shared_worker_state, worker_address):
    """
    Stop the worker VM and remove it from the registry.
    """
    with shared_worker_state.worker_lock:
        vm = shared_worker_state.worker_registry[worker_address]["vm"]
        print(f"Stopping virtual machine: {vm.vm_id}")
        vm.stop_vm(worker_address, shared_worker_state)  # Stop the VM
        del shared_worker_state.worker_registry[worker_address]


def scale_workers(shared_worker_state, required_workers, model_requested, action_type):
    """
    Adjust the number of active workers to match the required count.
    """
    current_workers = len(shared_worker_state.worker_registry)

    print(f"Scaling workers. Current: {current_workers}, Required: {required_workers}")

    # Start new workers if needed
    if current_workers < required_workers:
        print(f"Starting new workers to reach {required_workers} workers.")
        for port in range(shared_worker_state.BASE_WORKER_PORT + current_workers, shared_worker_state.BASE_WORKER_PORT + required_workers):
            start_worker(shared_worker_state, port, model_requested, action_type)

    # Stop excess workers
    if current_workers > required_workers:
        excess_workers = list(shared_worker_state.worker_registry.keys())[required_workers:]
        for worker_address in excess_workers:
            stop_worker(shared_worker_state, worker_address)


def monitor_workers(shared_worker_state):
    """
    Monitors workers, restarts them if they stop unexpectedly or become idle.
    """
    while True:
        time.sleep(10)
        with shared_worker_state.worker_lock:
            for worker_address, info in list(shared_worker_state.worker_registry.items()):
                if info["vm"].health_check() != "running":  # Check if the VM is still running
                    print(f"Worker {worker_address} stopped unexpectedly.")
                    port = int(worker_address.split(":")[1])
                    start_worker(shared_worker_state, port, info["model_name"], info["action_type"])
                elif time.time() - info["last_active"] > shared_worker_state.WORKER_IDLE_TIMEOUT:
                    print(f"Worker {worker_address} idle for too long. Stopping.")
                    stop_worker(shared_worker_state, worker_address)
