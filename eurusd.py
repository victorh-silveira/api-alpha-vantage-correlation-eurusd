import requests
import pandas as pd
import numpy as np
from scipy.stats import pearsonr

def obterDadosHistoricos(parMoeda, apiKey, outputsize="compact"):
    """
    Consulta a API para obter dados históricos de um par de moedas.

    :param parMoeda: Par de moedas no formato "XXXYYY" (ex: "EURUSD")
    :param apiKey: Chave de API para autenticação
    :param outputsize: Tamanho do retorno da API ("compact" para últimos 100 dados, "full" para todos os dados)
    :return: DataFrame com dados históricos de fechamento diário
    """
    url = f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={parMoeda[:3]}&to_symbol={parMoeda[3:]}&apikey={apiKey}&outputsize={outputsize}"
    response = requests.get(url)
    data = response.json()

    if "Time Series FX (Daily)" not in data:
        raise ValueError(f"Erro ao obter dados para {parMoeda}")

    # Converter dados para DataFrame
    df = pd.DataFrame(data["Time Series FX (Daily)"]).T
    df = df.rename(columns={
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close"
    })
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)

    return df["close"]

def calcularCorrelacoes(paresMoedas, referencia, apiKey):
    """
    Calcula as correlações entre o par de referência e os demais pares de moedas.

    :param paresMoedas: Lista de pares de moedas para análise
    :param referencia: Par de moedas de referência (ex: "EURUSD")
    :param apiKey: Chave de API para autenticação
    :return: DataFrame com as correlações de cada par de moedas com o par de referência
    """
    dadosReferencia = obterDadosHistoricos(referencia, apiKey)
    correlacoes = {}

    for par in paresMoedas:
        if par != referencia:
            dadosPar = obterDadosHistoricos(par, apiKey)
            # Alinhar os dados pelo índice (data)
            dadosCombinados = pd.concat([dadosReferencia, dadosPar], axis=1, join='inner')
            dadosCombinados.columns = [referencia, par]
            
            # Calcular correlação
            correlacao, _ = pearsonr(dadosCombinados[referencia], dadosCombinados[par])
            correlacoes[par] = correlacao

    # Converter o dicionário para DataFrame e ordenar
    dfCorrelacoes = pd.DataFrame.from_dict(correlacoes, orient='index', columns=['Correlacao'])
    dfCorrelacoes = dfCorrelacoes.sort_values(by='Correlacao', ascending=False)

    return dfCorrelacoes

def principaisCorrelacoesPositivasNegativas(dfCorrelacoes, n=3):
    """
    Identifica os principais pares com correlações positivas e negativas.

    :param dfCorrelacoes: DataFrame contendo as correlações
    :param n: Número de pares a serem exibidos para cada categoria (positiva e negativa)
    :return: DataFrame com os principais pares de correlação positiva e negativa
    """
    correlacoesPositivas = dfCorrelacoes[dfCorrelacoes['Correlacao'] > 0].head(n)
    correlacoesNegativas = dfCorrelacoes[dfCorrelacoes['Correlacao'] < 0].tail(n)

    return pd.concat([correlacoesPositivas, correlacoesNegativas])

def main():
    apiKey = "JHDH6P13A5W0RIMK"
    referencia = "EURUSD"
    paresMoedas = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURGBP"]

    dfCorrelacoes = calcularCorrelacoes(paresMoedas, referencia, apiKey)
    resultado = principaisCorrelacoesPositivasNegativas(dfCorrelacoes)

    print("Principais Pares Correlacionados com EUR/USD (Positiva e Negativamente):")
    print(resultado)

if __name__ == "__main__":
    main()
