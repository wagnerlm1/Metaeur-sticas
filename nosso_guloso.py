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

# Dataframes copiados para não ter conflito com outros códigos
arestas_gu = arestas.copy()
vertices_gu = vertices.copy()

# Criando coluna com os vertices [x,y] das arestas
arestas_gu['coord'] = arestas_gu[['x','y']].values.tolist()
arestas_gu = arestas_gu[['coord', 'length']]

# Copiando lista de terminais
lista_terminais = terminais.copy()

# Lista "corrida" das arestas > exemplo: [[1,2], [3,4], [5,6]] = [1,2,3,4,5,6]
lista_arestas = pd.Series(arestas_gu['coord'].sum())

# Vertices de grau 1 = aqueles que na lista corrida só aparecem uma unica vez.
vert_grau1 = lista_arestas[~lista_arestas.duplicated(keep=False)].to_list()

# listas_arestas para lista
lista_arestas = lista_arestas.to_list()

# É o index das arestas com vertices de grau 1 no dataframe arestas_gu
index_vgrau1 = [(lista_arestas.index(item)-1)/2 if item % 2 != 0 else lista_arestas.index(item)/2 for item in vert_grau1]
# Verifica se os vertices não são terminais
index_vgrau1 = [item for item in index_vgrau1 if item not in [lista_terminais]]
# Removendo as arestas com vertices de grau um do dataframe
arestas_gu.drop(index_vgrau1, inplace=True)

# Escolhendo o terminal de start
tr_start = random.choice(lista_terminais)


# função que procura os vizinho de um vertice e os que são terminais
def procura_vizinhos(links, terms, vert):

    """

    Args:
        links: dataframe com as coordenadas
        terms: lista de
        vert:

    Returns:

    """
    # Verifica se quais são os vizinhos do vertice (vert) em questão
    vizinhos = links['coord'][links['coord'].apply(lambda x: True if vert in x else False)].index.to_list()

    # Pega o nome dos vértices vizinhos
    nome_vizinhos = set(links.loc[vizinhos]['coord'].sum())
    nome_vizinhos.remove(vert)
    nome_vizinhos = list(nome_vizinhos)
    # Verifica quais vizinhos são terminais
    com_terms = [item for item in nome_vizinhos if item in terms and item is not vert]
    # Pega os index dos vizinhos com terminais
    com_terms = links.loc[vizinhos][
        links.loc[vizinhos]['coord'].apply(lambda x: len(set(x).intersection(com_terms)) != 0)].index.to_list()

    return vizinhos, com_terms, nome_vizinhos


def seleciona_melhor_vertice(links, nodes, vert_state):
    # Se tiver um terminal
    if len(nodes) == 1:
        # O terminal vira o vert e vai pro próximo laço
        index_vert = nodes[0]

    # Se tiver mais que um terminal
    if len(nodes) > 1:
        # Pegar pesos das arestas
        pesos = links.loc[nodes][['length']]
        # Se não tiverem pesos duplicados
        if not any(pesos.duplicated()):
            # pegar o mínimo vertice
            index_vert = pesos.loc[pesos['length'] == pesos['length'].min()].index[0]
        # Se tiver peso duplicado
        else:
            # Selecio pesos duplicados
            pesos = pesos[pesos.duplicated(keep=False)]
            # Garantindo que mesmo dentro das duplicatas eu pego a duplicata com menor peso
            pesos = pesos.loc[pesos['length'] == pesos['length'].min()]
            # Escolher aleatoriamente entre os terminais de msm peso
            index_vert = random.choice(pesos.index.to_list())[0]

    # Pegar o vertice seguinte da melhor aresta
    vert = links.loc[index_vert]['coord'].copy()
    vert.remove(vert_state)
    vert = vert[0]

    return vert

#  Essa lista vai servir como referência para verificar se todos os terminais foram conectados
terminais_aux = lista_terminais.copy()
# Primeiro vértice do guloso
vert = 47
# Rota de grafo que o guloso vai lendo
rota = [vert]

vert_seguinte = None
max_iter = 1000

print(rota)

for n in range(0, max_iter):

    # Critérios de parada
    # Se terminais_aux estiver vazio quer dizer que todos os terminais foram usados
    if not terminais_aux:
        break # TODO: SUGESTÃO COLOCAR BREAKPOINT AQUI
    # Se chegar ao número máximo de iterações e a terminais aux não estiver vazio
    if n == max_iter-1 and terminais_aux:
        print('Não achou solução inicial') # TODO: SUGESTÃO COLOCAR BREAKPOINT AQUI

    # Exclui as arestas já caminhadas
    if len(rota) >= 2:
        index_drop = arestas_gu.loc[arestas_gu['coord'].apply(lambda x: set(x) == set(rota[-2:]))].index
        arestas_gu.drop(index_drop, inplace=True)

    # Se vert não estiver em rota ou ser o primeiro loop
    if vert not in rota or len(rota) == 1:

        if n != 0:
            # Adiciona vertice na rota
            rota.append(vert)
            if vert_seguinte:
                if vert_seguinte not in rota:
                    rota.append(vert_seguinte)
                    vert = vert_seguinte

        # Pega os vizinhos do vertice e diz quais são terminais
        vizinhos, com_terms, nome_vizinhos = procura_vizinhos(arestas_gu.copy(), terminais_aux, vert)

        # Esse isso serve para verificar se o vértice é um terminal de grau1
        if len(nome_vizinhos) != 1 and vert in rota:
            # Se tiver terminal ele não vai ser de grau1
            terminal_grau1 = False

            # Se tiver terminais
            if com_terms:
                # Seleciona o melhor terminal
                vert = seleciona_melhor_vertice(arestas_gu.copy(), com_terms, vert)
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
                    # Marco o vizinho como vert
                    vert = viz
                    # Seleciona o melhor terminal do vizinho do vizinho
                    vert_seguinte = seleciona_melhor_vertice(arestas_gu.copy(), viz_com_term, vert)
                    # Remove da lista com terminal
                    terminais_aux.remove(vert_seguinte)
                    continue

                # Se não tiver terminais nos vizinhos dos vizinhos
                if sem_terms:
                    # Seleciona o melhor vizinho para seguir
                    vert = seleciona_melhor_vertice(arestas_gu.copy(), vizinhos, vert)
                    vert_seguinte = None
                    continue

        else:
            # Se o terminal for de grau1
            terminal_grau1 = True

    # Se vertice estiver na rota ou o vertice for um terminal de grau1
    if vert in rota or terminal_grau1:

        # Pega o vertice anterior ao atual
        vert = rota[rota.index(vert) - 1]
        # Vê o vizinhos anterior ao atual
        vizinhos, com_terms, nome_vizinhos = procura_vizinhos(arestas_gu.copy(), terminais_aux, vert)
        # Pega lista de vizinhos que não estão na rota
        nome_vizinhos = list(set(nome_vizinhos).difference(set(rota)))

        # Se houverem anteriores ao atual que naõ estão na rota
        if nome_vizinhos:
            # Seleciona melhor vertice
            vert = seleciona_melhor_vertice(arestas_gu.copy(), vizinhos, vert)

        continue


