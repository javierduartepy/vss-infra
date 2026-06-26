class PagesModule:
    def __init__(self):
        self.module_name = "VSS Pages Conector"
        self.template_bound = "base.html"

    def get_status(self):
        """Retorna el estado del renderizador de vistas."""
        return {"status": "READY", "template": self.template_bound}
