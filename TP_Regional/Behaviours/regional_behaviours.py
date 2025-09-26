from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
import os
import json
from Agents.gestor_da_Rua import Gestor_de_Rua_Agent
from Agents.ambiente_CityFlow import Ambiente_CityFlow_Agent
from Agents.controlador_RL import Controlador_RL_Agent

XMPP_SERVER = 'zephyrus-g34'
PASSWORD = 'NOPASSWORD'
MAX_STEPS = 1000


class CriarGestoresRuasBehaviour(OneShotBehaviour):
    def __init__(self, output_folder):
        super().__init__()
        self.output_folder = output_folder

    async def run(self):
        arquivos = os.listdir(self.output_folder)
        ruas_ids = set()
        for nome in arquivos:
            if nome.startswith("config_") and nome.endswith(".json"):
                rua_id = nome.replace("config_", "").replace(".json", "")
                ruas_ids.add(rua_id)

        gestores_rua = []
        ambientes_cityflow = []
        controladores_rl = []

        for rua_id in ruas_ids:
            try:
                with open(os.path.join(self.output_folder, f"config_{rua_id}.json")) as f:
                    config_json = json.load(f)
                with open(os.path.join(self.output_folder, f"flow_{rua_id}.json")) as f:
                    flow_json = json.load(f)
                with open(os.path.join(self.output_folder, f"roadnet_{rua_id}.json")) as f:
                    roadnet_json = json.load(f)
            except Exception as e:
                print(f"Erro ao carregar arquivos da rua {rua_id}: {e}")
                continue

            gestor_rua_jid = f"gestor_da_{rua_id}@{XMPP_SERVER}"
            gestor_rua_agent = Gestor_de_Rua_Agent(
                gestor_rua_jid,
                PASSWORD,
                config_json,
                flow_json,
                roadnet_json,
                gestor_regional_jid=self.agent.jid
            )
            gestores_rua.append(gestor_rua_agent)

            ambiente_cityflow_jid = f"ambient_cityflow_{rua_id}@{XMPP_SERVER}"
            ambiente_cityflow_agent = Ambiente_CityFlow_Agent(
                ambiente_cityflow_jid,
                PASSWORD,
                MAX_STEPS,
                fazer_simulacao_base=True,
                sim_id=f"sim_{rua_id}"
            )
            ambientes_cityflow.append(ambiente_cityflow_agent)

            rl_jid = f'controlador_rl_{rua_id}@{XMPP_SERVER}'
            rl_agent = Controlador_RL_Agent(
                rl_jid,
                PASSWORD,
                "./Modelos/ppo_cityflow_1.zip",
                MAX_STEPS,
                device="cpu",
            )
            controladores_rl.append(rl_agent)

        for controlador in controladores_rl:
            await controlador.start()
        for gestor in gestores_rua:
            await gestor.start()
        for ambiente in ambientes_cityflow:
            await ambiente.start()
        print(f"Todos os agentes de Ruas iniciados com sucesso.")
        self.agent.gestores_rua = gestores_rua
        self.agent.ambientes_cityflow = ambientes_cityflow
        self.agent.controladores_rl = controladores_rl


class ReceberEpisodiosRegionais(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=20)
        if msg and msg.get_metadata("performative") == "episodio_stats":
            payload = json.loads(msg.body)
            from_jid = payload["from_jid"]
            episodio_stats = payload["episodio_stats"]
            if not hasattr(self.agent, "episodios_por_gestor"):
                self.agent.episodios_por_gestor = {}
            self.agent.episodios_por_gestor[from_jid] = episodio_stats