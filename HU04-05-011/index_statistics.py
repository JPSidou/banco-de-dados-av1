def bucket_chain(bucket):
    """Percorre um bucket primário e todos os seus buckets de overflow."""
    current = bucket

    while current is not None:
        yield current
        current = current.overflow


def overflow_statistics(buckets):
    """
    HU13 / RN25: calcula a taxa de overflow (%) do índice.
    HU08 / CA18: contabiliza quantos buckets entraram em overflow.

    Um bucket está em overflow quando excedeu o FR e precisou de pelo menos um
    bucket de transbordamento. A taxa é a proporção desses buckets sobre o NB.
    """
    number_of_buckets = len(buckets)

    overflowed_buckets = 0
    overflow_buckets_created = 0
    registers_in_overflow = 0
    longest_overflow_chain = 0

    for bucket in buckets:
        if bucket.overflow is not None:
            overflowed_buckets += 1

        chain_length = 0
        for extra in bucket_chain(bucket.overflow):
            chain_length += 1
            registers_in_overflow += len(extra.registers)

        overflow_buckets_created += chain_length
        longest_overflow_chain = max(longest_overflow_chain, chain_length)

    overflow_rate = (
        overflowed_buckets / number_of_buckets * 100.0
        if number_of_buckets > 0
        else 0.0
    )

    return {
        "number_of_buckets": number_of_buckets,
        "overflowed_buckets": overflowed_buckets,
        "overflow_buckets_created": overflow_buckets_created,
        "registers_in_overflow": registers_in_overflow,
        "longest_overflow_chain": longest_overflow_chain,
        "overflow_rate_pct": overflow_rate,
    }


def overflow_rate(buckets):
    """CA26: percentual de overflow a ser exibido na interface."""
    return overflow_statistics(buckets)["overflow_rate_pct"]


def collision_statistics(buckets, number_of_registers):
    """
    HU12 / RN24: calcula a taxa de colisões (%) do índice.

    Conforme a RN14, só é colisão o registro que chega a um bucket já cheio,
    ou seja, que precisou ir para a cadeia de overflow. A taxa é a proporção
    desses registros sobre o total de registros (NR).
    """
    collisions = overflow_statistics(buckets)["registers_in_overflow"]

    collision_rate = (
        collisions / number_of_registers * 100.0
        if number_of_registers > 0
        else 0.0
    )

    return {
        "collisions": collisions,
        "collision_rate_pct": collision_rate,
    }
