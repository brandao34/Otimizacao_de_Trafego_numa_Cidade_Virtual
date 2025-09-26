import json
import os
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
import jsonpickle
from Classes.rua_stats import Rua_Stats

class InformarPronto(OneShotBehaviour):
        async def run(self):
            self.sim_id = self.agent.sim_id
            print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Simulação ID: {self.sim_id}")
            rua_id = self.sim_id.split("_",1)[1]
            print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Rua ID: {rua_id}")
            gestor_jid = f"gestor_da_{rua_id}@zephyrus-g34"  
            msg = Message(to=gestor_jid)
            msg.set_metadata("performative", "ambiente_ready")
            msg.body = "Ambiente CityFlow pronto para receber ficheiros."
            await self.send(msg)
            print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Mensagem de pronto enviada ao Gestor.")
            self.agent.add_behaviour(ReceberFicheiros())

class ReceberFicheiros(CyclicBehaviour):
    async def run(self):
        print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Aguardando mensagem de ficheiros...")
        msg = await self.receive(timeout=20)
        self.sim_id = self.agent.sim_id
        rua_id = self.sim_id.split("_",1)[1]

        if msg:
            if msg.get_metadata("performative") == "envio_ficheiros":
                self.agent.ficheiros = jsonpickle.decode(msg.body)
                print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Ficheiros recebidos e guardados no agente.")

                self.agent.inicializar_ambiente()

                # AVISA O RL QUE ESTE AMBIENTE ESTÁ PRONTO
                rl_jid = f"controlador_rl_{rua_id}@zephyrus-g34"  
                msg_rl = Message(to=rl_jid)
                msg_rl.set_metadata("performative", "ambiente_ready")
                msg_rl.body = f"Ambiente {str(self.agent.jid)} pronto para interação RL."
                await self.send(msg_rl)
                print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Avisou RL que está pronto.")
                self.agent.add_behaviour(RLInteractionBehaviour())
                self.kill()
            else:
                print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Mensagem recebida, mas performative diferente.")
        else:
            print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Nenhuma mensagem recebida no timeout.")
        


class RLInteractionBehaviour(CyclicBehaviour):
    async def on_start(self):
        self.sim_id = self.agent.sim_id

        print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Aguardando controlador RL...")
        while not self.agent.rl_connected:
            msg = await self.receive(timeout=200)
            if msg and msg.get_metadata("performative") == "controlador_ready":
                self.agent.rl_connected = True
                print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Controlador RL conectado ao ambiente.")
                break
    async def run(self):
        if not hasattr(self.agent, "env"):
            return
        rua_id = self.sim_id.split("_",1)[1]

        obs = self.agent.env.reset()
        done = False
        reward_info = None
        while not done:
            controlador_jid = f"controlador_rl_{rua_id}@zephyrus-g34"  
            msg = Message(to=controlador_jid)
            msg.set_metadata("performative", "obs")
            msg.body = jsonpickle.encode(obs)
            await self.send(msg)

            resposta = await self.receive(timeout=2)
            if resposta and resposta.get_metadata("performative") == "action":
                action = jsonpickle.decode(resposta.body)
                obs, reward, done, info = self.agent.env.step(action)
                reward_info = reward
            else:
                print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Não recebeu ação do controlador RL.")
                break

        print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Episódio finalizado.")
        # Salvar stats RL
        stats = self.agent.env.get_stats()
        sim_id = self.agent.sim_id
         
        
        episodio_stats = Rua_Stats(
        total_wait_time=stats['total_wait_time'],
        total_reward=stats['total_reward'],
        steps=stats['steps'],
        current_time=stats['current_time'],
        vehicle_count=stats['vehicle_count'],
        avg_speed=stats['avg_speed'],
        avg_wait_per_lane=stats['avg_wait_per_lane'],
        reward = reward_info
        )

        stats_path = f"./Auxiliar/replays/rl/stats_{sim_id}.json"
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=4)
        # Salvar stats RL em formato RuaStats


            self.sim_id = self.agent.sim_id
            rua_id = self.sim_id.split("_",1)[1]
            gestor_jid = f"gestor_da_{rua_id}@zephyrus-g34" 
            msg = Message(to=gestor_jid)
            msg.set_metadata("performative", "episodio_stats")
            msg.body = jsonpickle.encode(episodio_stats)
            await self.send(msg)






        print(f"    STATS : Ambiente_CityFlow_Agent {self.agent.jid}: Stat {stats}.")
        if self.agent.fazer_simulacao_base:
            print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Simulação base ativada.")
            self.agent.add_behaviour(FixedControllerBehaviour())
        self.kill() 


class FixedControllerBehaviour(CyclicBehaviour):
    async def run(self):
        if not hasattr(self.agent, "env_base"):
            return
        obs = self.agent.env_base.reset()
        done = False
        # Gera ação fixa para todas as interseções
        action = [0] * len(self.agent.env_base.inter_ids)
        while not done:
            obs, reward, done, info = self.agent.env_base.step(action)
        print(f"Ambiente_CityFlow_Agent {self.agent.jid}: Episódio finalizado (controle fixo).")
        # Salvar stats BASE
        stats = self.agent.env_base.get_stats()
        sim_id = self.agent.sim_id
        stats_path = f"./Auxiliar/replays/base/stats_{sim_id}.json"
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=4)
        self.kill()
