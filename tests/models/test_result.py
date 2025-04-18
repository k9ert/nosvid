"""
Tests for the Result class
"""

import unittest
from dataclasses import dataclass
from src.nosvid.models.result import Result

@dataclass
class TestData:
    """Test data class for Result tests"""
    name: str
    value: int
    
    def to_dict(self):
        return {
            'name': self.name,
            'value': self.value
        }

class TestResult(unittest.TestCase):
    """Tests for the Result class"""
    
    def test_success_result(self):
        """Test creating a successful result"""
        data = "test data"
        result = Result.success(data)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data, data)
        self.assertIsNone(result.error)
        self.assertIsNotNone(result.timestamp)
    
    def test_failure_result(self):
        """Test creating a failed result"""
        error = "test error"
        result = Result.failure(error)
        
        self.assertFalse(result.success)
        self.assertIsNone(result.data)
        self.assertEqual(result.error, error)
        self.assertIsNotNone(result.timestamp)
    
    def test_metadata(self):
        """Test metadata in result"""
        metadata = {"key": "value"}
        result = Result.success("data", metadata)
        
        self.assertEqual(result.metadata, metadata)
    
    def test_to_dict_simple(self):
        """Test to_dict with simple data"""
        data = "test data"
        result = Result.success(data)
        result_dict = result.to_dict()
        
        self.assertTrue(result_dict["success"])
        self.assertEqual(result_dict["data"], data)
        self.assertIn("timestamp", result_dict)
        self.assertIn("metadata", result_dict)
    
    def test_to_dict_with_object(self):
        """Test to_dict with object that has to_dict method"""
        data = TestData("test", 123)
        result = Result.success(data)
        result_dict = result.to_dict()
        
        self.assertTrue(result_dict["success"])
        self.assertEqual(result_dict["data"], {"name": "test", "value": 123})
    
    def test_to_dict_with_list(self):
        """Test to_dict with list of objects that have to_dict method"""
        data = [TestData("test1", 123), TestData("test2", 456)]
        result = Result.success(data)
        result_dict = result.to_dict()
        
        self.assertTrue(result_dict["success"])
        self.assertEqual(result_dict["data"], [
            {"name": "test1", "value": 123},
            {"name": "test2", "value": 456}
        ])
    
    def test_to_dict_with_dict(self):
        """Test to_dict with dict of objects that have to_dict method"""
        data = {
            "item1": TestData("test1", 123),
            "item2": TestData("test2", 456)
        }
        result = Result.success(data)
        result_dict = result.to_dict()
        
        self.assertTrue(result_dict["success"])
        self.assertEqual(result_dict["data"], {
            "item1": {"name": "test1", "value": 123},
            "item2": {"name": "test2", "value": 456}
        })

if __name__ == "__main__":
    unittest.main()
