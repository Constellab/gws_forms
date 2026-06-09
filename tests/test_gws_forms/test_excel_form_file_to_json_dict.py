import os

from gws_core import BaseTestCase, File, JSONDict, TaskRunner
from gws_forms.excel_form_file_to_json_dict.excel_form_file_to_json_dict import (
    ExcelFormFileToJsonDict,
)

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "..", "testdata")


class TestExcelFormFileToJsonDict(BaseTestCase):
    """Unit tests for the ExcelFormFileToJsonDict task."""

    def test_basic_conversion_english(self):
        """Test that an Excel form file is correctly converted to a JSON dict in English."""
        excel_path = os.path.join(TESTDATA_DIR, "form_questions.xlsx")

        runner = TaskRunner(
            task_type=ExcelFormFileToJsonDict,
            inputs={"excel_file": File(path=excel_path)},
            params={"language": "en"},
        )
        outputs = runner.run()

        self.assertIsNotNone(outputs["json_dict"])
        result: JSONDict = outputs["json_dict"]
        data = result.get_data()

        # Top-level structure
        self.assertIn("language", data)
        self.assertIn("questions", data)
        self.assertEqual(data["language"], "en")

        questions = data["questions"]
        self.assertEqual(len(questions), 5)

    def test_basic_conversion_french(self):
        """Test that the language parameter is correctly propagated."""
        excel_path = os.path.join(TESTDATA_DIR, "form_questions.xlsx")

        runner = TaskRunner(
            task_type=ExcelFormFileToJsonDict,
            inputs={"excel_file": File(path=excel_path)},
            params={"language": "fr"},
        )
        outputs = runner.run()

        data = outputs["json_dict"].get_data()
        self.assertEqual(data["language"], "fr")

    def test_question_fields(self):
        """Test that each question has the expected base fields."""
        excel_path = os.path.join(TESTDATA_DIR, "form_questions.xlsx")

        runner = TaskRunner(
            task_type=ExcelFormFileToJsonDict,
            inputs={"excel_file": File(path=excel_path)},
            params={"language": "en"},
        )
        outputs = runner.run()

        questions = outputs["json_dict"].get_data()["questions"]
        required_fields = {
            "section",
            "title",
            "question",
            "description",
            "response_type",
            "required",
        }

        for q in questions:
            for field in required_fields:
                self.assertIn(field, q, msg=f"Field '{field}' missing in question: {q}")

    def test_first_question_values(self):
        """Test the content of the first question row."""
        excel_path = os.path.join(TESTDATA_DIR, "form_questions.xlsx")

        runner = TaskRunner(
            task_type=ExcelFormFileToJsonDict,
            inputs={"excel_file": File(path=excel_path)},
            params={"language": "en"},
        )
        outputs = runner.run()

        first_q = outputs["json_dict"].get_data()["questions"][0]
        self.assertEqual(first_q["section"], "Personal Info")
        self.assertEqual(first_q["title"], "Name")
        self.assertEqual(first_q["question"], "What is your name?")
        self.assertEqual(first_q["response_type"], "text")
        self.assertTrue(first_q["required"])

    def test_optional_fields_allowed_values(self):
        """Test that allowed_values is correctly parsed from comma-separated string."""
        excel_path = os.path.join(TESTDATA_DIR, "form_questions.xlsx")

        runner = TaskRunner(
            task_type=ExcelFormFileToJsonDict,
            inputs={"excel_file": File(path=excel_path)},
            params={"language": "en"},
        )
        outputs = runner.run()

        questions = outputs["json_dict"].get_data()["questions"]

        # 4th question (index 3) is the "Smoker" select with allowed_values yes/no
        smoker_q = questions[3]
        self.assertIn("allowed_values", smoker_q)
        self.assertIn("yes", smoker_q["allowed_values"])
        self.assertIn("no", smoker_q["allowed_values"])

    def test_optional_fields_min_max_value(self):
        """Test that min_value and max_value are parsed for numeric questions."""
        excel_path = os.path.join(TESTDATA_DIR, "form_questions.xlsx")

        runner = TaskRunner(
            task_type=ExcelFormFileToJsonDict,
            inputs={"excel_file": File(path=excel_path)},
            params={"language": "en"},
        )
        outputs = runner.run()

        questions = outputs["json_dict"].get_data()["questions"]

        # 2nd question (index 1) is "Age" with min=0 max=120
        age_q = questions[1]
        self.assertIn("min_value", age_q)
        self.assertIn("max_value", age_q)
        self.assertEqual(age_q["min_value"], 0)
        self.assertEqual(age_q["max_value"], 120)

    def test_optional_fields_multiselect(self):
        """Test that multiselect field is correctly parsed."""
        excel_path = os.path.join(TESTDATA_DIR, "form_questions.xlsx")

        runner = TaskRunner(
            task_type=ExcelFormFileToJsonDict,
            inputs={"excel_file": File(path=excel_path)},
            params={"language": "en"},
        )
        outputs = runner.run()

        questions = outputs["json_dict"].get_data()["questions"]

        # 5th question (index 4) is "Favorite Color" with multiselect=True
        color_q = questions[4]
        self.assertIn("multiselect", color_q)
        self.assertTrue(color_q["multiselect"])

    def test_questions_without_optional_fields(self):
        """Test that optional fields are absent when not set in the Excel file."""
        excel_path = os.path.join(TESTDATA_DIR, "form_questions.xlsx")

        runner = TaskRunner(
            task_type=ExcelFormFileToJsonDict,
            inputs={"excel_file": File(path=excel_path)},
            params={"language": "en"},
        )
        outputs = runner.run()

        questions = outputs["json_dict"].get_data()["questions"]

        # 1st question (index 0) is "Name" (text) - no optional fields
        name_q = questions[0]
        self.assertNotIn("allowed_values", name_q)
        self.assertNotIn("min_value", name_q)
        self.assertNotIn("max_value", name_q)
        self.assertNotIn("multiselect", name_q)

    def test_minimal_form(self):
        """Test conversion of a minimal form with no optional columns filled."""
        excel_path = os.path.join(TESTDATA_DIR, "form_minimal.xlsx")

        runner = TaskRunner(
            task_type=ExcelFormFileToJsonDict,
            inputs={"excel_file": File(path=excel_path)},
            params={"language": "en"},
        )
        outputs = runner.run()

        data = outputs["json_dict"].get_data()
        self.assertEqual(len(data["questions"]), 2)

        q1 = data["questions"][0]
        self.assertEqual(q1["title"], "Q1")
        self.assertTrue(q1["required"])

        q2 = data["questions"][1]
        self.assertEqual(q2["title"], "Q2")
        self.assertFalse(q2["required"])
