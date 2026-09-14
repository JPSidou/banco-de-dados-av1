# Índice Hash Estático

Aplicação didática, feita em Python com interface Tkinter, que simula um **índice hash estático** sobre um arquivo de palavras dividido em páginas. Ela mostra como o índice é construído (buckets, colisões e overflow) e compara a busca pelo índice com um **table scan** sequencial, em tempo e em custo de leitura (I/O).

## Funcionalidades

- **Carga dos dados:** lê um arquivo `.txt` com uma palavra por linha e o divide em páginas do tamanho escolhido pelo usuário.
- **Construção do índice:** percorre as páginas registro por registro, aplica a função hash e guarda o par `(chave, página)` no bucket correspondente.
- **Estatísticas do índice:**
  - registros indexados comparados com o total do arquivo;
  - tempo de construção e páginas percorridas;
  - quantidade de buckets (NB) e capacidade de cada um (FR);
  - taxa de colisões e taxa de overflow;
  - buckets em overflow, buckets de overflow criados e a maior cadeia de overflow.
- **Busca com índice:** mostra passo a passo o bucket calculado, cada leitura na cadeia de overflow e a página acessada, destacando o registro encontrado.
- **Table scan:** lê página por página até achar a chave, informa o tempo de execução e lista os registros lidos no caminho com limite de exibição para manter a fluidez da UI.
- **Comparativo Índice x Scan (HU11):** aba dedicada e botão de comparação que contrastam tempo de execução, custo de I/O (páginas lidas), taxa de redução percentual (%) e notas didáticas explicando o comportamento do índice vs. scan para chaves na página 0.
- **Visualização:** abas com a primeira e a última página, a lista de buckets (com navegação direta por número), o conteúdo de cada bucket com sua cadeia de overflow e tabela comparativa de desempenho.

## Como funciona

| Conceito | Implementação |
| --- | --- |
| Capacidade do bucket (FR) | Fixa em `10` (`BUCKET_SIZE` em `app.py`) |
| Número de buckets (NB) | `⌊NR / FR⌋ + 1`, garantindo `NB > NR / FR` |
| Função hash | Hash multiplicativo sobre os caracteres da palavra (32 bits), módulo NB |
| Tratamento de overflow | Encadeamento: quando um bucket enche, um novo bucket de overflow é ligado a ele |
| Colisão | Registro que chega a um bucket já cheio e vai para a cadeia de overflow |
| Taxa de colisões | Registros em overflow ÷ total de registros (NR) |
| Taxa de overflow | Buckets com overflow ÷ total de buckets (NB) |
| Custo da busca com índice | 1 leitura por bucket percorrido na cadeia + 1 leitura da página de dados |
| Custo do table scan | Quantidade de páginas lidas até encontrar a chave |
| Comparativo (HU11) | Diferença de tempo (ms), diferença de I/O (páginas lidas) e % de redução |

## Requisitos

- Python 3.10 ou superior
- Tkinter (já vem com o Python no Windows e no macOS; no Linux pode ser instalado via `python3-tk`)
- `matplotlib`, apenas se desejar gerar arquivos PNG com gráficos em lote (opcional)

No Debian/Ubuntu:

```bash
sudo apt install python3-tk
pip install matplotlib  # opcional para exportar gráficos PNG
```

## Como executar

```bash
cd HU04-05-011
python3 app.py
```

Na interface:

1. Clique em **Selecionar arquivo .txt** e escolha o arquivo de palavras (uma por linha).
2. Informe o **tamanho da página** (inteiro maior que zero) e clique em **Construir índice**.
3. Digite uma **chave de busca** e use **Buscar com índice** (ou `Enter`), **Table scan** ou **Comparar**.
4. Navegue pelas abas **Páginas**, **Buckets**, **Busca por índice**, **Table scan** e **Comparativo (HU11)** para ver todos os detalhes.

## Estrutura do projeto

```
HU04-05-011/
├── app.py                    # Interface Tkinter, abas de navegação e comparativo HU11
├── bucket.py                 # Classe Bucket, com inserção e busca na cadeia de overflow
├── bucket_manager.py         # Cálculo de NB e criação dos buckets com validações defensivas
├── hasher.py                 # Função hash que mapeia uma palavra para um bucket
├── index_builder.py          # Construção do índice e contagem dos registros indexados
├── index_search.py           # Busca pelo índice com registro do caminho percorrido
├── index_statistics.py       # Estatísticas de colisão e overflow
├── table_scan.py             # Busca sequencial página por página com medição de tempo
└── performance_comparator.py # Lógica de comparação (HU11), testes em lote e exportação gráfica
```

### Comparador de desempenho (HU11)

A função `compare()` é consumida diretamente pela interface gráfica (`app.py`) na aba **Comparativo (HU11)**. Além disso, o arquivo `performance_comparator.py` pode ser executado via script para baterias de testes em lote e exportação de gráficos:

```python
from bucket_manager import create_buckets
from hasher import hash_word_to_bucket
from index_builder import build_index
from performance_comparator import compare_batch, plot_charts

words = [line.strip() for line in open("palavras.txt", encoding="utf-8") if line.strip()]
page_size = 100
pages = [words[i:i + page_size] for i in range(0, len(words), page_size)]

buckets = create_buckets(len(words), 10)
build_index(pages, buckets, hash_word_to_bucket)

batch = compare_batch(["casa", "banco", "dados"], buckets, hash_word_to_bucket, pages)
print(batch["avg_index_io"], batch["avg_scan_io"], batch["avg_io_reduction_pct"])
plot_charts(batch)  # salva comparativo_hu11.png se matplotlib estiver instalado
```
