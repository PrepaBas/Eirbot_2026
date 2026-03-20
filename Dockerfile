FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV ROS_DISTRO=humble

# Basic tools
RUN apt update && apt install -y \
    curl \
    gnupg2 \
    lsb-release \
    build-essential \
    cmake \
    git \
    wget \
    locales \
    sudo \
    software-properties-common \
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
    libserial-dev \
    ros-humble-desktop \
    python3-colcon-common-extensions \
    python3-serial \
    python3-rosdep \
    python3-argcomplete \
    && rm -rf /var/lib/apt/lists/*

RUN apt update && apt install -y \
    ros-humble-xacro \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    ros-humble-joint-state-publisher \
    ros-humble-joint-state-publisher-gui \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    && rm -rf /var/lib/apt/lists/*

# install Just
RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# Source ROS automatically
#RUN echo "source /opt/ros/humble/setup.bash" >> /etc/bash.bashrc
#RUN echo "source ~/ros2_ws/install/setup.bash" >> /etc/bash.bashrc

# Create dev user (recommended)
ARG USERNAME=ros
ARG UID=1000
ARG GID=1000

RUN groupadd -g $GID $USERNAME && \
    useradd -m -u $UID -g $GID -s /bin/bash $USERNAME && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# 5. Préparation de l'espace de travail
WORKDIR /home/ros/ros2_ws

# On copie le code source
COPY --chown=ros:ros src ./src

# --- RÉPARATION DE ROSDEP ---
RUN sudo rosdep init

USER root
RUN rosdep update

USER root
RUN apt-get update && \
    rosdep install --from-paths src --ignore-src -y && \
    rm -rf /var/lib/apt/lists/*

# On repasse en utilisateur ROS pour la suite
USER ros
# ----------------------------
    
# 6. Entrypoint
USER root
COPY ./ros_entrypoint.sh /
RUN chmod +x /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]

USER ros
CMD ["bash"]