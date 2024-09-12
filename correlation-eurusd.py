import requests
import pandas as pd
import os
from dotenv import load_dotenv


# Carregar o arquivo settings.env
load_dotenv('settings.env')


# Função para buscar os dados do Alpha Vantage no timeframe de 30min ou diário
def fetchExchangeRate(apiToken, pair):
    url = f"https://www.alphavantage.co/query"
    params = {
        "function": "FX_DAILY",  # Usando o endpoint de dados diários, que é gratuito
        "from_symbol": pair.split("/")[0],
        "to_symbol": pair.split("/")[1],
        "apikey": apiToken,
        "outputsize": "compact"
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Verifica se há mensagem de erro na resposta
    if "Error Message" in data or "Note" in data:
        raise Exception(f"Erro da API: {data.get('Error Message', data.get('Note', 'Erro desconhecido'))}")

    if "Time Series FX (Daily)" not in data:
        raise Exception(f"Erro ao buscar dados para o par {pair}")

    df = pd.DataFrame(data["Time Series FX (Daily)"]).T
    df = df.rename(columns={
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close"
    })
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


# Função para calcular a correlação entre o par alvo e outros pares fornecidos
def calcularCorrelacao(apiToken, targetPair, otherPairs):
    # Baixar dados para o par alvo (EUR/USD ou outro)
    dfTarget = fetchExchangeRate(apiToken, targetPair)
    dfTarget['close'] = pd.to_numeric(dfTarget['close'])  # Converter os preços para numéricos

    # Dicionário para armazenar correlações
    correlacoes = {}

    for pair in otherPairs:
        try:
            dfOther = fetchExchangeRate(apiToken, pair)
            dfOther['close'] = pd.to_numeric(dfOther['close'])

            # Concatenar os dados dos dois pares com base na data
            dfCombined = pd.concat([dfTarget['close'], dfOther['close']], axis=1, keys=[targetPair, pair]).dropna()

            # Calcular correlação
            correlacao = dfCombined.corr().iloc[0, 1]
            correlacoes[pair] = correlacao

        except Exception as e:
            print(f"Erro ao buscar dados ou calcular correlação para o par {pair}: {e}")

    # Ordenar as correlações em ordem crescente
    correlacoesOrdenadas = dict(sorted(correlacoes.items(), key=lambda item: item[1]))

    return correlacoesOrdenadas


# Função para exibir as correlações de forma organizada e salvar em um arquivo
def exibirCorrelacoes(titulo, correlacoes, outputFile):
    outputFile.write(f"\n{titulo}\n")
    print(f"\n{titulo}")
    for pair, corr in correlacoes.items():
        outputFile.write(f"{pair}: {corr:.2f}\n")
        print(f"{pair}: {corr:.2f}")


# Carregar o token da variável de ambiente
apiToken = os.getenv('ALPHAVANTAGE_API_KEY')

# Par alvo (EUR/USD)
targetPair = "EUR/USD"

# Pares Principais (Major Pairs)
majorPairs = ["AUD/JPY", "AUD/USD", "EUR/AUD", "EUR/CAD", "EUR/CHF", "EUR/GBP", "EUR/JPY", "EUR/USD", "GBP/AUD",
              "GBP/JPY", "GBP/USD", "USD/CAD", "USD/CHF", "USD/JPY"]

# Pares Secundários (Minor Pairs)
minorPairs = ["AUD/CAD", "AUD/CHF", "AUD/JPY", "EUR/NZD", "GBP/CAD", "GBP/CHF", "GBP/NZD", "NZD/JPY", "NZD/USD",
              "USD/MXN", "USD/PLN"]

# Calcula correlação para os pares Major
correlacaoMajor = calcularCorrelacao(apiToken, targetPair, majorPairs)
# Calcula correlação para os pares Minor
correlacaoMinor = calcularCorrelacao(apiToken, targetPair, minorPairs)

# Caminho do arquivo para salvar o resultado
currentDir = os.path.dirname(os.path.abspath(__file__))
outputPath = os.path.join(currentDir, "correlation-eurusd.txt")

# Abre o arquivo para escrever os resultados
with open(outputPath, "w") as outputFile:
    # Exibe e escreve correlações ordenadas em ordem crescente
    exibirCorrelacoes("Correlação - Pares Major", correlacaoMajor, outputFile)
    exibirCorrelacoes("Correlação - Pares Minor", correlacaoMinor, outputFile)

print(f"\nAs correlações foram salvas em: {outputPath}")
