from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
import json
from Behaviours.rua_Behaviours import ReceberPedidoFicheiros, ReceberEpisodioStats
import jsonpickle



class Gestor_de_Rua_Agent(Agent): 


    def __init__(self, jid,password ,  config_json : json, flow_json : json, roadnet_json : json, gestor_regional_jid : str): 
        super().__init__(jid, password)
        self.config_json = config_json
        self.flow_json = flow_json
        self.roadnet_json = roadnet_json
        self.gestor_regional_jid = gestor_regional_jid

    async def setup(self,): 
        print(f"Gestor_da_Rua_Agent {self.jid}: Running\n")
        if self.config_json and self.flow_json and self.roadnet_json:
            print(f"Gestor_da_Rua_Agent {self.jid}: Configurações carregadas com sucesso.")
        else:
            print(f"Gestor_da_Rua_Agent {self.jid}: Erro ao carregar configurações.")
        #self.add_behaviour(self.ConfirmacaoLigacao())
        self.add_behaviour(ReceberPedidoFicheiros())
        self.add_behaviour(ReceberEpisodioStats())


    class ConfirmacaoLigacao(OneShotBehaviour):
        async def run(self):
            # 1. Envia confirmação de ligação ao Ambiente
            msg = Message(to="ambient_cityflow@zephyrus-g34")
            msg.body = "Gestor: Confirma ligação"
            await self.send(msg)
            # 2. Espera resposta do Ambiente
            resposta = await self.receive(timeout=10)
            if resposta and "Ambiente: Ambos conectados" in resposta.body:
                # 3. Informa o Controlador RL
                msg_rl = Message(to="controlador_rl@zephyrus-g34")
                msg_rl.body = "Gestor: Estou ligado"
                await self.send(msg_rl)
                # 4. Espera confirmação do RL
                resposta_rl = await self.receive(timeout=10)
                if resposta_rl and "Controlador: Estou ligado" in resposta_rl.body:
                    # 5. Informa o Ambiente que todos estão conectados
                    msg_final = Message(to="ambient_cityflow@zephyrus-g34")
                    msg_final.body = "Todos conectados"
                    await self.send(msg_final)

