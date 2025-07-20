from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from src.domain.models.message import Message


class Channel(ABC):
    @abstractmethod
    def send_message(self, to: str, message: str) -> Tuple[bool, Dict[str, Any]]:
        """Send a message to a recipient.

        Args:
            to (str): Recipient ID/number
            message (str): Message content

        Returns:
            Tuple[bool, Dict[str, Any]]: Success status and response data
        """
        pass

    @abstractmethod
    def send_template_message(self, to: str, template_name: str, template_parameters: List[str]) -> Tuple[bool, Dict[str, Any]]:
        """Send a template message to a recipient.

        Args:
            to (str): Recipient ID/number
            template_name (str): Name of the template
            template_parameters (List[str]): Parameters for the template

        Returns:
            Tuple[bool, Dict[str, Any]]: Success status and response data
        """
        pass

    @abstractmethod
    def parse_message(self, data: Dict[str, Any]) -> Optional[Message]:
        """Parse incoming message data into a Message object.

        Args:
            data (Dict[str, Any]): Raw message data

        Returns:
            Optional[Message]: Parsed message or None if parsing fails
        """
        pass

    @abstractmethod
    def verify_webhook(self, request: Any) -> Tuple[Any, int]:
        """Verify webhook request from the channel provider.

        Args:
            request: Webhook request object

        Returns:
            Tuple[Any, int]: Response data and HTTP status code
        """
        pass
