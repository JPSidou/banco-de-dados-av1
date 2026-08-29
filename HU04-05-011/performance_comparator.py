import time
import matplotlib.pyplot as plt


def search_with_index(key, buckets, hasher_func, pages):
    """
    Busca uma chave usando o Índice Hash Estático.
    Retorna se achou, o id da página, o custo de I/O e o tempo em milissegundos.
    """
    start_time = time.perf_counter()
    
    num_buckets = len(buckets)
    bucket_index = hasher_func(key, num_buckets)
    
    current = buckets[bucket_index]
    bucket_io = 0
    found_page_id = None
    
    # Percorre a cadeia de buckets (Bucket Chaining)
    while current is not None:
        bucket_io += 1
        for reg_key, page_id in current.registers:
            if reg_key == key:
                found_page_id = page_id
                break
        if found_page_id is not None:
            break
        current = current.overflow
    
    # Se encontrou o ponteiro, faz 1 leitura da página de dados real
    data_page_io = 0
    found_in_page = False
    if found_page_id is not None:
        data_page_io = 1
        if 0 <= found_page_id < len(pages):
            if key in pages[found_page_id]:
                found_in_page = True
                
    end_time = time.perf_counter()
    elapsed_ms = (end_time - start_time) * 1000.0
    total_io = bucket_io + data_page_io
    
    return {
        "key": key,
        "found": found_in_page,
        "page_id": found_page_id,
        "cost_io": total_io,
        "bucket_io": bucket_io,
        "data_page_io": data_page_io,
        "time_ms": elapsed_ms
    }


def search_with_table_scan(key, pages):
    """
    Busca sequencial percorrendo página por página.
    Retorna se achou, o id da página, o custo de páginas lidas e o tempo em ms.
    """
    start_time = time.perf_counter()
    
    pages_read = 0
    found_page_id = None
    found = False
    
    for page_idx, page in enumerate(pages):
        pages_read += 1
        if key in page:
            found_page_id = page_idx
            found = True
            break
            
    end_time = time.perf_counter()
    elapsed_ms = (end_time - start_time) * 1000.0
    
    return {
        "key": key,
        "found": found,
        "page_id": found_page_id,
        "cost_io": pages_read,
        "time_ms": elapsed_ms
    }


def compare(key, buckets, hasher_func, pages):
    """
    HU11: Executa a comparação individual entre Índice e Table Scan.
    """
    index_res = search_with_index(key, buckets, hasher_func, pages)
    scan_res = search_with_table_scan(key, pages)
    
    time_diff = scan_res["time_ms"] - index_res["time_ms"]
    io_diff = scan_res["cost_io"] - index_res["cost_io"]
    
    # Redução percentual
    io_reduction = (io_diff / scan_res["cost_io"] * 100.0) if scan_res["cost_io"] > 0 else 0.0
    time_speedup = (time_diff / scan_res["time_ms"] * 100.0) if scan_res["time_ms"] > 0 else 0.0
    
    return {
        "key": key,
        "found": index_res["found"],
        "index": index_res,
        "scan": scan_res,
        "time_diff_ms": time_diff,
        "io_diff": io_diff,
        "io_reduction_pct": io_reduction,
        "time_speedup_pct": time_speedup
    }


def compare_batch(keys, buckets, hasher_func, pages):
    """
    Executa bateria de testes para uma lista de chaves e computa médias gerais.
    """
    results = [compare(k, buckets, hasher_func, pages) for k in keys]
    
    n = len(results)
    if n == 0:
        return {"results": [], "avg_index_io": 0, "avg_scan_io": 0, "avg_io_reduction_pct": 0, "avg_speedup_pct": 0}
        
    avg_idx_io = sum(r["index"]["cost_io"] for r in results) / n
    avg_scn_io = sum(r["scan"]["cost_io"] for r in results) / n
    avg_io_red = sum(r["io_reduction_pct"] for r in results) / n
    avg_speedup = sum(r["time_speedup_pct"] for r in results) / n
    
    return {
        "results": results,
        "avg_index_io": avg_idx_io,
        "avg_scan_io": avg_scn_io,
        "avg_io_reduction_pct": avg_io_red,
        "avg_speedup_pct": avg_speedup
    }


def plot_charts(batch_result, output_path="comparativo_hu11.png"):
    """
    Gera gráficos comparativos limpos para o GitHub e relatório.
    """
    results = batch_result["results"]
    keys = [r["key"] for r in results]
    idx_ios = [r["index"]["cost_io"] for r in results]
    scn_ios = [r["scan"]["cost_io"] for r in results]
    idx_times = [r["index"]["time_ms"] for r in results]
    scn_times = [r["scan"]["time_ms"] for r in results]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    x = range(len(keys))
    
    # 1. Gráfico de I/O
    ax1.bar([i - 0.2 for i in x], idx_ios, width=0.4, label='Índice Hash', color='#2ecc71')
    ax1.bar([i + 0.2 for i in x], scn_ios, width=0.4, label='Table Scan', color='#e74c3c')
    ax1.set_title('Custo de I/O (Páginas Lidas por Chave)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Quantidade de Acessos a Disco (I/O)')
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(keys, rotation=45, ha='right', fontsize=9)
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.4)
    
    # 2. Gráfico de Tempo
    ax2.plot(x, idx_times, marker='o', label='Índice Hash', color='#2ecc71', linewidth=2)
    ax2.plot(x, scn_times, marker='s', label='Table Scan', color='#e74c3c', linewidth=2)
    ax2.set_title('Tempo de Execução (ms por Chave)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Tempo (ms)')
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(keys, rotation=45, ha='right', fontsize=9)
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.4)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"📊 Gráfico salvo com sucesso em: {output_path}")
