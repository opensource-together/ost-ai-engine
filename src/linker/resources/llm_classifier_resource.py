import logging
import json
import os
from openai import OpenAI
from dagster import ConfigurableResource

class LLMClassifierResource(ConfigurableResource):
    api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    model_id: str = "mistralai/mistral-small-3.2-24b-instruct"

    def classify_project(self, title: str, project_context: str, categories: list[str], domains: list[str]) -> dict:
        """
        Takes a project in context (title, description, topics, readme) and the list of valid categories/domains from OST.
        Returns a Dict with the classification.
        """
        if not self.api_key:
            logging.error("LLMResource: No OPENROUTER_API_KEY found in environment variables.")
            return {"error": "no_api_key"}

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )
        
        # Truncate context to keep it snappy and cheap
        truncated_context = (project_context or "")[:8000] 

        cats_str = ", ".join(categories)
        doms_str = ", ".join(domains)

        system_prompt = (
            "You are an expert technical classifier. "
            "Analyze the GitHub project context (Title, Description, Topics, Readme) and classify it.\n"
            f"1. Assign the single most relevant Category from: [{cats_str}]\n"
            f"2. Assign the single most relevant Domain from: [{doms_str}]\n"
            "If unsure, pick the closest match or null.\n"
            "Response format: JSON ONLY, no markdown, no explanation.\n"
            "Example: {\"category\": \"Framework\", \"domain\": \"Web Development\"}"
        )

        user_content = f"Title: {title}\n\nProject Context:\n{truncated_context}"

        try:
            completion = client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            content = completion.choices[0].message.content
            
            # Clean up potential markdown code blocks 
            clean_json = content.replace("```json", "").replace("```", "").strip()
            
            return json.loads(clean_json)

        except Exception as e:
            logging.error(f"OpenRouter API Error for {title}: {e}")
            return {"error": "api_error", "details": str(e)}
