# Utilisation de l'image officielle pré-configurée (Ubuntu 22.04 + ROS Humble Desktop)
FROM osrf/ros:humble-desktop

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# 1. Outils de base et dépendances système
# Note: curl, gnupg2, etc. sont souvent déjà là, mais on assure le coup
RUN apt-get update && apt-get install -y \
    libserial-dev \
    python3-colcon-common-extensions \
    python3-serial \
    python3-argcomplete \
    curl \
    git \
    wget \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# 2. Installation des packages ROS 2 (Adapté ARM64 / x86_64)
# J'ai retiré 'gazebo' (classic) qui pose problème sur ARM
RUN apt-get update && apt-get install -y \
    ros-humble-xacro \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    ros-humble-joint-state-publisher \
    ros-humble-joint-state-publisher-gui \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    && rm -rf /var/lib/apt/lists/*

# 3. Installation de 'Just'
RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# 4. Gestion de l'utilisateur (UID/GID 1000 pour éviter les problèmes de droits avec l'hôte)
ARG USERNAME=ros
ARG UID=1000
ARG GID=1000

RUN groupadd -g $GID $USERNAME && \
    useradd -m -u $UID -g $GID -s /bin/bash $USERNAME && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# 5. Préparation de l'espace de travail
WORKDIR /home/ros/ros2_ws
USER ros

# Rosdep update (init est déjà fait dans l'image de base OSRF)
RUN rosdep update

# On copie le code source
COPY --chown=ros:ros src ./src

# Installation automatique des dépendances manquantes via rosdep
RUN sudo apt-get update && \
    rosdep install --from-paths src --ignore-src -y && \
    sudo rm -rf /var/lib/apt/lists/*

# 6. Entrypoint (L'image OSRF a déjà un entrypoint, on le remplace par le tien)
USER root
COPY ./ros_entrypoint.sh /
RUN chmod +x /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]

USER ros
CMD ["bash"]