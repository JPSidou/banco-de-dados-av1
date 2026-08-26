import math
from typing import overload


class Bucket:
    def __init__(self, bucket_size):
        self.bucket_size = bucket_size
        self.registers = [None] * self.bucket_size
        self.overflow = None #inicia como registers e adiciona mais valores quando registers encher
        """
        talvez essa do overflow nao tenha sido a melhor forma de fazer. o que quero é que no fim de registers tenha,
        após o n'ésimo registro, um ponteiro indicando a lista de overflow. Para isso, acho que preciso usar uma
        linked list com os n espaços + 1 espaço que é a lista de overflow.
        """



    def insert(self, position, register):
        try:
            if len(self.registers) == self.bucket_size:
                self.overflow =  Bucket(self.bucket_size)
                self.overflow.insert(0, register)
            elif len(self.registers) > self.bucket_size:
                self.overflow.insert((len(self.overflow)-1), register)
            else:
                self.registers[position] = register
        except IndexError:
            print("Index out of bounds")
    """
    #estou errado aqui e no insert de overflow anterior. nao da pra rodar len no self overflow 
    pois ele é um Objeto, não uma lista. Para conseugir fazer isso corretamente, tenho que rodar o len
    em cima da lista de registros do objeto overflow.
    Além disso, acho que não é correto fazer o overflow ser um objeto do tipo Bucket, pois pode ter o caso de encher
    o overflow e aí vou ter que criar outro overflow pro overlow? será qu faz sentid?e
    """
    def getWord(self, position):
        try:
            return self.registers[position]
        except IndexError:
            print("Index out of bounds")

