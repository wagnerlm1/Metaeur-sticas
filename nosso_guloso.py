import numpy as np
import pandas as pd
import random

f = open('K100.1', 'r')
instancia = f.readlines()

node = [index for index, line in enumerate(instancia) if 'node' in line][0]
link = [index for index, line in enumerate(instancia) if 'link' in line][0]

vertices = instancia[node+1:link]
arestas = instancia[link+1:-1]

vertices = [vert.split() for vert in vertices]
arestas = [ares.split() for ares in arestas]

vertices = pd.DataFrame(vertices, columns=vertices[0])
vertices = vertices.drop(index=0)

arestas = pd.DataFrame(arestas, columns=arestas[0])
arestas = arestas.drop(index=0)

arestas = arestas[['x', 'y', 'length']]
vertices = vertices[['#name', 'weight']]

arestas = arestas.astype(float)
vertices = vertices.astype(float)

arestas.reset_index(inplace=True, drop=True)
vertices.reset_index(inplace=True, drop=True)

terminais = vertices.loc[vertices['weight'] != 0, '#name'].to_list()

# TODO: Dataframes copiados para não ter conflito com outros códigos
arestas_gu = arestas.copy()
vertices_gu = vertices.copy()
# arestas_gu = pd.read_excel(r'C:\Users\Wagne\Desktop\inst_toy.xlsx')
# arestas_gu['coord'] = arestas_gu['coord'].apply(lambda x: eval(x))

# TODO:Criando coluna com os vertices [x,y] das arestas
arestas_gu['coord'] = arestas_gu[['x','y']].values.tolist()
# arestas_gu = arestas_gu[['coord', 'length']]

# TODO: Copiando lista de terminais
lista_terminais = terminais.copy()
# lista_terminais = [2, 4, 7, 9]

# Lista "corrida" das arestas > exemplo: [[1,2], [3,4], [5,6]] = [1,2,3,4,5,6]
lista_arestas = pd.Series(arestas_gu['coord'].sum())

# Vertices de grau 1 = aqueles que na lista corrida só aparecem uma unica vez.
vert_grau1 = lista_arestas[~lista_arestas.duplicated(keep=False)].to_list()
# terminais de grau1
term_grau1 = [item for item in vert_grau1 if item in lista_terminais]
# Confere se algum vértice de grau1 é terminal
vert_grau1 = [item for item in vert_grau1 if item not in lista_terminais]

# listas_arestas para lista
lista_arestas = lista_arestas.to_list()

# É o index das arestas com vertices de grau 1 no dataframe arestas_gu
index_vgrau1 = [(lista_arestas.index(item)-1)/2 if item % 2 != 0 else lista_arestas.index(item)/2 for item in vert_grau1]
# Removendo as arestas com vertices de grau um do dataframe
arestas_gu.drop(index_vgrau1, inplace=True)
arestas_gu.reset_index(drop=True, inplace=True)
# Escolhendo o terminal de start
tr_start = random.choice(lista_terminais)


# função que procura os vizinho de um vertice e os que são terminais
def procura_vizinhos(links, terms, vert):

    """

    Args:
        links: dataframe com as coordenadas e pesos de cada aresta
        terms: lista de terminais
        vert: vertice para olhar os vizinhos

    Returns:
        vizinhos: LISTA de INDEX das arestas que saem de vert do dataframe links
        com_terms: LISTA de INDEX das arestas com terminais
        nome_vizinhos: LISTA com os nomes dos vértices vizinhos a vert


    """
    # Verifica se quais são os vizinhos do vertice (vert) em questão
    vizinhos = links['coord'][links['coord'].apply(lambda x: True if vert in x else False)].index.to_list()

    if vizinhos:

        # Pega o nome dos vértices vizinhos
        nome_vizinhos = set(links.loc[vizinhos]['coord'].sum())
        nome_vizinhos.remove(vert)
        nome_vizinhos = list(nome_vizinhos)
        # Verifica quais vizinhos são terminais
        com_terms = [item for item in nome_vizinhos if item in terms and item is not vert]
        # Pega os index dos vizinhos com terminais
        com_terms = links.loc[vizinhos].loc[
            links.loc[vizinhos]['coord'].apply(lambda x: len(set(x).intersection(com_terms)) != 0)].index.to_list()

    else:
        com_terms, nome_vizinhos = [], []

    return vizinhos, com_terms, nome_vizinhos


def seleciona_melhor_vertice(links, nodes, vert_state, term_grau1, rot):
    """

    Args:
        links: dataframe com as coordenadas e pesos de cada aresta
        nodes: lista com os INDEX das opções de arestas para selecionar a "melhor"
        vert_state: é o vertice em que o código está atualmente, logo antes de entrar na função

    Returns:

    """
    # Se tiver um caminho possível
    if len(nodes) == 1:

        # O caminho possível vira o vert e vai pro próximo laço
        index_vert = nodes[0]

    # Se tiver mais que um caminho possível
    if len(nodes) > 1:

        # Pegar pesos das arestas
        pesos = links.loc[nodes]

        rot = rot.copy()
        # Garante não andar em círculos excluindo os vértices que já estão na rota
        # Rot é a variável que armazena a rota
        if vert_state in rot:
            rot.remove(vert_state)
        pesos = pesos.loc[~pesos['coord'].apply(lambda x: len(set(x).intersection(set(rot))) != 0)]

        pesos_grau1 = pesos.loc[pesos['coord'].apply(lambda x: len(set(x).intersection(term_grau1))) != 0].index.to_list()

        if pesos_grau1:

            index_vert = random.choice(pesos_grau1)

        else:

            # Se não tiverem pesos duplicados
            if not any(pesos['length'].duplicated()):
                # pegar o mínimo vertice
                index_vert = pesos.loc[pesos['length'] == pesos['length'].min()].index[0]
            # Se tiver peso duplicado
            else:
                # Selecio pesos duplicados
                pesos = pesos[pesos.duplicated(keep=False)]
                # Garantindo que mesmo dentro das duplicatas eu pego a duplicata com menor peso
                pesos = pesos.loc[pesos['length'] == pesos['length'].min()]
                # Escolher aleatoriamente entre os terminais de msm peso
                index_vert = random.choice(pesos.index.to_list())

    # Pegar o vertice seguinte da melhor aresta
    vert = links.loc[index_vert]['coord'].copy()
    vert.remove(vert_state)
    vert = vert[0]

    return vert, index_vert

# Terminais de grau1
term_grau1 = term_grau1.copy()
#  Essa lista vai servir como referência para verificar se todos os terminais foram conectados
terminais_aux = lista_terminais.copy()
# Primeiro vértice do guloso
# TODO: 18, 92 ta dando problema
vert = tr_start
# Rota de grafo que o guloso vai lendo
rota = [vert]
# variavel para armazenar os index das rotas
rota_index = []
# Remover o terminal inicial da lista auxiliar da parada
terminais_aux.remove(vert)

add_vert_seguinte = False
max_iter = 500

print(rota)
arestas_gu.reset_index(drop=True, inplace=True)
arestas_original = arestas_gu.copy()

for n in range(0, max_iter):

    if vert not in rota and n != 0:
        # Adiciona vertice na rota
        rota.append(vert)
        # Adiciona na lista de index da rota
        rota_index.append(index_vert)
        # remover aresta caminhada de arestas
        arestas_gu.drop(index_vert, inplace=True)

        if add_vert_seguinte and vert_seguinte not in rota:
            # Adiciona vertice seguinte na rota
            rota.append(vert_seguinte)
            # Adiciona na lista de index da rota
            rota_index.append(index_vert_seguinte)
            # remove a rota até o vertice seguinte
            arestas_gu.drop(index_vert_seguinte, inplace=True)
            vert = vert_seguinte
            add_vert_seguinte = False

    # Critérios de parada
    # Se terminais_aux estiver vazio quer dizer que todos os terminais foram usados
    if not terminais_aux:
        print('Achou solução inicial')
        break  # TODO: SUGESTÃO COLOCAR BREAKPOINT AQUI
    # Se chegar ao número máximo de iterações e a terminais aux não estiver vazio
    if n == max_iter - 1 and terminais_aux:
        print('Não achou solução inicial')  # TODO: SUGESTÃO COLOCAR BREAKPOINT AQUI

    # Pega os vizinhos do vertice e diz quais são terminais
    vizinhos, com_terms, nome_vizinhos = procura_vizinhos(arestas_gu.copy(), terminais_aux, vert)

    # Esse isso serve para verificar se o vértice é um terminal de grau1
    if nome_vizinhos or not set(nome_vizinhos).issubset(set(rota)):

        # Se tiver terminais
        if com_terms:

            # Seleciona o melhor terminal
            vert, index_vert = seleciona_melhor_vertice(arestas_gu.copy(), com_terms, vert, term_grau1, rota)
            # Remove da lista de terminais
            terminais_aux.remove(vert)

            continue

        # Se não tem terminais nesses vizinhos
        if not com_terms:

            # Vai verificar se ter terminais conectados os vizinhos dos vizinhos de vert
            for viz in nome_vizinhos:
                viz_de_vizinhos, viz_com_term, nome_viz_de_vizinhos = procura_vizinhos(arestas_gu.copy(), terminais_aux,
                                                                                       viz)
                # O primeiro que tiver cancela o laço
                if viz_com_term:
                    sem_terms = False

                    break
                # Se não tiver continua esse laço
                if not viz_com_term:
                    sem_terms = True

                    continue

            # Se tiver terminais em algum vizinho dos vizinhos seleciona
            if not sem_terms:

                index_vert = arestas_gu['coord'].loc[arestas_gu['coord'].apply(lambda x: set([vert, viz]) == set(x))].index[0]
                # Marco o vizinho como vert
                vert = viz
                # Seleciona o melhor terminal do vizinho do vizinho
                vert_seguinte, index_vert_seguinte = seleciona_melhor_vertice(arestas_gu.copy(), viz_com_term, vert, term_grau1, rota)

                # Remove da lista com terminal
                terminais_aux.remove(vert_seguinte)
                add_vert_seguinte = True

                continue

            # Se não tiver terminais nos vizinhos dos vizinhos
            if sem_terms:

                # Seleciona o melhor vizinho para seguir
                vert, index_vert = seleciona_melhor_vertice(arestas_gu.copy(), vizinhos, vert, term_grau1, rota)

                add_vert_seguinte = False

                continue
    else:

        # Pega a ultima aresta percorrida
        caminho = arestas_original.loc[rota_index[-1], 'coord']
        # Remove o vertice de onde ela veio (anterior)
        caminho.remove(vert)
        # Pega o vertice anterior ao atual
        vert = caminho[0]
        # Vê o vizinhos anterior ao atual
        vizinhos, com_terms, nome_vizinhos = procura_vizinhos(arestas_gu.copy(), terminais_aux, vert)
        # Pega lista de vizinhos que não estão na rota
        nome_vizinhos = list(set(nome_vizinhos).difference(set(rota)))

        # Se houverem anteriores ao atual que naõ estão na rota
        if nome_vizinhos:
            # Seleciona melhor vertice
            vert, index_vert = seleciona_melhor_vertice(arestas_gu.copy(), vizinhos, vert, term_grau1, rota)

        continue

print('rota = {}'.format(rota))
print('index_rota = {}'.format(rota_index))
print('terminais = {}'.format(lista_terminais))
print('terminais não incluidos = {}'.format(terminais_aux))
print('numero de iteração = {}'.format(n))


