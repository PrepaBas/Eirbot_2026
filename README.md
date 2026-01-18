# Eirbot 2026
objectif : premier

## Config Docker
Il y a deux façons de lancer le projet dans un docker.
`.devcontainer` contient :
- `Dockerfile` - sert à lancer le docker (voir la doc docker). Il faut se rattacher au workspace (le fichier versioné, souvent nommé `ros2_ws`). Example de commande pour lancer le docker : 
```bash
docker run -it --rm --name ros2_dev -v ~/<nom_du_workspace>:/home/ros/ros2_ws ros2-humble:22.04
```
- `devcontainer.json` - sert à lancer un docker intégré dans VScode. Il faut juste lancer `>Dev Container:Open Folder in Container...` comme commande Code

## Fonctionnement ROS2
Ros2 (Robot Operating System 2) permet de créer une architecture de robot et d'utiliser des outils de développemet quasi-professionels. 
Son installation est facilité par le docker. Après le clone du git, il faut 