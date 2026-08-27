import math
from typing import overload


class Bucket:
    def __init__(self, bucket_size):
        self.bucket_size = bucket_size
        self.registers = []
        self.overflow = None #inicia como registers e adiciona mais valores quando registers encher


    def insert(self, key, page_id):
        try:
            if len(self.registers) == self.bucket_size: # limite máximo do bucket, agora é overflow!
                if(self.overflow != None): # Se o bucket do overflow já tiver sido criado, só insere
                    self.overflow.insert(key, page_id)
                else: # Senão, cria o bucket de overflow e insere o novo registro
                    self.overflow =  Bucket(self.bucket_size)
                    self.overflow.insert(key, page_id)
            elif len(self.registers) > self.bucket_size:
                self.overflow.insert(key, page_id)
            else:
                self.registers.append((key, page_id))
        except IndexError:
            print("Index out of bounds")

    def search(self, key):
        page_id = next(
            (r[1] for r in self.registers if r[0] == key),
            None
        )
        if self.overflow != None:
            return self.overflow.search(key)
        return None


