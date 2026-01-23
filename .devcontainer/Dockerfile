FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Basic tools
RUN apt update && apt install -y \
    curl \
    gnupg2 \
    lsb-release \
    build-essential \
    cmake \
    git \
    wget \
    software-properties-common \
    locales \
    sudo \
    && add-apt-repository -y universe \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# Locale
RUN locale-gen en_US en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# ROS 2 repository
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg

RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/ros2.list

# Install ROS 2 Humble (desktop or base)
RUN apt update && apt install -y \
    ros-humble-desktop \
    python3-colcon-common-extensions \
    python3-serial \
    python3-rosdep \
    python3-argcomplete \
    gazebo \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-gazebo-ros \
    && rm -rf /var/lib/apt/lists/*

# rosdep
RUN rosdep init || true
RUN rosdep update

# Source ROS automatically
RUN echo "source /opt/ros/humble/setup.bash" >> /etc/bash.bashrc

# Create dev user (recommended)
ARG USERNAME=ros
ARG UID=1000
ARG GID=1000

RUN groupadd -g $GID $USERNAME && \
    useradd -m -u $UID -g $GID -s /bin/bash $USERNAME && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER ros
WORKDIR /home/ros

CMD ["bash"]
