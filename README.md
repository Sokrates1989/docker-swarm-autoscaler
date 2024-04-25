# docker-swarm-autoscaler
Auto-Scaler for docker swarm

# Used libraries
- https://docker-py.readthedocs.io/en/stable/


# Push image to dockerhub

```bash
docker image ls sokrates1989/swarm-autoscaler
```

```bash
docker build -t swarm-autoscaler .
docker tag swarm-autoscaler sokrates1989/swarm-autoscaler:latest
docker tag swarm-autoscaler sokrates1989/swarm-autoscaler:major.minor.patch
docker login
docker push sokrates1989/swarm-autoscaler:latest
docker push sokrates1989/swarm-autoscaler:major.minor.patch
```


## Debug images

### Create

```bash
docker build -t swarm-autoscaler .
docker tag swarm-autoscaler sokrates1989/swarm-autoscaler:DEBUG-major.minor.patch
docker login
docker push sokrates1989/swarm-autoscaler:DEBUG-major.minor.patch
docker image ls sokrates1989/swarm-autoscaler
git status

```
### Cleanup / Delete
```bash
docker rmi sokrates1989/swarm-autoscaler:DEBUG-major.minor.patch
```

