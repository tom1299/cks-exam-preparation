#!/bin/bash
set -euxo pipefail

# Get the node container name
NODE_CONTAINER_NAME=$(docker ps --filter "name=kind-control-plane" --format "{{.Names}}")

# Copy the setup script to the node
docker cp setup-master-node.sh "${NODE_CONTAINER_NAME}":/setup-master-node.sh

# Execute the script on the node
docker exec "${NODE_CONTAINER_NAME}" /bin/bash /setup-master-node.sh

# Clean up the script from the node
docker exec "${NODE_CONTAINER_NAME}" rm /setup-master-node.sh

echo "Script executed on the node and cleaned up successfully!"
