import json
import re
import copy
import os

def simplificar_road_id(road_id):
    m = re.match(r"road_(\d+)_(\d+)_\d+", road_id)
    if m:
        return f"{m.group(1)}_{m.group(2)}"
    m = re.match(r"road_(\d+)_(\d+)", road_id)
    if m:
        return f"{m.group(1)}_{m.group(2)}"
    return None

def transformar_road_id_old(rid, road_id):
    if road_id == "1_2":
        if rid in {"0_1", "2_0"}:
            return None
        if rid in {"2_3", "3_2"}:
            return "2_2"
        if rid in {"2_1", "3_1", "0_1",""}:
            return "1_1"
    if road_id == "2_2":
        if rid in {"0_1", "1_0"}:
            return None
        if rid in {"1_3", "3_1"}:
            return "2_1"
        if rid in {"1_2", "2_3", "3_2"}:
            return "1_2"
    if road_id == "1_1":
        if rid in {"0_1", "1_0"}:
            return None
        if rid in {"1_2", "2_1"}:
            return "1_2"
        if rid in {"2_3", "3_2"}:
            return "2_2"
    if road_id == "2_1":
        if rid in {"0_1", "1_0"}:
            return None
        if rid in {"1_2", "2_2"}:
            return "1_1"
        if rid in {"1_3", "3_1"}:
            return "2_2"
    return rid

def filtrar_intersecoes(input_path, output_path, ids_intersecoes, id_principal):
    with open(input_path, "r") as f:
        data = json.load(f)

    ids_validos = set(ids_intersecoes)
    ids_validos.add(id_principal)

    intersections = []
    for inter in data["intersections"]:
        if inter["id"] in ids_validos:
            nova = dict(inter)
            if inter["id"] != id_principal:
                nova["roadLinks"] = []
                nova["trafficLight"] = {
                    "roadLinkIndices": [],
                    "lightphases": [
                        {"time": 30, "availableRoadLinks": []},
                        {"time": 5, "availableRoadLinks": []},
                        {"time": 30, "availableRoadLinks": []},
                        {"time": 5, "availableRoadLinks": []},
                        {"time": 30, "availableRoadLinks": []},
                        {"time": 5, "availableRoadLinks": []},
                        {"time": 30, "availableRoadLinks": []},
                        {"time": 5, "availableRoadLinks": []}
                    ]
                }
                nova["virtual"] = True
            intersections.append(nova)

    roads_filtradas = []
    for r in data["roads"]:
        if r["startIntersection"] in ids_validos and r["endIntersection"] in ids_validos:
            roads_filtradas.append(r)

    roads_transformadas = []
    road_ids_validos = set()
    for r in roads_filtradas:
        rid = simplificar_road_id(r["id"])
        rid_transformado = transformar_road_id_old(rid,road_id=r["id"])
        if rid_transformado:
            r_novo = dict(r)
            roads_transformadas.append(r_novo)
            road_ids_validos.add(r["id"])

    for inter in intersections:
        if "roads" in inter:
            inter["roads"] = [rid for rid in inter["roads"] if rid in road_ids_validos]

    novo_json = {
        "intersections": intersections,
        "roads": roads_transformadas
    }

    with open(output_path, "w") as f:
        json.dump(novo_json, f, indent=2)

    return road_ids_validos

def filtrar_flow_apenas_roads_principais(flow_path, roadnet_path, id_principal, output_path):
    with open(roadnet_path, "r") as f:
        roadnet = json.load(f)
    roads_principais = set()
    for inter in roadnet["intersections"]:
        if inter["id"] == id_principal:
            roads_principais = set(inter.get("roads", []))
            break

    with open(flow_path, "r") as f:
        flows = json.load(f)

    flows_filtrados = []
    for v in flows:
        nova_route = [r for r in v["route"] if r in roads_principais]
        if nova_route:
            v_novo = copy.deepcopy(v)
            v_novo["route"] = nova_route
            flows_filtrados.append(v_novo)

    with open(output_path, "w") as f:
        json.dump(flows_filtrados, f, indent=2)

def criar_config_file(nome_saida, output_dir="."):
    config = {
        "interval": 1.0,
        "seed": 0,
        "dir": "",
        "roadnetFile": f"roadnet_{nome_saida}.json",
        "flowFile": f"flow_{nome_saida}.json",
        "rlTrafficLight": True,
        "laneChange": False,
        "saveReplay": True,
        "roadnetLogFile": os.path.join(output_dir, f"replay_roadnet_{nome_saida}.json"),
        "replayLogFile": os.path.join(output_dir, f"replay_{nome_saida}.txt")
    }
    config_path = os.path.join(output_dir, f"config_{nome_saida}.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

def gerar_subconjunto_cityflow(
    ids_intersecoes, id_principal,
    roadnet_original, flow_original, nome_saida,
    output_dir="."
):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    roadnet_saida = os.path.join(output_dir, f"roadnet_{nome_saida}.json")
    flow_saida = os.path.join(output_dir, f"flow_{nome_saida}.json")
    filtrar_intersecoes(
        roadnet_original, roadnet_saida, ids_intersecoes, id_principal
    )
    filtrar_flow_apenas_roads_principais(
        flow_original, roadnet_saida, id_principal, flow_saida
    )
    criar_config_file(nome_saida, output_dir)
