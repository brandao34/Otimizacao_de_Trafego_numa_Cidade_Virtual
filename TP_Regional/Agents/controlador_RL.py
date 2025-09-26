from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from stable_baselines3 import PPO
import numpy as np
from Behaviours.RL_Handler import RLDecisionBehaviour, RLController

class Controlador_RL_Agent(Agent):
    def __init__(self, jid, password, model_path, maxsetps : int ,device="cpu"):
        super().__init__(jid, password)
        self.model = PPO.load(model_path, device=device)
        self.max_steps = maxsetps

    async def setup(self):
        print(f"Controlador_RL_Agent {self.jid} Running\n")
        self.add_behaviour(RLController())
        if self.model:
            print(f"Controlador {self.jid}: Modelo carregado com sucesso.")
        self.add_behaviour(RLDecisionBehaviour())



