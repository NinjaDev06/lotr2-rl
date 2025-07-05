# lotr2-rl
RL implementation for the Ms-Dos game Lord of the Realm 2

# Work in progress
This project is in initial phase as the goal is to be able to train an RL AI agent to play LOTR2 from a linux server.
When this goal will be achieved, the project will be refactor to present a clean state because going to phase 2 that is training a good AI agent.

# Usefull Commands

```
# launch http server to serve ROMS localy
python -m http.server 8080

# launch manual mode
python main.py --game lotr2 --emulator gym --render-mode human --action-mode manual
# launch random bot mode 
python main.py --game lotr2 --emulator gym --render-mode human

# launch custom training with stable-baselines3
python main.py --game lotr2 --emulator gym --action-mode train
# launch custom training with stable-baselines3 with visual
python main.py --game lotr2 --emulator gym --action-mode train --render-mode human

# launch training with RL-ZOO3
python -m rl_zoo3.train --algo ppo --env lotr2-rl/LordsOfTheRealm2-v0 --conf configs/lotr2.yaml --gym-packages lotr2_rl -n 500000 --save-freq 100000
```