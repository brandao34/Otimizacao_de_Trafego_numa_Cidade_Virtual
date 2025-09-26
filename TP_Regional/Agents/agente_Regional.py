from spade.agent import Agent
import os
import json
from Behaviours.regional_behaviours import CriarGestoresRuasBehaviour, ReceberEpisodiosRegionais
from Scripts.dive_and_conquer import gerar_subconjunto_cityflow

class Gestor_Regional_Agent(Agent):
    def __init__(self, jid, password, regiao_folder):
        super().__init__(jid, password)
        self.regiao_folder = regiao_folder  # Pasta com os ficheiros originais de flow e roadnet
        self.output_folder = f"Agents/{jid}"
        self.episodios_por_gestor = {}

    async def setup(self):
        print(f"Gestor Regional Agent {self.jid}: Running\n")

        # Verifica se as pastas existem
        if not os.path.exists(self.regiao_folder):
            print(f"Erro: Pasta da região '{self.regiao_folder}' não encontrada.")
            return
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            print(f"Pasta de saída '{self.output_folder}' criada.")

        # Gera os cruzamentos automaticamente
        self.gerar_cruzamentos()

        # Adiciona os behaviours
        self.add_behaviour(CriarGestoresRuasBehaviour(self.output_folder))
        self.add_behaviour(ReceberEpisodiosRegionais())

    def gerar_cruzamentos(self):
        # Define os cruzamentos e os ficheiros originais
        cruzamentos = [
            (["intersection_0_2", "intersection_1_3", "intersection_1_2", "intersection_2_2", "intersection_1_1"], "intersection_1_2", "cruzamento_1_2"),
            (["intersection_2_3", "intersection_1_2", "intersection_2_2", "intersection_2_1", "intersection_3_2"], "intersection_2_2", "cruzamento_2_2"),
            (["intersection_0_1", "intersection_1_2", "intersection_1_1", "intersection_1_0", "intersection_2_1"], "intersection_1_1", "cruzamento_1_1"),
            (["intersection_1_1", "intersection_2_2", "intersection_2_1", "intersection_2_0", "intersection_3_1"], "intersection_2_1", "cruzamento_2_1")
        ]
        roadnet_original = os.path.join(self.regiao_folder, "regiao1_roadnet_2_2.json")
        flow_original = os.path.join(self.regiao_folder, "regiao1_flow_2_2.json")

        # Gera os ficheiros para cada cruzamento
        for ids_intersecoes, id_principal, nome_saida in cruzamentos:
            gerar_subconjunto_cityflow(
                ids_intersecoes,
                id_principal,
                roadnet_original,
                flow_original,
                nome_saida, 
                self.output_folder
            )
        print(f"Gestor Regional Agent {self.jid}: Todos os cruzamentos foram gerados com sucesso.")

