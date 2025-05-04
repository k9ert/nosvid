"""
Result class for standardizing operation responses
"""

from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar("T")


class Result(Generic[T]):
    """
    A standardized result object for operations

    Attributes:
        success (bool): Whether the operation was successful
        data (Optional[T]): The data returned by the operation (if successful)
        error (Optional[str]): Error message (if unsuccessful)
        metadata (Dict[str, Any]): Additional metadata about the operation
        timestamp (str): ISO-formatted timestamp of when the result was created
    """

    def __init__(
        self,
        success: bool,
        data: Optional[T] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a Result object

        Args:
            success: Whether the operation was successful
            data: The data returned by the operation (if successful)
            error: Error message (if unsuccessful)
            metadata: Additional metadata about the operation
        """
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()

    @classmethod
    def success(cls, data: T, metadata: Optional[Dict[str, Any]] = None) -> "Result[T]":
        """
        Create a successful result

        Args:
            data: The data returned by the operation
            metadata: Additional metadata about the operation

        Returns:
            A successful Result object
        """
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def failure(
        cls, error: str, metadata: Optional[Dict[str, Any]] = None
    ) -> "Result[T]":
        """
        Create a failed result

        Args:
            error: Error message
            metadata: Additional metadata about the operation

        Returns:
            A failed Result object
        """
        return cls(success=False, error=error, metadata=metadata)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization

        Returns:
            Dictionary representation of the Result
        """
        result = {
            "success": self.success,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

        if self.data is not None:
            # Handle dataclasses and objects with to_dict method
            if hasattr(self.data, "to_dict") and callable(
                getattr(self.data, "to_dict")
            ):
                result["data"] = self.data.to_dict()
            # Handle lists of objects with to_dict method
            elif isinstance(self.data, list) and all(
                hasattr(item, "to_dict") and callable(getattr(item, "to_dict"))
                for item in self.data
            ):
                result["data"] = [item.to_dict() for item in self.data]
            # Handle dictionaries with values that have to_dict method
            elif isinstance(self.data, dict) and all(
                hasattr(value, "to_dict") and callable(getattr(value, "to_dict"))
                for value in self.data.values()
            ):
                result["data"] = {
                    key: value.to_dict() for key, value in self.data.items()
                }
            else:
                result["data"] = self.data

        if self.error is not None:
            result["error"] = self.error

        return result
