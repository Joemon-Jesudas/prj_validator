import json
import os
import time
from typing import Tuple, Dict, Any

class ContractAnalyzer:
    """
    Uses Azure OpenAI to analyze contract text according to the provided prompt template
    and return a JSON object matching the schema in the prompt.
    """

    def __init__(self, client):
        self.client = client
        self.model = os.getenv("AZURE_OPENAI_MODEL")

    def analyze(self, text: str) -> Tuple[Dict[str, Any], float, Dict[str,int]]:
        """
        Send the system prompt (from prompt_template.txt) and the contract text to the model.
        Returns (result_json, analysis_time_seconds).
        """
        # Load prompt template file (should be present in project root)
        prompt_path = os.path.join(os.getcwd(), "prompt_template.txt")
        if not os.path.exists(prompt_path):
            raise FileNotFoundError("prompt_template.txt not found in working directory.")

        legal_template_path = os.path.join(os.getcwd(), "legal_template.txt")
        if not os.path.exists(legal_template_path):
            raise FileNotFoundError("Legal template not found in working directory.")

        response_schema_path = os.path.join(os.getcwd(), "response_schema.json")
        if not os.path.exists(response_schema_path):
            raise FileNotFoundError("response_schema.json not found in working directory.")

        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()

        with open(legal_template_path, "r", encoding="utf-8") as f:
            legal_template = f.read()

        with open(response_schema_path, "r", encoding="utf-8") as f:
            response_schema = json.load(f)

        # Update system prompt to include legal template and response JSON
        system_prompt += "\n\n" + legal_template
        system_prompt += "\n\nReturn response as JSON object matching the following schema:\n" + json.dumps(response_schema, indent=4)
        print("Updated system prompt")

        user_message = f"""Please analyze the following contract document and extract the required information:
                        CONTRACT CONTENT:
                        ---
                        {text}
                        ---
                        Extract all required information according to the validation rules specified."""

        start_time = time.time()

        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=4096,
            temperature=0.3,
            model=self.model,
            response_format={"type": "json_object"}
        )

        analysis_time = time.time() - start_time

        content = response.choices[0].message.content
        if isinstance(content, (bytes, bytearray)):
            content = content.decode("utf-8")
        try:
            result_json = json.loads(content)
        except json.JSONDecodeError as e:
            # Provide helpful error if JSON not parseable
            raise ValueError(f"Model did not return valid JSON. Error: {str(e)}. Raw content: {content[:1000]}")

        #token statistics:
        usage = response.usage
        usage_stats = {
            "prompt_tokens":usage.prompt_tokens,
            "completion_tokens":usage.completion_tokens,
            "total_tokens":usage.total_tokens
        }

        return result_json, analysis_time,usage_stats