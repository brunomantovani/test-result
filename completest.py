from functools import reduce
import os
import requests
import time
import json

def listar_arquivos_com_multiplas_extensoes_recursivamente(diretorio):
    print("Iniciando a busca por arquivos recursivamente...")
    extensoes_permitidas = ['.cs', '.java']
    arquivos_encontrados = []

    resultados = []

    for raiz, diretorios, arquivos in os.walk(diretorio):
        for arquivo in arquivos:
            if any(arquivo.endswith(extensao) for extensao in extensoes_permitidas):
                caminho_arquivo = os.path.join(raiz, arquivo)

                # Ignora arquivos que já contêm "Test" no final do nome (case insensitive)
                if "test" not in os.path.basename(caminho_arquivo).lower():
                    arquivos_encontrados.append(caminho_arquivo)
                    caminho_arquivo_test = criar_caminho_test(caminho_arquivo, diretorio)
                    os.makedirs(os.path.dirname(caminho_arquivo_test), exist_ok=True)

                    resultado = processar_arquivo(caminho_arquivo, caminho_arquivo_test)
                    resultados.append(resultado)

    return arquivos_encontrados, resultados

def criar_caminho_test(caminho_arquivo, diretorio_destino):
    caminho_relativo = os.path.relpath(caminho_arquivo, diretorio_destino)
    caminho_modificado = caminho_relativo.replace(os.path.sep + "src" + os.path.sep + "main", os.path.sep + "src" + os.path.sep + "test")
    
    # Adicionando o sufixo "Test" no nome do arquivo
    nome_arquivo, extensao = os.path.splitext(os.path.basename(caminho_modificado))
    caminho_modificado = os.path.join(os.path.dirname(caminho_modificado), nome_arquivo + "Test" + extensao)

    return os.path.join(diretorio_destino, caminho_modificado)

def processar_arquivo(caminho_arquivo, caminho_arquivo_test):
    print(f"Iniciando o processamento do arquivo: {caminho_arquivo}...")
    try:
        inicio_tempo = time.time()
        resposta_api = enviar_para_gpt3(caminho_arquivo)
        fim_tempo = time.time()
        
        if resposta_api:
            with open(caminho_arquivo_test, 'w', encoding='utf-8') as f_test:
                f_test.write(resposta_api)

            # Conta as linhas retornadas pela API
            qtd_linhas = resposta_api.count('\n')
            
            # Conta quantas vezes a string "@Test" aparece no conteúdo do arquivo
            qtd_testes = resposta_api.lower().count('@test')

            print(f"Arquivo processado: {caminho_arquivo}. Tempo de resposta da API: {fim_tempo - inicio_tempo:.2f} segundos")

            # Retorna as informações em um dicionário
            return {
                'nome_projeto': 'CompleTest',
                'tempo_execucao': fim_tempo - inicio_tempo,
                'qtd_linhas': qtd_linhas,
                'qtd_testes': qtd_testes
            }
        else:
            print(f"Resposta da API vazia para o arquivo: {caminho_arquivo}")
            return None
    except Exception as e:
        print(f"Erro ao processar o arquivo {caminho_arquivo}: {str(e)}")
        return None

def enviar_para_gpt3(caminho_arquivo):
    print(f"Iniciando a chamada à API para o arquivo: {caminho_arquivo}...")
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key is None:
        print("Chave de API não encontrada. Configure a variável de ambiente OPENAI_API_KEY.")
        return

    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    dados = {
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'user', 'content': f'Create only a test class using junit jupiter with all possible scenarios and same packages declaration for the given content:\n\n{conteudo}\n\nTest class:'}]
    }

    try:
        inicio_tempo_api = time.time()
        resposta = requests.post(url, json=dados, headers=headers)
        fim_tempo_api = time.time()
        
        # Verifica se o código de status é 400 (Bad Request)
        if resposta.status_code == 400:
            print(f"Erro na solicitação para a API: {resposta.text}")
            return None

        resposta.raise_for_status()  # Lança uma exceção se a solicitação não for bem-sucedida

        resposta_json = resposta.json()
        tempo_resposta_api = fim_tempo_api - inicio_tempo_api
        print(f"Tempo total de chamada à API: {tempo_resposta_api:.2f} segundos")
        return resposta_json['choices'][0]['message']['content']
    except requests.exceptions.RequestException as req_error:
        print(f"Erro na solicitação para a API: {req_error}")
        return None
    except Exception as e:
        print(f"Erro ao processar a resposta da API: {str(e)}")
        return None

def somar_propriedades(objeto1, objeto2):
    return {
        'nome_projeto': 'CompleTest',
        'qtd_linhas': objeto1['qtd_linhas'] + objeto2['qtd_linhas'],
        'qtd_testes': objeto1['qtd_testes'] + objeto2['qtd_testes'],
        'tempo_execucao': objeto1['tempo_execucao'] + objeto2['tempo_execucao']
    }

# Use '.' para indicar o diretório corrente da linha de comando
diretorio_corrente = '.'
arquivos_encontrados, resultados = listar_arquivos_com_multiplas_extensoes_recursivamente(diretorio_corrente)

soma_total = reduce(somar_propriedades, resultados)

# Caminho do arquivo JSON
caminho_arquivo_json = 'result.json'

# Escrevendo o JSON no arquivo
with open(caminho_arquivo_json, 'w') as arquivo_json:
    json.dump(soma_total, arquivo_json, indent=2)
