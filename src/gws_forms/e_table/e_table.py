import json
from typing import List, Dict, Any


class Etable:
    TEXT = "text"
    NUMERIC = "numeric"
    DATE = "date"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    LIST = "list"
    LIST_OBJECT = "list<object>"

    def __init__(self, json_path: str = None):
        self.json_path = json_path
        if self.json_path:
            self.data = self._load_json()
            self.processed_data = self._process_data()
        else:
            self.data = {"data": []}
            self.processed_data = []

    def _load_json(self) -> Dict:
        """Load JSON data from file."""
        try:
            with open(self.json_path, 'r', encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            raise ValueError(f"The file at {self.json_path} was not found.")
        except json.JSONDecodeError:
            raise ValueError(f"The file at {self.json_path} is not a valid JSON.")

    def _process_data(self) -> List[Dict[str, Any]]:
        """Process the data with correct types. To be implemented by subclasses."""
        return []

    def download(self, file_format: str = "csv") -> str:
        """Download the DataFrame as CSV or JSON."""
        if file_format == "csv":
            # Create CSV string manually
            if not self.processed_data:
                return ""
            headers = list(self.processed_data[0].keys())
            csv_lines = [",".join(headers)]
            for item in self.processed_data:
                row = [str(item.get(header, "")) for header in headers]
                csv_lines.append(",".join(row))
            return "\n".join(csv_lines)
        elif file_format == "json":
            return json.dumps(self.processed_data, indent=2)
