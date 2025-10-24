from abc import ABC, abstractmethod
import logging

class BaseSource(ABC):
    """
    Classe base abstrata para todas as fontes de entropia.
    Define a interface que cada fonte deve implementar.
    """
    def __init__(self):
        self.name = self.__class__.__name__
        # O logger será configurado pelo harvester principal,
        # mas o obtemos aqui para uso na classe.
        self.logger = logging.getLogger(f"harvester.source.{self.name}")

    @abstractmethod
    def get_entropy(self) -> bytes | None:
        """Coleta dados da fonte e os retorna como bytes."""
        pass
