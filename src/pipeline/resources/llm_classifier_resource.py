import logging
import json
import torch
from dagster import ConfigurableResource
from pydantic import PrivateAttr
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

class LLMClassifierResource(ConfigurableResource):
    device: str = "cpu" # Default to cpu, can be mps or cuda
    model_id: str = "Qwen/Qwen2.5-1.5B-Instruct"
    _pipeline = PrivateAttr(default=None)

    def get_pipeline(self):
        if self._pipeline is None:
            print(f"LLMResource: Loading model '{self.model_id}' on {self.device}...", flush=True)
            
            # 1. Load model and tokenizer
            model = AutoModelForCausalLM.from_pretrained(
                self.model_id, 
                device_map=self.device, 
                dtype="auto"
            )
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_id
            )

            # 2. Create text generation pipeline
            self._pipeline = pipeline(
                "text-generation", 
                model=model, 
                tokenizer=tokenizer
            )
            print("LLMResource: Model loaded successfully.", flush=True)
            
        return self._pipeline

    def classify_project(self, title: str, project_context: str, categories: list[str], domains: list[str]) -> dict:
        """
        Takes a project (title + rich context) and a list of valid categories/domains.
        Returns a Dict (parsed JSON) with the classification.
        """
        pipe = self.get_pipeline()

        # Construct prompt formatted for Phi-3
        # Truncate context to 6000 chars
        truncated_context = (project_context or "")[:6000] 
        
        # Categories and Domains formatting
        cats_str = ", ".join(categories)
        doms_str = ", ".join(domains)

        messages = [
            {
                "role": "system", 
                "content": (
                    "You are an expert technical classifier. "
                    "Your goal is to categorize a GitHub project based on its context (Title, Description, Topics, Readme). "
                    "You must choose categories and domains that correspond the most to the project from the provided lists.\n"
                    f"Allowed Categories: [{cats_str}]\n"
                    f"Allowed Domains: [{doms_str}]\n"
                    "Output STRICT JSON format only: {\"category\": \"...\", \"domain\": \"...\", \"tech_stack\": [\"...\"], \"use_case\": \"...\"}"
                )
            },
            {
                "role": "user", 
                "content": f"Title: {title}\n\nProject Context:\n{truncated_context}"
            }
        ]

        # Generation
        outputs = pipe(
            messages, 
            max_new_tokens=500, 
            return_full_text=False,
            do_sample=False, # Deterministic
            temperature=0.0
        )
        
        generated_text = outputs[0]['generated_text']
        
        # Cleanup to retrieve only JSON
        clean_json = generated_text.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(clean_json)
        except json.JSONDecodeError:
            print(f"JSON parsing error for project {title}. Raw JSON: {clean_json}")
            # Fallback trivial or return error
            return {"error": "parsing_failed", "raw": generated_text}
