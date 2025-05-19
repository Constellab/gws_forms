import pandas as pd
from gws_core import (ConfigSpecs, File, InputSpec, InputSpecs, JSONDict,
                      OutputSpec, OutputSpecs, StrParam, Task, TaskInputs,
                      TaskOutputs, task_decorator)


@task_decorator("ExcelFormFileToJsonDict", human_name="Excel Form File to Json Dict",
                short_description="Converts an Excel file containing form questions data to a JSON dictionary")
class ExcelFormFileToJsonDict(Task):

    input_specs: InputSpecs = InputSpecs({'excel_file': InputSpec(File, human_name="Excel file")})
    output_specs: OutputSpecs = OutputSpecs({'json_dict': OutputSpec(JSONDict, human_name="JSON dictionary")})
    config_specs: ConfigSpecs = ConfigSpecs({'language': StrParam(
        default_value='en', short_description="Language", allowed_values=['en', 'fr'])})

    def run(self, params, inputs: TaskInputs) -> TaskOutputs:

        excel_file_path = inputs['excel_file'].path

        # Read the Excel file into a DataFrame
        df = pd.read_excel(excel_file_path)

        # Create a list to hold the questions
        questions = []

        # Iterate over the rows of the DataFrame
        for _, row in df.iterrows():
            question_dict = {
                "section": row['Section'] if pd.notna(row['Section']) else "",
                "title": row['Title'] if pd.notna(row['Title']) else "",
                "question": row['Question'] if pd.notna(row['Question']) else "",
                "description": row['Description'] if pd.notna(row['Description']) else "",
                "response_type": row['Response Type'] if pd.notna(row['Response Type']) else "",
                "required": bool(row['Is Required']) if pd.notna(row['Is Required']) else False
            }

            # Handle optional fields like AllowedValued, MultiSelect, MinValue, MaxValue
            if pd.notna(row['Allowed Values']):
                question_dict['allowed_values'] = [val.strip() for val in row['Allowed Values'].split(',')]
            if pd.notna(row['Min Value']):
                question_dict['min_value'] = row['Min Value']
            if pd.notna(row['Max Value']):
                question_dict['max_value'] = row['Max Value']
            if pd.notna(row['MultiSelect']):
                question_dict['multiselect'] = bool(row['MultiSelect'])

            # Append the question to the list
            questions.append(question_dict)

        # Create the final dictionary
        data = {"language": params['language'], "questions": questions}

        return {'json_dict': JSONDict(data)}
