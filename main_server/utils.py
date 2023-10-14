import docker
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)


def get_containers_address_in_network(network_name):
    client = docker.from_env()
    containers = client.containers.list()

    # Filter containers in the specified network
    network_containers = [
        container.attrs['NetworkSettings']['Networks'][network_name]["IPAddress"]
        for container in containers
        if network_name in container.attrs['NetworkSettings']['Networks']
        and 'secondary' in container.attrs['Name']
    ]

    LOGGER.info(f"network_containers: {network_containers}")

    return network_containers
