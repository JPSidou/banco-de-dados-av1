def _bucket_chain(bucket):
    """Percorre um bucket primário e todos os seus buckets de overflow."""
    current = bucket

    while current is not None:
        yield current
        current = current.overflow


def overflow_statistics(buckets):
    """
    HU13 / RN25: calcula a taxa de overflow (%) do índice.

    Um bucket está em overflow quando excedeu o FR e precisou de pelo menos um
    bucket de transbordamento. A taxa é a proporção desses buckets sobre o NB.
    """
    number_of_buckets = len(buckets)

    overflowed_buckets = 0
    overflow_buckets_created = 0
    registers_in_overflow = 0

    for bucket in buckets:
        if bucket.overflow is not None:
            overflowed_buckets += 1

        for extra in _bucket_chain(bucket.overflow):
            overflow_buckets_created += 1
            registers_in_overflow += len(extra.registers)

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
        "overflow_rate_pct": overflow_rate,
    }


def overflow_rate(buckets):
    """CA26: percentual de overflow a ser exibido na interface."""
    return overflow_statistics(buckets)["overflow_rate_pct"]
