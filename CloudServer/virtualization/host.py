class Host:
    def __init__(self, host_id, os, arch, cpu, ram_capacity):
        self.host_id = host_id
        self.os = os
        self.arch = arch
        self.cpu = cpu
        self.ram_capacity = ram_capacity
        self.vm_list = []

    def allocate_vm(self, vm):
        """Assigns a VM to this host."""
        self.vm_list.append(vm)
        print(f"VM {vm.vm_id} allocated to Host {self.host_id}.")

    def deallocate_vm(self, vm):
        """Deallocates a VM from this host."""
        self.vm_list.remove(vm)
        print(f"VM {vm.vm_id} deallocated from Host {self.host_id}.")

