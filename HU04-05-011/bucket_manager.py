import math
from bucket import Bucket



def create_buckets(number_of_registers, bucket_size):
    if bucket_size <= 0:
        raise ValueError("O tamanho do bucket (FR) deve ser maior que zero.")
    if number_of_registers <= 0:
        raise ValueError("A quantidade de registros deve ser maior que zero.")

    bucket_quantity = math.floor(
        number_of_registers / bucket_size) + 1

    if bucket_quantity <= number_of_registers / bucket_size:
        raise ValueError("Invalid size of bucket.  NB <= NR / FR")

    buckets = []

    for i in range(bucket_quantity):
        buckets.append(Bucket(bucket_size))

    print("Foram criados ", bucket_quantity, " buckets.")

    return buckets

