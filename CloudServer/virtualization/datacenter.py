class Datacenter:
    def __init__(self, datacenter_id):
        self.datacenter_id = datacenter_id
        self.host_list = []

    def add_host(self, host):
        """Adds a host to the datacenter."""
        self.host_list.append(host)
        print(f"Host {host.host_id} added to Datacenter {self.datacenter_id}.")

    def remove_host(self, host):
        """Removes a host from the datacenter."""
        self.host_list.remove(host)
        print(f"Host {host.id} removed from Datacenter {self.datacenter_id}.")
