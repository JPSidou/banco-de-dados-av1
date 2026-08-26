
def hash_word_to_bucket(word: str, bucket_size: int):
    hash_val = 618619
    for char in word:
        hash_val = (hash_val << 7) + hash_val + ord(char)
        hash_val = hash_val & 0xFFFFFFFF
        return hash_val % bucket_size
