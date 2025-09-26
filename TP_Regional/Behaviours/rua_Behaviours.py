import json
import jsonpickle
from spade.behaviour import CyclicBehaviour
from spade.message import Message


class ReceberPedidoFicheiros(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg and msg.get_metadata("performative") == "ambiente_ready":
                print(f"Gestor_da_Rua_Agent {self.agent.jid}: Ambiente pronto, enviando ficheiros...")
                resposta = Message(to=str(msg.sender))
                resposta.set_metadata("performative", "envio_ficheiros")
                # Serializa os ficheiros usando jsonpickle
                ficheiros = {
                    "config_json": self.agent.config_json,
                    "flow_json": self.agent.flow_json,
                    "roadnet_json": self.agent.roadnet_json
                }
                resposta.body = jsonpickle.encode(ficheiros)
                await self.send(resposta)
                print(f"Gestor_da_Rua_Agent  {self.agent.jid} : Ficheiros enviados ao Ambiente.")



class ReceberEpisodioStats(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=20)
        if msg and msg.get_metadata("performative") == "episodio_stats":
            episodio_stats = jsonpickle.decode(msg.body)
            #print(f"Gestor_da_Rua_Agent {self.agent.jid}: Recebeu episodio_stats: {episodio_stats.to_dict()}")

                    # Enviar para o agente regional
            regional_jid = str(self.agent.gestor_regional_jid)
            
            resposta = Message(to=regional_jid)
            resposta.set_metadata("performative", "episodio_stats")
            # Inclui o jid do gestor de rua no corpo da mensagem para identificação
            payload = {
                "from_jid": str(self.agent.jid),
                "episodio_stats": episodio_stats
            }

            resposta.body = jsonpickle.encode(payload)
            await self.send(resposta)
