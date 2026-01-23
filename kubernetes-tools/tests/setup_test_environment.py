"""
Setup script for creating test environment for kubernetes-tools tests.
"""
import os
from pathlib import Path
from kubernetes import client, config
from kubernetes.client.rest import ApiException


def load_kube_config():
    """Load Kubernetes configuration."""
    try:
        config.load_kube_config()
    except config.ConfigException:
        config.load_incluster_config()


def delete_namespace_if_exists(namespace: str) -> bool:
    """
    Delete a namespace if it exists.

    Args:
        namespace: Name of the namespace to delete

    Returns:
        True if namespace was deleted, False if it didn't exist
    """
    load_kube_config()
    v1 = client.CoreV1Api()

    try:
        v1.read_namespace(name=namespace)
        print(f"Namespace '{namespace}' exists, deleting...")
        v1.delete_namespace(name=namespace, body=client.V1DeleteOptions())
        print(f"Namespace '{namespace}' deleted successfully")

        # Wait for namespace to be fully deleted
        import time
        max_wait = 60
        elapsed = 0
        while elapsed < max_wait:
            try:
                v1.read_namespace(name=namespace)
                print(f"Waiting for namespace '{namespace}' to be deleted...")
                time.sleep(2)
                elapsed += 2
            except ApiException as e:
                if e.status == 404:
                    print(f"Namespace '{namespace}' fully deleted")
                    break
                raise
        return True
    except ApiException as e:
        if e.status == 404:
            print(f"Namespace '{namespace}' does not exist, skipping deletion")
            return False
        raise


def create_namespace(namespace: str, labels: dict = None) -> client.V1Namespace:
    """
    Create a namespace.

    Args:
        namespace: Name of the namespace to create
        labels: Optional labels to apply to the namespace

    Returns:
        The created V1Namespace object
    """
    load_kube_config()
    v1 = client.CoreV1Api()

    namespace_metadata = client.V1ObjectMeta(
        name=namespace,
        labels=labels or {}
    )
    namespace_body = client.V1Namespace(
        metadata=namespace_metadata
    )

    try:
        ns = v1.create_namespace(body=namespace_body)
        print(f"Namespace '{namespace}' created successfully")
        return ns
    except ApiException as e:
        print(f"Error creating namespace '{namespace}': {e}")
        raise


def create_configmap(name: str, namespace: str, data: dict) -> client.V1ConfigMap:
    """
    Create a ConfigMap.

    Args:
        name: Name of the ConfigMap
        namespace: Namespace for the ConfigMap
        data: Data dictionary for the ConfigMap

    Returns:
        The created V1ConfigMap object
    """
    load_kube_config()
    v1 = client.CoreV1Api()

    configmap = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(name=name, namespace=namespace),
        data=data
    )

    try:
        cm = v1.create_namespaced_config_map(namespace=namespace, body=configmap)
        print(f"ConfigMap '{name}' created in namespace '{namespace}'")
        return cm
    except ApiException as e:
        print(f"Error creating ConfigMap '{name}': {e}")
        raise


def create_pod(pod_spec: dict, namespace: str) -> client.V1Pod:
    """
    Create a pod from a specification.

    Args:
        pod_spec: Dictionary containing pod specification
        namespace: Namespace for the pod

    Returns:
        The created V1Pod object
    """
    load_kube_config()
    v1 = client.CoreV1Api()

    try:
        pod = v1.create_namespaced_pod(namespace=namespace, body=pod_spec)
        print(f"Pod '{pod_spec['metadata']['name']}' created in namespace '{namespace}'")
        return pod
    except ApiException as e:
        print(f"Error creating pod '{pod_spec['metadata']['name']}': {e}")
        raise


def create_service(service_spec: dict, namespace: str) -> client.V1Service:
    """
    Create a service from a specification.

    Args:
        service_spec: Dictionary containing service specification
        namespace: Namespace for the service

    Returns:
        The created V1Service object
    """
    load_kube_config()
    v1 = client.CoreV1Api()

    try:
        service = v1.create_namespaced_service(namespace=namespace, body=service_spec)
        print(f"Service '{service_spec['metadata']['name']}' created in namespace '{namespace}'")
        return service
    except ApiException as e:
        print(f"Error creating service '{service_spec['metadata']['name']}': {e}")
        raise


def create_test_app_environment(cleanup: bool = True) -> None:
    """
    Create the complete test-app environment from test-app.yaml.

    This function creates:
    - test-app namespace
    - frontend pod (nginx)
    - backend pod (python flask app)
    - mysql pod with query-logger sidecar
    - mysql-config ConfigMap
    - Services for frontend, backend, and mysql

    Args:
        cleanup: If True, delete existing namespace before creating resources
    """
    load_kube_config()
    namespace = "test-app"

    # Step 1: Cleanup if requested
    if cleanup:
        delete_namespace_if_exists(namespace)

    # Step 2: Create namespace
    create_namespace(namespace, labels={"name": "test-app"})

    # Step 3: Create ConfigMap for MySQL
    mysql_config_data = {
        "my.cnf": """[mysqld]
general_log = 1
general_log_file = /var/log/mysql/queries.log
log_queries_not_using_indexes = 1
log_error_verbosity = 3
slow_query_log = 1
"""
    }
    create_configmap("mysql-config", namespace, mysql_config_data)

    # Step 4: Create Pods
    # Frontend Pod
    frontend_pod = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": "frontend",
            "namespace": namespace,
            "labels": {"app": "frontend"}
        },
        "spec": {
            "containers": [{
                "name": "frontend",
                "image": "nginx:alpine",
                "ports": [{"containerPort": 8080}],
                "command": ["/bin/sh"],
                "args": [
                    "-c",
                    """cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 8080;
    location / {
        proxy_pass http://backend.test-app.svc.cluster.local:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF
nginx -g 'daemon off;'"""
                ]
            }]
        }
    }
    create_pod(frontend_pod, namespace)

    # Backend Pod
    backend_pod = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": "backend",
            "namespace": namespace,
            "labels": {"app": "backend"}
        },
        "spec": {
            "containers": [{
                "name": "backend",
                "image": "python:3.9-slim",
                "ports": [{"containerPort": 8080}],
                "env": [
                    {"name": "DB_HOST", "value": "mysql.db.svc.cluster.local"},
                    {"name": "DB_PORT", "value": "3306"},
                    {"name": "DB_USER", "value": "root"},
                    {"name": "DB_PASSWORD", "value": "password"},
                    {"name": "DB_NAME", "value": "testdb"}
                ],
                "command": ["/bin/sh"],
                "args": [
                    "-c",
                    """pip install flask mysql-connector-python
cat > app.py << 'EOF'
from flask import Flask
import mysql.connector
import json

app = Flask(__name__)

@app.route('/')
def test_db():
    try:
        conn = mysql.connector.connect(
            host="mysql.db.svc.cluster.local",
            port=3306,
            user="root",
            password="password",
            database="testdb"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 'Database connection successful!' as message, NOW() as timestamp")
        result = cursor.fetchone()
        conn.close()
        return {"status": "success", "message": result[0], "timestamp": str(result[1])}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF
python app.py"""
                ]
            }]
        }
    }
    create_pod(backend_pod, namespace)

    # MySQL Pod
    mysql_pod = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": "mysql",
            "namespace": namespace,
            "labels": {"app": "db"}
        },
        "spec": {
            "containers": [
                {
                    "name": "mysql",
                    "image": "mysql:8.0",
                    "ports": [{"containerPort": 3306}],
                    "env": [
                        {"name": "MYSQL_ROOT_PASSWORD", "value": "password"},
                        {"name": "MYSQL_DATABASE", "value": "testdb"}
                    ],
                    "volumeMounts": [
                        {
                            "name": "mysql-config-volume",
                            "mountPath": "/etc/mysql/conf.d",
                            "readOnly": True
                        },
                        {
                            "name": "query-log",
                            "mountPath": "/var/log/mysql",
                            "readOnly": False
                        }
                    ]
                },
                {
                    "name": "query-logger",
                    "image": "busybox",
                    "command": ["/bin/sh", "-c", "tail -f /var/log/mysql/queries.log"],
                    "volumeMounts": [
                        {
                            "name": "query-log",
                            "mountPath": "/var/log/mysql",
                            "readOnly": True
                        }
                    ]
                }
            ],
            "volumes": [
                {
                    "name": "mysql-config-volume",
                    "configMap": {"name": "mysql-config"}
                },
                {
                    "name": "query-log",
                    "emptyDir": {}
                }
            ]
        }
    }
    create_pod(mysql_pod, namespace)

    # Step 5: Create Services
    # Frontend Service
    frontend_service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": "frontend",
            "namespace": namespace
        },
        "spec": {
            "selector": {"app": "frontend"},
            "ports": [{"port": 8080, "targetPort": 8080}],
            "type": "NodePort"
        }
    }
    create_service(frontend_service, namespace)

    # Backend Service
    backend_service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": "backend",
            "namespace": namespace
        },
        "spec": {
            "selector": {"app": "backend"},
            "ports": [{"port": 8080, "targetPort": 8080}]
        }
    }
    create_service(backend_service, namespace)

    # MySQL Service
    mysql_service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": "mysql",
            "namespace": namespace
        },
        "spec": {
            "selector": {"app": "db"},
            "ports": [{"port": 3306, "targetPort": 3306}]
        }
    }
    create_service(mysql_service, namespace)

    print(f"\nTest environment created successfully in namespace '{namespace}'")
    print("Resources created:")
    print("  - Namespace: test-app")
    print("  - ConfigMap: mysql-config")
    print("  - Pods: frontend, backend, mysql")
    print("  - Services: frontend, backend, mysql")


def create_deny_all_network_policy(namespace: str) -> client.V1NetworkPolicy:
    """
    Create a deny-all network policy in the specified namespace.

    This network policy will:
    - Select all pods in the namespace (empty podSelector)
    - Deny all ingress traffic (empty ingress list)
    - Deny all egress traffic (empty egress list)

    Args:
        namespace: Namespace where the network policy should be created

    Returns:
        The created V1NetworkPolicy object
    """
    load_kube_config()
    networking_v1 = client.NetworkingV1Api()

    network_policy = client.V1NetworkPolicy(
        metadata=client.V1ObjectMeta(
            name="deny-all",
            namespace=namespace
        ),
        spec=client.V1NetworkPolicySpec(
            pod_selector=client.V1LabelSelector(
                match_labels={}  # Empty selector matches all pods
            ),
            policy_types=["Ingress", "Egress"],
            ingress=[],  # Empty list denies all ingress
            egress=[]    # Empty list denies all egress
        )
    )

    try:
        # Check if policy already exists and delete it
        try:
            networking_v1.read_namespaced_network_policy(name="deny-all", namespace=namespace)
            print(f"Network policy 'deny-all' already exists in namespace '{namespace}', deleting...")
            networking_v1.delete_namespaced_network_policy(
                name="deny-all",
                namespace=namespace,
                body=client.V1DeleteOptions()
            )
            print(f"Network policy 'deny-all' deleted")
        except ApiException as e:
            if e.status != 404:
                raise

        # Create the network policy
        np = networking_v1.create_namespaced_network_policy(
            namespace=namespace,
            body=network_policy
        )
        print(f"Deny-all network policy created in namespace '{namespace}'")
        return np
    except ApiException as e:
        print(f"Error creating deny-all network policy: {e}")
        raise


def cleanup_test_environment(namespace: str = "test-app") -> None:
    """
    Clean up the test environment by deleting the namespace.

    Args:
        namespace: Name of the namespace to delete (default: "test-app")
    """
    delete_namespace_if_exists(namespace)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        print("Cleaning up test environment...")
        cleanup_test_environment()
    elif len(sys.argv) > 1 and sys.argv[1] == "deny-all":
        print("Creating deny-all network policy...")
        create_deny_all_network_policy("test-app")
    else:
        print("Setting up test environment...")
        create_test_app_environment(cleanup=True)
        print("\nTo create a deny-all network policy, run:")
        print("  python setup_test_environment.py deny-all")
        print("\nTo cleanup, run:")
        print("  python setup_test_environment.py cleanup")
