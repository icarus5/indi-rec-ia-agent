from src.integrations.data_provider import DataProvider
from src.integrations.indi.provider import IndiProvider


class DataProviderFactory:
    """
    Factory class for creating data providers based on the provider type.
    """
    @staticmethod
    def get_data_provider(provider_type: str) -> DataProvider:
        """
        Get a data provider based on the provider type.
        """
        if provider_type == "indi":
            return IndiProvider()
        
        raise ValueError(f"Unknown provider type: {provider_type}")
