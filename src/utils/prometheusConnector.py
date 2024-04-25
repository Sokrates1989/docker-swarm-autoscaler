from prometheus_api_client import PrometheusConnect

class PrometheusConnector:
    def __init__(self):
        prometheus_url = "http://prometheus:9090"
        self.prometheusClient = PrometheusConnect(url=prometheus_url)
        self.cpuQuery30Seconds="avg(rate(container_cpu_usage_seconds_total{container_label_com_docker_swarm_task_name=~'.+'}[30s]))BY(container_label_com_docker_swarm_service_name)*100"

    def get_all_services(self):

        # Execute proemtheus query.
        result = self.prometheusClient.custom_query(query=self.cpuQuery30Seconds)

        # Return services.
        services = []
        for item in result:
            services.append(item['metric']['container_label_com_docker_swarm_service_name'])
        return services


    def get_cpu_avg_30seconds_all_services(self):

        # Execute proemtheus query.
        result = self.prometheusClient.custom_query(query=self.cpuQuery30Seconds)

        # Return services.
        services = []
        for item in result:
            service_name = item['metric']['container_label_com_docker_swarm_service_name']
            cpu_value = float(item['value'][1]) if item['value'][1] else 0.0
            services.append({'service_name': service_name, 'cpu_value': cpu_value})
        return services
    