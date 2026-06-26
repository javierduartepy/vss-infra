import time

class VSSProvider:
    def __init__(self):
        # Nombre completo de producción real
        self.provider_name = "Microsoft Software Shadow Copy Provider (VSS_PROV_18)"

    def create_shadow_copy_set(self, id_dato, contenido):
        time.sleep(0.5) 
        return {
            "id_dato": id_dato,
            "vss_provider": self.provider_name,
            "contenido_congelado": f"{contenido} [Shadow Copy Block]",
        }
