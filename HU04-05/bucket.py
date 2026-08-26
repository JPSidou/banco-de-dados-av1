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



    def insert(self, register):
        try:
            if len(self.registers) == self.bucket_size:
                if(self.overflow != None):
                    self.overflow.insert((len(self.overflow.registers)-1), register)
                else:
                    self.overflow =  Bucket(self.bucket_size)
                    self.overflow.insert(0, register)
            elif len(self.registers) > self.bucket_size:
                self.overflow.insert((len(self.overflow)-1), register)
            else:
                self.registers[len(self.registers)-1] = register
        except IndexError:
            print("Index out of bounds")

    def getWord(self, position):
        try:
            if position <= self.bucket_size:
                return self.registers[position]
            else:
                return self.overflow.getWord(position - self.bucket_size)
        except IndexError:
            print("Index out of bounds")


