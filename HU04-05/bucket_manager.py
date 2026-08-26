import math
from bucket import Bucket



def create_buckets(number_of_registers, bucket_size):
    bucket_quantity = math.floor(
        number_of_registers / bucket_size) + 1

    if bucket_quantity <= number_of_registers / bucket_size:
        raise ValueError("Invalid size of bucket.  NB <= NR / FR")

    buckets = []

    for i in range(bucket_quantity):
        buckets.append(Bucket(bucket_size))

    print("Foram criados ", bucket_quantity, " buckets.")

    return buckets

