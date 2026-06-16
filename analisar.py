import pandas as pd
import numpy as np
from scipy import stats
import sys
import os
from datetime import datetime

def parse_moeda(serie):
    return (
        serie.str.replace("R$ ", "", regex=False)
             .str.replace(".", "", regex=False)
             .str.replace(",", ".", regex=False)
             .astype(float)
    )

def carregar_dataset(caminho):
    df = pd.read_csv(caminho)
    df["Data"] = pd.to_datetime(df["Data"])
    for col in ["comissão", "cashback", "vendas totais"]:
        df[col] = parse_moeda(df[col])
    return df

def calcular_metricas(df):
    grupos = df.groupby("Grupos de usuários").agg(
        dias=("Data", "nunique"),
        compradores=("compradores", "sum"),
        comissao=("comissão", "sum"),
        cashback=("cashback", "sum"),
        vendas=("vendas totais", "sum"),
    ).reset_index()

    grupos["ticket_medio"] = grupos["vendas"] / grupos["compradores"]
    grupos["margem_liquida"] = grupos["comissao"] - grupos["cashback"]
    grupos["taxa_cashback"] = grupos["cashback"] / grupos["comissao"]
    grupos["roi"] = grupos["margem_liquida"] / grupos["cashback"]
    grupos["vendas_por_dia"] = grupos["vendas"] / grupos["dias"]
    grupos["compradores_por_dia"] = grupos["compradores"] / grupos["dias"]

    return grupos

def teste_significancia(df, metrica="vendas totais"):
    grupos = df["Grupos de usuários"].unique()
    resultados = {}

    for g in grupos:
        serie = df[df["Grupos de usuários"] == g][metrica].values
        resultados[g] = serie

    pares = []
    lista_grupos = list(grupos)
    for i in range(len(lista_grupos)):
        for j in range(i + 1, len(lista_grupos)):
            g1 = lista_grupos[i]
            g2 = lista_grupos[j]
            stat, p = stats.ttest_ind(resultados[g1], resultados[g2])
            pares.append({
                "par": f"{g1} vs {g2}",
                "t_stat": round(stat, 4),
                "p_value": round(p, 4),
                "significativo": "Sim" if p < 0.05 else "Não"
            })

    return pd.DataFrame(pares)

def escolher_vencedor(metricas):
    controle = metricas.iloc[0]["Grupos de usuários"]

    candidatos = metricas.copy()
    candidatos["score"] = (
        candidatos["vendas"].rank() * 0.4 +
        candidatos["compradores"].rank() * 0.3 +
        candidatos["margem_liquida"].rank() * 0.2 +
        candidatos["roi"].rank() * 0.1
    )

    vencedor = candidatos.loc[candidatos["score"].idxmax(), "Grupos de usuários"]
    return vencedor, controle

def gerar_relatorio(caminho_csv):
    nome_arquivo = os.path.basename(caminho_csv)
    parceiro = nome_arquivo.replace(".csv", "").split("_")[-1]

    df = carregar_dataset(caminho_csv)

    parceiro_nome = df["Parceiro"].iloc[0]
    periodo_inicio = df["Data"].min().strftime("%d/%m/%Y")
    periodo_fim = df["Data"].max().strftime("%d/%m/%Y")
    n_grupos = df["Grupos de usuários"].nunique()
    n_dias = df["Data"].nunique()

    metricas = calcular_metricas(df)
    sig = teste_significancia(df, "vendas totais")
    vencedor, controle = escolher_vencedor(metricas)

    controle_linha = metricas[metricas["Grupos de usuários"] == controle].iloc[0]
    vencedor_linha = metricas[metricas["Grupos de usuários"] == vencedor].iloc[0]

    if controle != vencedor:
        uplift_vendas = ((vencedor_linha["vendas"] - controle_linha["vendas"]) / controle_linha["vendas"]) * 100
        uplift_compradores = ((vencedor_linha["compradores"] - controle_linha["compradores"]) / controle_linha["compradores"]) * 100
    else:
        uplift_vendas = 0
        uplift_compradores = 0

    linhas = []
    linhas.append("=" * 65)
    linhas.append(f"RELATÓRIO DE TESTE A/B — {parceiro_nome.upper()}")
    linhas.append("=" * 65)
    linhas.append(f"Período: {periodo_inicio} a {periodo_fim} ({n_dias} dias)")
    linhas.append(f"Grupos testados: {n_grupos}")
    linhas.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    linhas.append("")

    linhas.append("─" * 65)
    linhas.append("1. MÉTRICAS CONSOLIDADAS POR GRUPO")
    linhas.append("─" * 65)

    for _, row in metricas.iterrows():
        linhas.append(f"\n{row['Grupos de usuários']}")
        linhas.append(f"  Compradores totais:      {int(row['compradores']):>10,}")
        linhas.append(f"  Vendas totais (GMV):     R$ {row['vendas']:>12,.2f}")
        linhas.append(f"  Comissão recebida:       R$ {row['comissao']:>12,.2f}")
        linhas.append(f"  Cashback distribuído:    R$ {row['cashback']:>12,.2f}")
        linhas.append(f"  Margem líquida:          R$ {row['margem_liquida']:>12,.2f}")
        linhas.append(f"  Ticket médio:            R$ {row['ticket_medio']:>12,.2f}")
        linhas.append(f"  Taxa de cashback:        {row['taxa_cashback']*100:>10.1f}%")
        linhas.append(f"  ROI (margem/cashback):   {row['roi']:>10.2f}x")
        linhas.append(f"  Vendas/dia:              R$ {row['vendas_por_dia']:>12,.2f}")

    linhas.append("")
    linhas.append("─" * 65)
    linhas.append("2. TESTE DE SIGNIFICÂNCIA ESTATÍSTICA (t-test, α = 0.05)")
    linhas.append("─" * 65)
    for _, row in sig.iterrows():
        linhas.append(f"  {row['par']}")
        linhas.append(f"    p-value: {row['p_value']}  |  Significativo: {row['significativo']}")

    linhas.append("")
    linhas.append("─" * 65)
    linhas.append("3. ANÁLISE E DECISÃO")
    linhas.append("─" * 65)

    if vencedor == controle:
        linhas.append(f"\n  Nenhum grupo superou o controle ({controle}) de forma")
        linhas.append("  consistente. Recomenda-se manter o grupo de controle.")
        decisao = f"Manter {controle} (sem vencedor claro)"
        resultado = "Inconclusivo"
    else:
        linhas.append(f"\n  Grupo vencedor: {vencedor}")
        linhas.append(f"  Uplift em vendas vs controle: +{uplift_vendas:.1f}%")
        linhas.append(f"  Uplift em compradores vs controle: +{uplift_compradores:.1f}%")
        linhas.append("")
        linhas.append(f"  RECOMENDAÇÃO: Escalar {vencedor} para 100% do tráfego.")
        decisao = f"Escalar {vencedor} para 100% do tráfego"
        resultado = f"{vencedor} vence com +{uplift_vendas:.1f}% em vendas"

    linhas.append("")
    linhas.append("=" * 65)

    relatorio_texto = "\n".join(linhas)

    nome_saida = f"relatorio_{parceiro.lower()}.txt"
    caminho_saida = os.path.join("relatorios", nome_saida)
    os.makedirs("relatorios", exist_ok=True)

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(relatorio_texto)

    print(f"Relatório salvo em: {caminho_saida}")

    return {
        "nome_teste": f"Teste A/B {parceiro_nome}",
        "descricao": f"Teste com {n_grupos} grupos — {periodo_inicio} a {periodo_fim} ({n_dias} dias)",
        "resultado": resultado,
        "decisao": decisao,
        "data_analise": datetime.now().strftime("%d/%m/%Y"),
    }

def registrar_acompanhamento(entradas, caminho_saida="acompanhamento_testes.csv"):
    colunas = ["nome_teste", "descricao", "resultado", "decisao", "data_analise"]

    df_novo = pd.DataFrame(entradas, columns=colunas)

    if os.path.exists(caminho_saida) and os.path.getsize(caminho_saida) > 0:
        df_existente = pd.read_csv(caminho_saida)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
        df_final = df_final.drop_duplicates(subset=["nome_teste"], keep="last")
    else:
        df_final = df_novo

    df_final.to_csv(caminho_saida, index=False)
    print(f"Planilha de acompanhamento atualizada: {caminho_saida}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python analisar.py <caminho_do_csv> [<csv2> <csv3> ...]")
        sys.exit(1)

    arquivos = sys.argv[1:]
    registros = []

    for arquivo in arquivos:
        if not os.path.exists(arquivo):
            print(f"Arquivo não encontrado: {arquivo}")
            continue
        print(f"\nAnalisando: {arquivo}")
        registro = gerar_relatorio(arquivo)
        registros.append(registro)

    if registros:
        registrar_acompanhamento(registros)