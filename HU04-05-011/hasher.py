def hash_word_to_bucket(word: str, num_buckets: int) -> int:
    """
    HU05: Função Hash customizada desenvolvida pela equipe (RN11).
    Mapeia uma palavra de entrada para um endereço válido de bucket [0..NB-1] (RN10 / CA12).

    Funcionamento do algoritmo (Fundamentação Teórica para o Critério 5):
    1. Seed Inicial: 618619 (número primo amplo para espalhamento inicial de bits).
    2. Bit Shifting & Multiplicação:
       A operação `(hash_val << 7) + hash_val + ord(char)` multiplica o valor anterior
       por 129 ((1 << 7) + 1 = 129) e adiciona o código ASCII do caractere.
       O fator 129 distribui muito bem permutações de letras em strings curtas e longas.
    3. Máscara de 32 bits (`& 0xFFFFFFFF`):
       Garante que o cálculo opere como um inteiro de 32 bits sem sinal (unsigned 32-bit),
       evitando crescimento arbitrário em memória e mantendo determinismo (RNF05).
    4. Mapeamento Modular (`% num_buckets`):
       Garante que o endereço resultante caia rigorosamente no intervalo [0, num_buckets - 1].
    """
    if num_buckets <= 0:
        raise ValueError("A quantidade de buckets deve ser maior que zero.")

    hash_val = 618619
    for char in word:
        hash_val = (hash_val << 7) + hash_val + ord(char)
        hash_val = hash_val & 0xFFFFFFFF
    return hash_val % num_buckets
