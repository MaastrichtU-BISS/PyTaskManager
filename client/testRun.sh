docker rmi jvsoest/ptm_client
docker build -t jvsoest/ptm_client ./

docker volume create ioData

docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v $(pwd)/config.json:/ptm_client/config.json \
    -v ioData:/ioData \
    jvsoest/ptm_client
