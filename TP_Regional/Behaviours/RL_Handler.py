from spade.behaviour import CyclicBehaviour
from spade.message import Message
import jsonpickle

class RLDecisionBehaviour(CyclicBehaviour):
    async def on_start(self):
        print(f" Controlador {self.agent.jid}: Aguardando mensagens do ambiente...")
    async def run(self):
        msg = await self.receive(timeout=200)
        if msg and msg.get_metadata("performative") == "obs":
            obs = jsonpickle.decode(msg.body)
            sender_jid = str(msg.sender)

            action, _ = self.agent.model.predict(obs, deterministic=True)
            resposta = Message(to=sender_jid)
            resposta.set_metadata("performative", "action")
            resposta.body = jsonpickle.encode(action)
            await self.send(resposta)

class RLController(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=10)  # Aguarda por 10 segundos
        if msg:
            if msg.metadata and msg.metadata.get("performative") == "ambiente_ready":
            #  print(f"Mensagem recebida do ambiente: {msg.body}")
                # Envia confirmação de volta ao ambiente
                resposta = Message(to=str(msg.sender))
                resposta.set_metadata("performative", "controlador_ready")
                resposta.body = "RL conectado ao ambiente com sucesso."
                await self.send(resposta)
                print(f"Controlador {self.agent.jid}: Mensagem de confirmação enviada ao ambiente.")
                self.kill()
        else:
            print(f"Controlador {self.agent.jid}: Nenhuma mensagem recebida dentro do tempo limite.")
            