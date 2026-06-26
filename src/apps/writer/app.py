import random

class VSSWriter:
    def __init__(self):
        self.is_frozen = False

    def freeze(self):
        self.is_frozen = True
        return "🛑 Writer: I/O de la base de datos CONGELADO. Escrituras retenidas en caché."

    def thaw(self):
        self.is_frozen = False
        return "🟢 Writer: I/O LIBERADO. Vaciando transacciones acumuladas en disco."

    def simular_escritura(self):
        if self.is_frozen:
            return None
        return {"monto": round(random.uniform(10.0, 1500.0), 2), "estado": "PROCESADO"}
