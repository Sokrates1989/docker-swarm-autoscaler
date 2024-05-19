from prometheus_api_client import PrometheusConnect

class PrometheusConnector:
    def __init__(self):
        _prometheus_url = "http://prometheus:9090"
        self._prometheusClient = PrometheusConnect(url=_prometheus_url)
        self._customizable_cpu_query = "avg(rate(container_cpu_usage_seconds_total{{container_label_com_docker_swarm_service_name='{}', container_label_com_docker_swarm_task_name=~'.+'}}[{}])) * 100"
        self._customizable_memory_query="avg(container_memory_usage_bytes{{container_label_com_docker_swarm_service_name='{}', container_label_com_docker_swarm_task_name=~'.+'}})"
        self._cpuQuery30Seconds="avg(rate(container_cpu_usage_seconds_total{container_label_com_docker_swarm_task_name=~'.+'}[30s]))BY(container_label_com_docker_swarm_service_name)*100"

    def get_all_services(self):

        # Execute prometheus query.
        result = self._prometheusClient.custom_query(query=self._cpuQuery30Seconds)

        # Return services.
        services = []
        for item in result:
            services.append(item['metric']['container_label_com_docker_swarm_service_name'])
        return services


    def get_custom_cpu_metric(self, service_name, time_duration):

        # Execute prometheus query.
        customized_cpu_query = self._customizable_cpu_query.format(service_name, time_duration)
        result = self._prometheusClient.custom_query(query=customized_cpu_query)
        
        # Return cpu value.
        return float(result[0]['value'][1]) if result[0]['value'][1] else 0.0


    def get_custom_memory_metric(self, service_name):

        # Execute prometheus query.
        customized_memory_query = self._customizable_memory_query.format(service_name)
        result = self._prometheusClient.custom_query(query=customized_memory_query)

        # Return memory value.
        return float(result[0]['value'][1]) if result[0]['value'][1] else 0.0

    