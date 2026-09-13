import time


def table_scan(pages, key, max_records=None):
    """
    HU10: Executa o table scan lendo página por página e registro por registro
    até encontrar a chave de busca.

    RN21: os registros lidos até encontrar a chave são listados.
    CA22: informa o número da página onde encontrou e o custo (páginas lidas).

    O parâmetro max_records limita quantos registros são guardados na lista de
    retorno (a contagem continua exata), para que a interface não precise
    exibir centenas de milhares de linhas. max_records=None guarda todos e
    max_records=0 não guarda nenhum.
    """
    start_time = time.perf_counter()

    records_read = []
    records_read_count = 0
    pages_read = 0
    found_page_id = None
    found = False

    for page_id, page in enumerate(pages):
        pages_read += 1

        for register in page:
            records_read_count += 1

            if max_records is None or len(records_read) < max_records:
                records_read.append((page_id, register))

            if register == key:
                found_page_id = page_id
                found = True
                break

        if found:
            break

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return {
        "key": key,
        "found": found,
        "page_id": found_page_id,
        "cost_io": pages_read,
        "records_read": records_read,
        "records_read_count": records_read_count,
        "records_truncated": records_read_count > len(records_read),
        "time_ms": elapsed_ms,
    }
