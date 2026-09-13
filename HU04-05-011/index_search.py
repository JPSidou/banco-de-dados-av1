import time


def search_with_index_trace(key, buckets, hasher_func, pages):
    """
    Busca uma chave usando o índice e registra o caminho percorrido, para que a
    interface destaque o bucket e a página acessados (HU14 / CA29).

    RN19: aplica a função hash, localiza o bucket, recupera o endereço da página
    e carrega a página para localizar a tupla.

    Custo: cada bucket lido na cadeia conta 1 leitura e a página de dados, 1 leitura.
    """
    start_time = time.perf_counter()

    bucket_index = hasher_func(key, len(buckets))
    current = buckets[bucket_index]

    bucket_reads = 0
    chain_position = None
    bucket_position = None
    page_id = None

    while current is not None:
        for position, (register_key, register_page_id) in enumerate(current.registers):
            if register_key == key:
                chain_position = bucket_reads
                bucket_position = position
                page_id = register_page_id
                break

        bucket_reads += 1

        if page_id is not None:
            break

        current = current.overflow

    page_reads = 0
    page_position = None

    if page_id is not None:
        page_reads = 1
        try:
            page_position = pages[page_id].index(key)
        except ValueError:
            page_position = None

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return {
        "key": key,
        "found": page_position is not None,
        "bucket_index": bucket_index,
        "chain_position": chain_position,
        "bucket_position": bucket_position,
        "page_id": page_id,
        "page_position": page_position,
        "bucket_reads": bucket_reads,
        "page_reads": page_reads,
        "cost_io": bucket_reads + page_reads,
        "time_ms": elapsed_ms,
    }
