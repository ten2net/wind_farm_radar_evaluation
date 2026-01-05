docker run -it --shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 \
           --runtime nvidia -v ${PWD}:/workspace \
           --name radar_wtc --restart=always nvidia/cuda:13.0.2-cudnn-devel-ubuntu22.04 bash