# Docker Commands

### Build Docker Image
docker build -t arti-image .

### Run Docker Image
docker run -p 5000:5000 arti-image
<!-- Run "docker run -d -p 5000:5000 arti-image" to run in background-->
<!-- 4000:5000 is the temporary port while on local machine -->


### SSH into docker container
docker exec -it my-container bash


### Tag the docker image (0.5 is the latest)
docker tag arti-image oliversdg/arti:0.5

### Push Docker image to registry (0.5 is the latest)
docker push oliversdg/arti:0.3


## On server side

### Pull docker image from DockerHub Registry (0.5 is the latest)
sudo docker pull oliversdg/arti:0.5

### Run docker image on server
sudo docker run -d -p 80:5000 oliversdg/arti:0.5