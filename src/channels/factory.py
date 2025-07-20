from typing import Optional
import os

from src.channels.jelou import JelouChannel
from src.channels.channel import Channel


class ChannelFactory:
    @staticmethod
    def create_channel(provider: str) -> Optional[Channel]:
        """Create a channel instance based on the provider.

        Args:
            provider (str): Channel provider name ('meta', 'jelou')
            **kwargs: Additional arguments for channel initialization

        Returns:
            Optional[Channel]: Channel instance or None if provider not supported
        """

        if provider.lower() == "jelou":
            api_key = os.getenv("JELOU_API_KEY")
            bot_id = os.getenv("JELOU_BOT_ID")

            if all([api_key, bot_id]):
                return JelouChannel(api_key=api_key, bot_id=bot_id)

        return None
