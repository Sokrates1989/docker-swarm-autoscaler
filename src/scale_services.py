# Import own classes.
# Insert path to own stuff to allow importing them.
import os
import sys

sys.path.insert(1, os.path.join(os.path.dirname(__file__), "utils"))

# For getting datestrings.
import dateStringUtils

# For scaling services.
import dockerServiceScaler as DockerServiceScaler
dockerServiceScaler = DockerServiceScaler.DockerServiceScaler()

# For retrieving container/ service metrics via prometheus.
import prometheusConnector as PrometheusConnector
prometheusConnector = PrometheusConnector.PrometheusConnector()

# Test usage.
# Print current date.
print(dateStringUtils.getDateStringForLogTag())

# # Get current replicas of service.
# serviceName = "wordpress_test_wordpress"
# is_int, replicas = dockerServiceScaler.get_current_replicas(serviceName)
# if is_int:
#     print(f"Service {serviceName}, Get replicas: Is integer: {is_int}, Replicas: {replicas}")
# else:
#     print(replicas)

# Print all services that should auto-scale.
autoscale_services = dockerServiceScaler.get_autoscale_services()
print("Services that should auto-scale:")
for autoscale_service in autoscale_services:
    print(autoscale_service)


# # Print all service names from Prometheus.
# services = prometheusConnector.get_all_services()
# print("Services retrieved from Prometheus:")
# for service in services:
#     print(service)

# # Print service names and their CPU values.
# services = prometheusConnector.get_cpu_avg_30seconds_all_services()
# print("Services with their CPU value from Prometheus:")
# for service in services:
#     print(f"Service: {service['service_name']}, CPU Value: {service['cpu_value']}")

