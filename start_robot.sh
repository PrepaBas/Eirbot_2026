#!/bin/bash

#!/bin/bash

# 1. On tue l'ancienne session Tmux s'il y en a une
tmux kill-session -t eurobot 2>/dev/null

# 2. On force l'arrêt des processus ROS qui pourraient traîner dans le docker
docker exec my_ros_container pkill rviz2 2>/dev/null
docker exec my_ros_container pkill -f micro_ros_agent 2>/dev/null
docker exec my_ros_container pkill -f ros2 2>/dev/null

# 3. On attend une seconde que tout soit bien mort
sleep 1

# Nom de la session
SESSION="eurobot"
CONTAINER="my_ros_container"

# 1. On s'assure que le conteneur est bien démarré (mais il ne fait rien)
# S'il tourne déjà, cette commande ne fera rien de mal.
docker start $CONTAINER

# 2. On tue la session Tmux si elle existe déjà pour repartir à zéro
tmux kill-session -t $SESSION 2>/dev/null

# 3. On crée la session en arrière-plan
tmux new-session -d -s $SESSION

# --- FENÊTRE 1 : MICRO-ROS AGENT ---
tmux rename-window -t $SESSION:0 'Agent'
# On entre dans le conteneur pour lancer l'agent avec ta commande
tmux send-keys -t $SESSION:0 "docker exec -it $CONTAINER bash -c 'just chmod && source ~/ros2_ws/install/setup.bash && source /home/ros/ros2_ws/install/setup.bash && just lura'" C-m

# --- FENÊTRE 2 : MATCH (BRINGUP) ---
tmux new-window -t $SESSION:1 -n 'Match'
# On prépare le split d'écran AVANT de lancer les commandes
tmux split-window -v -t $SESSION:1

# Panneau du haut : Lancement du Bringup
tmux send-keys -t $SESSION:1.0 "docker exec -it $CONTAINER  bash -c 'source ~/ros2_ws/install/setup.bash && source /home/ros/ros2_ws/install/setup.bash && ros2 launch eirbot_bringup rasp.launch.py'" C-m

# Panneau du bas : Monitoring des switches (Tirette)
tmux send-keys -t $SESSION:1.1 "docker exec -it $CONTAINER bash -c 'source ~/ros2_ws/install/setup.bash && source /home/ros/ros2_ws/install/setup.bash && ros2 topic echo /hardware/switches'" C-m

# --- FINALISATION ---
# On affiche la fenêtre de Match par défaut
tmux select-window -t $SESSION:1
tmux attach-session -t $SESSION