# Import own classes.
# Insert path to own stuff to allow importing them.
import os
import sys
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "utils"))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "utils", "messaging"))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "models"))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "definitions"))

# For scaling services.
import dockerServiceScaler as DockerServiceScaler
dockerServiceScaler = DockerServiceScaler.DockerServiceScaler()

# Autoscale.
dockerServiceScaler.auto_scale_services()
