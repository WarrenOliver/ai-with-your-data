# Docker Commands

### Build Docker Image
docker build -t ai-with-your-data .

### Run Docker Image
docker run -p 5000:5000 ai-with-your-data
<!-- Run "docker run -d -p 5000:5000 ai-with-your-data" to run in background-->
<!-- 4000:5000 is the temporary port while on local machine -->


### SSH into docker container
docker exec -it my-container bash


### Tag the docker image (0.5 is the latest)
docker tag ai-with-your-data oliversdg/awyd:0.5

### Push Docker image to registry (0.5 is the latest)
docker push oliversdg/awyd:0.5


## On server side

### Pull docker image from DockerHub Registry (0.5 is the latest)
sudo docker pull oliversdg/awyd:0.5

### Run docker image on server
sudo docker run -d -p 80:5000 oliversdg/awyd:0.5