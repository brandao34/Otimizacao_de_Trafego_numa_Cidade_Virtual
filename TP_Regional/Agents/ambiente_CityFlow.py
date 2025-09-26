from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
import jsonpickle
from spade.behaviour import CyclicBehaviour
import asyncio
from Behaviours.cityflow import InformarPronto, ReceberFicheiros, RLInteractionBehaviour, FixedControllerBehaviour
import os
import shutil

#from Classes.classes import Cordenadas
#from Behaviours.client_request import Client_Request
#from Behaviours.client_handle_arrival import Client_Handle_Arrival
import json 
import gym
from gym import spaces
import cityflow
import numpy as np

class Ambiente_CityFlow_Agent(Agent): 

    def __init__(self, jid,password, max_steps: int , fazer_simulacao_base: bool, sim_id: str ): 
        super().__init__(jid, password)
        self.rl_connected = False
        self.max_steps = max_steps
        self.ficheiros = None
        self.env = None
        self.env_base = None
        self.fazer_simulacao_base = fazer_simulacao_base
        self.sim_id = sim_id


    async def setup (self): 
        print(f"Ambiente_CityFlow_Agent {self.jid}: Running\n")
        self.add_behaviour(InformarPronto())
       # self.add_behaviour(ReceberFicheiros())




    def mostrar_ficheiros(self):
        print(f"Ambiente_CityFlow_Agent {self.jid}:  Ficheiros atuais no agente:", self.ficheiros)



    def inicializar_ambiente(self):
        sim_id = self.sim_id
        if self.ficheiros and "config_json" in self.ficheiros:
            base_dir = "./Auxiliar/tmp_cityflow/" 
            os.makedirs(base_dir, exist_ok=True)
            config_path = os.path.join(base_dir, "config.json")
            roadnet_path = os.path.join(base_dir, "roadnet.json")
            flow_path = os.path.join(base_dir, "flow.json")
        
            # Salvar arquivos como JSON
            with open(config_path, "w") as f:
                json.dump(self.ficheiros["config_json"], f)
            with open(roadnet_path, "w") as f:
                json.dump(self.ficheiros["roadnet_json"], f)
            with open(flow_path, "w") as f:
                json.dump(self.ficheiros["flow_json"], f)
        
            with open(config_path, "r") as f:
                cfg = json.load(f)
            cfg["roadnetFile"] = roadnet_path
            cfg["flowFile"] = flow_path

            # Sempre cria ambiente RL
            replay_dir_rl = "./Auxiliar/replays/rl"
            os.makedirs(replay_dir_rl, exist_ok=True)
            cfg_rl = cfg.copy()
            cfg_rl["saveReplay"] = True
          #  cfg_rl["replayLogFile"] = os.path.join(replay_dir_rl, f"replay_{sim_id}.txt")
            config_path_rl = os.path.join(base_dir, f"config_rl_{sim_id}.json")
            with open(config_path_rl, "w") as f:
                json.dump(cfg_rl, f)

            self.env = CityFlowEnv(config_path_rl, self.max_steps, min_phase_time=15)
            print(f"Ambiente_CityFlow_Agent {self.jid}:  Simulação CityFlow RL começou! ID: {sim_id}")

            # Copiar roadnet para a pasta de replays RL
            shutil.copy(roadnet_path, os.path.join(replay_dir_rl, f"replay_roadnet_{sim_id}.json"))

            # Se for simulação base, cria também ambiente base
            if self.fazer_simulacao_base:
                replay_dir_base = "./Auxiliar/replays/base"
                os.makedirs(replay_dir_base, exist_ok=True)
                cfg_base = cfg.copy()
                cfg_base["saveReplay"] = True
                #cfg_base["replayLogFile"] = os.path.join(replay_dir_base, f"replay_{sim_id}.txt")
                config_path_base = os.path.join(base_dir, f"config_base_{sim_id}.json")
                with open(config_path_base, "w") as f:
                    json.dump(cfg_base, f)

                self.env_base = CityFlowEnv(config_path_base, self.max_steps, min_phase_time=15)
                print(f"Ambiente_CityFlow_Agent {self.jid}:  Simulação CityFlow BASE começou! ID: {sim_id}")

                # Copiar roadnet para a pasta de replays BASE
                shutil.copy(roadnet_path, os.path.join(replay_dir_base, f"replay_roadnet_{sim_id}.json"))




class CityFlowEnv(gym.Env):
    metadata = {"render.modes": ["human"]}

    def __init__(self, config_path: str, max_steps: int = 1000, penalty_weight: float = 5.0, min_phase_time: int = 15):
        super(CityFlowEnv, self).__init__()
        with open(config_path, 'r') as f:
            cfg = json.load(f)
        self.engine = cityflow.Engine(config_path, thread_num=1)
        self.max_steps = max_steps
        self.step_count = 0
        self.penalty_weight = penalty_weight
        self.min_phase_time = min_phase_time
        self.phase_durations = {}

        roadnet_file = cfg.get('roadnetFile')
        with open(roadnet_file, 'r') as f:
            roadnet_data = json.load(f)

        self.inter_ids = [inter['id'] for inter in roadnet_data['intersections']]
        self.intersection_lanes = [
            lane for inter in roadnet_data['intersections']
            if isinstance(inter.get('virtual', []), list)
            for lane in inter['virtual']
        ]
        self.phases = [len(inter['trafficLight']['lightphases']) for inter in roadnet_data['intersections']]
        self.action_space = spaces.MultiDiscrete(self.phases)

        self.roads = list({road for inter in roadnet_data['intersections'] for road in inter['roads']})
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(len(self.roads),), dtype=np.float32)

        
        self.max_steps = max_steps
        self.step_count = 0
        self.penalty_weight = penalty_weight

        self.total_wait_time = 0
        self.total_reward = 0

    def reset(self):
        self.engine.reset()
        self.step_count = 0
        self.phase_durations = {inter_id: 0 for inter_id in self.inter_ids}
        return self._get_obs()

    def _get_obs(self):
        lane_wait = self.engine.get_lane_waiting_vehicle_count()
        road_wait = {rid: 0 for rid in self.roads}
        for lane_id, count in lane_wait.items():
            road_id = lane_id.rsplit('_', 1)[0]
            road_wait[road_id] += count
        return np.array([road_wait[rid] for rid in self.roads], dtype=np.float32)

    def step(self, action):
        for idx, phase in enumerate(action):
            inter_id = self.inter_ids[idx]
            if self.phase_durations.get(inter_id, 0) >= self.min_phase_time:
                self.engine.set_tl_phase(inter_id, int(phase))
                self.phase_durations[inter_id] = 0
            else:
                self.phase_durations[inter_id] += 1

        self.engine.next_step()
        self.step_count += 1

        obs = self._get_obs()
        total_wait = np.sum(obs)

        vehicle_speeds = self.engine.get_vehicle_speed()
        vehicles_stopped_in_intersections = sum(
            1 for lane in self.intersection_lanes 
            for veh in self.engine.get_lane_vehicles()[lane]
            if vehicle_speeds.get(veh, 1) < 0.1
        )

        reward = -total_wait - (self.penalty_weight * vehicles_stopped_in_intersections) /100.00

        done = self.step_count >= self.max_steps
        print(f"Step: {self.step_count}, Reward: {reward}, Done: {done}")
        return obs, reward, done, {}



    def get_stats(self):
        # Coleta as estatísticas atuais do ambiente CityFlow
        waits = self.engine.get_lane_waiting_vehicle_count()
        t = self.engine.get_current_time()
        vc = self.engine.get_vehicle_count()
        speeds = self.engine.get_vehicle_speed()
        avg_speed = sum(speeds.values()) / len(speeds) if speeds else 0.0
        avg_wait = sum(waits.values()) / len(waits) if waits else 0.0

        return {
            "total_wait_time": self.total_wait_time,
            "total_reward": self.total_reward,
            "steps": self.step_count,
            "current_time": t,
            "vehicle_count": vc,
            "avg_speed": avg_speed,
            "avg_wait_per_lane": avg_wait
        }