# docker run -it --rm --shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 \
#            --runtime nvidia -v ${PWD}:/workspace \
#            -p 7601:8501 \
#            nvidia/cuda:13.0.2-cudnn-devel-ubuntu22.04 /workspace/entry_point.sh

#!/bin/bash

CONTAINER_NAME="radar_7500"

# 检查容器是否存在（包括运行中和已停止的）
if docker container inspect "$CONTAINER_NAME" > /dev/null 2>&1; then
    echo "容器 $CONTAINER_NAME 已存在"
    
    # 检查容器是否在运行
    if [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME")" = "true" ]; then
        echo "容器正在运行，执行命令..."
    else
        echo "容器已停止，正在启动..."
        docker start "$CONTAINER_NAME"
    fi
else
    echo "容器 $CONTAINER_NAME 不存在，正在创建..."
    # 这里需要你提供创建容器的具体参数
    docker run -it \
              --runtime nvidia -v ${PWD}:/workspace \
              -p 7500:8501 \
              --name $CONTAINER_NAME --restart=always cc/cuda:13.0.2-cudnn-devel-ubuntu22.04 bash
fi

# 执行命令
docker exec -it "$CONTAINER_NAME" bash -c "./entry_point.sh"
