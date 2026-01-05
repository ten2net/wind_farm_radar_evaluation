FROM nvidia/cuda:13.0.2-cudnn-devel-ubuntu22.04

# 安装必要的软件包
RUN apt update -o Acquire::AllowInsecureRepositories=true && \
    apt install -y --no-install-recommends git && \
    apt install -y --allow-unauthenticated python3 python3-pip python-is-python3
RUN pip install uv -U -i https://pypi.tuna.tsinghua.edu.cn/simple

# 设置工作目录
WORKDIR /workspace

# 暴露 8501 端口（通常用于 Streamlit、Gradio 等应用）
EXPOSE 8501

# 设置默认命令（可选）
CMD ["/bin/bash"]

# uv sync    && \
# uv pip install ipykernel  && \
# uv pip install -e .

# docker build --build-arg HTTPS_PROXY=http://192.168.200.24:7890 --build-arg HTTP_PROXY=http://192.168.200.24:7890 -t cc/cuda:13.0.2-cudnn-devel-ubuntu22.04 .

# 运行容器，挂载 outputs 目录到宿主机，并映射端口
docker run -it --gpus all --name radar_8501 --restart=always \
  -p 8501:8501 \
  -v $(pwd)/:/workspace \
  cc/cuda:13.0.2-cudnn-devel-ubuntu22.04
