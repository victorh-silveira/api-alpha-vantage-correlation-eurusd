import requests
import pandas as pd
import numpy as np

# Função para buscar os dados do Alpha Vantage no timeframe de 30min
def fetchExchangeRate(apiToken, pair):
    url = f"https://www.alphavantage.co/query"
    params = {
        "function": "FX_INTRADAY",  # Pegando dados intraday de Forex
        "from_symbol": pair.split("/")[0],
        "to_symbol": pair.split("/")[1],
        "apikey": apiToken,
        "interval": "30min",  # Definindo o intervalo de 30 minutos
        "outputsize": "compact"
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if "Time Series FX (30min)" not in data:
        raise Exception(f"Erro ao buscar dados para o par {pair}")
    
    # Convertendo o dicionário em um DataFrame
    df = pd.DataFrame(data["Time Series FX (30min)"]).T
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
    correlacoes_ordenadas = dict(sorted(correlacoes.items(), key=lambda item: item[1]))

    return correlacoes_ordenadas

# Função para exibir as correlações de forma organizada
def exibirCorrelacoes(titulo, correlacoes):
    print(f"\n{titulo}")
    for pair, corr in correlacoes.items():
        print(f"{pair}: {corr:.2f}")

# Seu token da Alpha Vantage
apiToken = "HIBKV1AXJA6BTKDE"

# Par alvo (EUR/USD)
targetPair = "EUR/USD"

# Pares Major e Minor
majorPairs = ["GBP/USD", "USD/JPY", "USD/CHF", "USD/CAD", "AUD/USD", "NZD/USD"]
minorPairs = ["EUR/GBP", "EUR/AUD", "EUR/CAD", "EUR/JPY", "GBP/JPY", "GBP/AUD", "AUD/JPY", "CHF/JPY", "NZD/JPY", "GBP/CHF"]

# Calcula correlação para os pares Major
correlacao_major = calcularCorrelacao(apiToken, targetPair, majorPairs)
# Calcula correlação para os pares Minor
correlacao_minor = calcularCorrelacao(apiToken, targetPair, minorPairs)

# Exibe correlações ordenadas em ordem crescente
exibirCorrelacoes("Correlação - Pares Major", correlacao_major)
exibirCorrelacoes("Correlação - Pares Minor", correlacao_minor)
