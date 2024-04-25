import docker

class DockerServiceScaler:
    """
    A class for scaling Docker services and retrieving their current replicas.

    This class provides methods to scale Docker services to a specified number of replicas
    and retrieve the current number of replicas for a given service.

    Methods:
        scale_service: Scale the specified service to the given number of replicas.
        get_current_replicas: Retrieve the current number of replicas for the specified service.
    """

    def __init__(self):
        self.client = docker.from_env()

    def scale_service(self, service_name, replicas):
        """
        Scale the specified service to the given number of replicas.

        Parameters:
            service_name (str): The name of the service to scale.
            replicas (int): The desired number of replicas for the service.

        Returns:
            None
        """
        try:
            # Get the service.
            service = self.client.services.get(service_name)
            
            # Update the service with the new number of replicas.
            success_scaling = service.scale(replicas)

            # Evaluate sclaing success and return state of scaling attempt.    
            if success_scaling:
                print(f"Successfully scaled service {service_name} to {replicas} replicas.")
                return True
            else:
                errorMsg=f"Unknown issue: Could not change {service_name} to {replicas} replicas."
                print(errorMsg)
                return errorMsg
        # Service not found error.
        except docker.errors.NotFound:
            errorMsg=f"Service {service_name} not found."
            print(errorMsg)
            return errorMsg
        # Other error.
        except docker.errors.APIError as e:
            errorMsg=f"Error occurred while scaling service {service_name}: {e}"
            print(errorMsg)
            return errorMsg

    def get_current_replicas(self, service_name):
        """
        Retrieve the current number of replicas for the specified service.

        Parameters:
            service_name (str): The name of the service to query.

        Returns:
            tuple: A tuple containing a boolean indicating whether the replicas count is an integer,
                   and either the integer count or an error message.
        """
        try:
            # Get the service.
            service = self.client.services.get(service_name)
            
            # Access the replicas attribute of the service.
            current_replicas = service.attrs['Spec']['Mode']['Replicated']['Replicas']

            if isinstance(current_replicas, int):
                return True, int(current_replicas)
            else:
                return False, current_replicas
        except docker.errors.NotFound:
            return False, f"Service {service_name} not found."
        except docker.errors.APIError as e:
            return False, f"Error occurred while getting replicas for service {service_name}: {e}"



    def get_autoscale_services(self):
        """
        Retrieve all services with autoscale enabled.

        Returns:
            list: A list of dictionaries containing information about autoscale-enabled services.
                Each dictionary contains keys: "name", "minimum_replicas", "maximum_replicas".
        """
        autoscale_services = []
        try:
            services = self.client.services.list()
            for service in services:

                # Check if the label "autoscale" is set to "true"
                if "Labels" in service.attrs["Spec"] and "autoscale" in service.attrs["Spec"]["Labels"] and service.attrs["Spec"]["Labels"]["autoscale"] == "true":
                    if "autoscale.minimum_replicas" in service.attrs["Spec"]["Labels"] and "autoscale.maximum_replicas" in service.attrs["Spec"]["Labels"]:
                        service_to_autoscale = {
                            "name": service.attrs["Spec"]["Name"],
                            "minimum_replicas": service.attrs["Spec"]["Labels"]["autoscale.minimum_replicas"],
                            "maximum_replicas": service.attrs["Spec"]["Labels"]["autoscale.maximum_replicas"]
                        }
                        autoscale_services.append(service_to_autoscale)
                    else:
                        raise ValueError("autoscale.minimum_replicas and autoscale.maximum_replicas labels are not set for service:", service.attrs["Spec"]["Name"])
            return autoscale_services
        except docker.errors.APIError as e:
            print(f"Error occurred while fetching autoscale services: {e}")
            return autoscale_services
        