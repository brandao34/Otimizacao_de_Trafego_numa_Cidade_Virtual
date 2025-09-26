import spade
from spade import wait_until_finished
import random
import asyncio

from Agents.controlador_RL import Controlador_RL_Agent
from Agents.agente_Regional import Gestor_Regional_Agent
#from Classes.classes import Cordenadas


XMPP_SERVER = 'zephyrus-g34'
PASSWORD = 'NOPASSWORD'

MAX_STEPS = 10

import asyncio


def gestor_regional_loader(Regiao_id): 
        base_path = f"Regiao/{Regiao_id}"
        with open(f"Regiao/{Regiao_id}_config.json") as f:
            config_json = f.read()
        with open(f"Regiao/{Regiao_id}_flow_2_2.json") as f:
            flow_json = f.read()
        with open(f"Regiao/{Regiao_id}_roadnet_2_2.json") as f:
            roadnet_json = f.read()

        gestor_regional_config = {
            "gestor_regional_id": Regiao_id,
            "config_json": config_json,
            "flow_json": flow_json,
            "roadnet_json": roadnet_json
        }
        return gestor_regional_config


async def main():

    regiaos = ["regiao1"]  
    gestores_regional = []

    for regiao_id in regiaos:
        gestor_regional_config = gestor_regional_loader(regiao_id)
        gestor_regional_jid = f'gestor_da_{regiao_id}@{XMPP_SERVER}'
        gestor_regional_agent = Gestor_Regional_Agent(
            gestor_regional_jid,
            PASSWORD,
     "Regiao"
        )
        gestores_regional.append(gestor_regional_agent)
        # Inicia o agente gestor Da regiao 
        await gestor_regional_agent.start()


    


     

    # Cria o agente RL (pode ser um para todas as ruas ou um por rua, conforme sua arquitetura)


    #for gestor_regional_agent in gestores_regional:
        # Aguarda o agente gestor da rua estar pronto
        #await gestor_regional_agent.start()


  



    await asyncio.sleep(2)

    await wait_until_finished(gestores_regional)

    for gestor_regional_agent in gestores_regional:
        # Para gestores de rua e ambientes cityflow, se existirem
        if hasattr(gestor_regional_agent, "gestores_rua"):
            for gestor_rua in gestor_regional_agent.gestores_rua:
                await gestor_rua.stop()
        if hasattr(gestor_regional_agent, "ambientes_cityflow"):
            for ambiente in gestor_regional_agent.ambientes_cityflow:
                await ambiente.stop()
        if hasattr(gestor_regional_agent, "controladores_rl"):
            for controlador in gestor_regional_agent.controladores_rl:
                await controlador.stop()

    
    


if __name__ == "__main__":
    spade.run(main())

