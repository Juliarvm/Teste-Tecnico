# Análise de Testes A/B — Méliuz Cashback

Solução para automatizar a análise de testes A/B de cashback por parceiro.

## Estrutura do projeto

```
ab_cashback/
├── analisar.py                  # script principal
├── prompt_instrucao.txt         # instruções para uso com IA (Claude, ChatGPT etc.)
├── acompanhamento_testes.csv    # planilha com todos os testes analisados
└── relatorios/
    ├── relatorio_parceiroa.txt
    ├── relatorio_parceirob.txt
    └── relatorio_parceiroc.txt
```

## Como rodar

### Pré-requisitos

```bash
pip install pandas scipy numpy
```

### Analisar um único arquivo

```bash
python analisar.py caminho/para/dataset.csv
```

### Analisar vários de uma vez

```bash
python analisar.py dataset_01_parceiroA.csv dataset_02_parceiroB.csv dataset_03_parceiroC.csv
```

Os arquivos CSV podem estar em qualquer pasta — basta passar o caminho completo. Não é necessário colocá-los na mesma pasta do script.

O relatório de cada teste é salvo automaticamente em `relatorios/` e o arquivo `acompanhamento_testes.csv` é atualizado com o resumo.

---

## Como usar com IA (Claude Code, Cursor, ChatGPT)

Copie o conteúdo de `prompt_instrucao.txt` como system prompt ou instrução inicial.
Depois, basta pedir em linguagem natural:

> "Analisa o teste do Parceiro D, o arquivo é dataset_04_parceiroD.csv"

A IA executa `python analisar.py dataset_04_parceiroD.csv` e retorna a análise.

---

## Schema esperado dos CSVs

| Coluna             | Tipo       | Exemplo       |
|--------------------|------------|---------------|
| Data               | YYYY-MM-DD | 2011-01-01    |
| Grupos de usuários | string     | Grupo 1       |
| Parceiro           | string     | Parceiro A    |
| compradores        | int        | 142           |
| comissão           | R$ string  | R$ 10.273     |
| cashback           | R$ string  | R$ 3.267      |
| vendas totais      | R$ string  | R$ 93.390     |

---

## O que o relatório entrega

- Métricas consolidadas por grupo: GMV, compradores, comissão, cashback, margem líquida, ticket médio, taxa de cashback, ROI e vendas/dia
- Teste t de Student entre todos os pares de grupos (α = 0.05)
- Decisão: qual variante escalar para 100% do tráfego

---

## Planilha de acompanhamento

O arquivo `acompanhamento_testes.csv` registra automaticamente cada teste com:
- Nome do teste
- Descrição (período e número de grupos)
- Resultado
- Decisão tomada
- Data da análise

---

## Resultados dos testes rodados

### Parceiro A — Jan/2011 a Abr/2011 (92 dias, 3 grupos)

O Grupo 3 apresentou o maior volume de vendas (R$ 6,78M) e mais compradores (11.410), com uplift de +21,1% em GMV e +18,4% em compradores em relação ao controle. A diferença entre Grupo 1 e Grupo 3 foi estatisticamente significativa (p = 0.02). O trade-off é a margem líquida menor (R$ 264k vs R$ 404k do controle), pois o cashback mais alto consome mais da comissão.

**Decisão: escalar Grupo 3 para 100% do tráfego.**

---

### Parceiro B — Mai/2011 a Jun/2011 (61 dias, 3 grupos)

O Grupo 1 (controle) foi superior em todas as métricas relevantes: maior GMV (R$ 4,09M), mais compradores (7.990), melhor margem líquida (R$ 286k) e melhor ROI (1.75x). Os Grupos 2 e 3 tiveram cashback mais alto mas perderam volume e margem — a diferença é estatisticamente significativa (p ≈ 0).

**Decisão: manter Grupo 1 (controle).**

---

### Parceiro C — Jul/2011 a Ago/2011 (45 dias, 2 grupos)

Os dois grupos tiveram desempenho similar em vendas e compradores, sem diferença estatística (p = 0.63). O Grupo 2, porém, distribuiu 100% da comissão como cashback — margem líquida zero, inviável financeiramente. O Grupo 1 ainda retém R$ 34k de margem com taxa de cashback de 71,4%.

**Decisão: manter Grupo 1 (controle).**
