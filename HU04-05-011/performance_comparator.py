import time

from index_search import search_with_index_trace
from table_scan import table_scan

# Aliases para compatibilidade retroativa
search_with_index = search_with_index_trace
search_with_table_scan = table_scan


def compare(key, buckets, hasher_func, pages):
    """
    HU11: Executa a comparação individual entre Índice e Table Scan.
    RN22: Mostra a diferença de tempo entre busca com índice e table scan.
    RN23: Estima custo em acessos a disco/leitura de páginas.
    CA23: Exibe tempo de execução de ambos.
    CA24: Exibe custo estimado (páginas lidas) de ambos e a diferença percentual.
    """
    index_res = search_with_index_trace(key, buckets, hasher_func, pages)
    scan_res = table_scan(pages, key, max_records=0)

    time_diff = scan_res["time_ms"] - index_res["time_ms"]
    io_diff = scan_res["cost_io"] - index_res["cost_io"]

    # Redução percentual: quanto o índice economizou em relação ao scan
    io_reduction = (io_diff / scan_res["cost_io"] * 100.0) if scan_res["cost_io"] > 0 else 0.0
    time_reduction = (time_diff / scan_res["time_ms"] * 100.0) if scan_res["time_ms"] > 0 else 0.0

    # Fator de aceleração (Speedup real = T_scan / T_indice)
    speedup_ratio = (scan_res["time_ms"] / index_res["time_ms"]) if index_res["time_ms"] > 0 else 0.0

    return {
        "key": key,
        "found": index_res["found"],
        "index": index_res,
        "scan": scan_res,
        "time_diff_ms": time_diff,
        "io_diff": io_diff,
        "io_reduction_pct": io_reduction,
        "time_reduction_pct": time_reduction,
        "time_speedup_pct": time_reduction,  # Mantido para compatibilidade retroativa
        "speedup_ratio": speedup_ratio,
    }


def compare_batch(keys, buckets, hasher_func, pages):
    """
    Executa bateria de testes para uma lista de chaves e computa médias gerais.
    """
    results = [compare(k, buckets, hasher_func, pages) for k in keys]

    n = len(results)
    if n == 0:
        return {
            "results": [],
            "avg_index_io": 0,
            "avg_scan_io": 0,
            "avg_io_reduction_pct": 0,
            "avg_time_reduction_pct": 0,
            "avg_speedup_pct": 0,
            "avg_speedup_ratio": 0,
        }

    avg_idx_io = sum(r["index"]["cost_io"] for r in results) / n
    avg_scn_io = sum(r["scan"]["cost_io"] for r in results) / n
    avg_io_red = sum(r["io_reduction_pct"] for r in results) / n
    avg_time_red = sum(r["time_reduction_pct"] for r in results) / n
    avg_speedup_ratio = sum(r["speedup_ratio"] for r in results) / n

    return {
        "results": results,
        "avg_index_io": avg_idx_io,
        "avg_scan_io": avg_scn_io,
        "avg_io_reduction_pct": avg_io_red,
        "avg_time_reduction_pct": avg_time_red,
        "avg_speedup_pct": avg_time_red,  # Mantido para compatibilidade
        "avg_speedup_ratio": avg_speedup_ratio,
    }


def plot_charts(batch_result, output_path="comparativo_hu11.png"):
    """
    Gera gráficos comparativos salvando em PNG.
    Usa import preguiçoso (lazy import) de matplotlib para não quebrar a aplicação
    caso a biblioteca não esteja instalada no computador de apresentação.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("⚠️ Aviso: A biblioteca 'matplotlib' não está instalada no ambiente.")
        print("   A interface gráfica funciona normalmente sem ela.")
        print("   Para gerar o gráfico PNG em lote, instale com: pip install matplotlib")
        return None

    results = batch_result["results"]
    keys = [r["key"] for r in results]
    idx_ios = [r["index"]["cost_io"] for r in results]
    scn_ios = [r["scan"]["cost_io"] for r in results]
    idx_times = [r["index"]["time_ms"] for r in results]
    scn_times = [r["scan"]["time_ms"] for r in results]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    x = range(len(keys))

    # 1. Gráfico de I/O
    ax1.bar([i - 0.2 for i in x], idx_ios, width=0.4, label="Índice Hash", color="#2ecc71")
    ax1.bar([i + 0.2 for i in x], scn_ios, width=0.4, label="Table Scan", color="#e74c3c")
    ax1.set_title("Custo de I/O (Páginas Lidas por Chave)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Quantidade de Acessos a Disco (I/O)")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(keys, rotation=45, ha="right", fontsize=9)
    ax1.legend()
    ax1.grid(True, linestyle="--", alpha=0.4)

    # 2. Gráfico de Tempo
    ax2.plot(x, idx_times, marker="o", label="Índice Hash", color="#2ecc71", linewidth=2)
    ax2.plot(x, scn_times, marker="s", label="Table Scan", color="#e74c3c", linewidth=2)
    ax2.set_title("Tempo de Execução (ms por Chave)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Tempo (ms)")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(keys, rotation=45, ha="right", fontsize=9)
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"📊 Gráfico salvo com sucesso em: {output_path}")
    return output_path
