import time


def build_index(pages, buckets, hasher_func):
    """
    HU06: Constrói o índice hash percorrendo página por página e registro por
    registro, para simular o custo real de leitura dos dados.

    RN12: a construção percorre as páginas e os registros de cada página.
    RN13: para cada tupla, aplica-se a função hash sobre a chave de busca e
          armazena-se no bucket o par (chave de busca, endereço da página).

    Retorna o tempo de construção (CA14) e a quantidade de registros indexados.
    """
    number_of_buckets = len(buckets)

    if number_of_buckets == 0:
        raise ValueError("Nenhum bucket foi criado. Execute create_buckets antes.")

    start_time = time.perf_counter()

    pages_read = 0
    indexed_registers = 0

    for page_id, page in enumerate(pages):
        pages_read += 1
        for key in page:
            bucket_index = hasher_func(key, number_of_buckets)
            buckets[bucket_index].insert(key, page_id)
            indexed_registers += 1

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    print("Índice construído com", indexed_registers, "registros em",
          f"{elapsed_ms:.2f}", "ms.")

    return {
        "indexed_registers": indexed_registers,
        "pages_read": pages_read,
        "number_of_buckets": number_of_buckets,
        "build_time_ms": elapsed_ms,
        "build_time_s": elapsed_ms / 1000.0,
    }


def count_indexed_registers(buckets):
    """
    CA13: percorre os buckets e suas cadeias de overflow para conferir que o
    índice contém todos os registros que foram lidos das páginas.
    """
    total = 0

    for bucket in buckets:
        current = bucket
        while current is not None:
            total += len(current.registers)
            current = current.overflow

    return total
