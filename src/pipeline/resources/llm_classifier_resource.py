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
            
            # 1. Chargement du modèle et du tokenizer
            model = AutoModelForCausalLM.from_pretrained(
                self.model_id, 
                device_map=self.device, 
                dtype="auto"
            )
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_id
            )

            # 2. Création de la pipeline de génération de texte
            self._pipeline = pipeline(
                "text-generation", 
                model=model, 
                tokenizer=tokenizer
            )
            print("LLMResource: Model loaded successfully.", flush=True)
            
        return self._pipeline

    def classify_project(self, title: str, project_context: str, categories: list[str], domains: list[str]) -> dict:
        """
        Prend un projet (titre + contexte riche) et une liste de catégories/domaines valides.
        Retourne un Dict (JSON parsé) avec la classification.
        """
        pipe = self.get_pipeline()

        # Construction du Prompt formaté pour Phi-3
        # On tronque à 6000 chars pour le contexte
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

        # Génération
        outputs = pipe(
            messages, 
            max_new_tokens=500, 
            return_full_text=False,
            do_sample=False, # Déterministe
            temperature=0.0
        )
        
        generated_text = outputs[0]['generated_text']
        
        # Nettoyage pour récupérer uniquement le JSON
        clean_json = generated_text.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(clean_json)
        except json.JSONDecodeError:
            print(f"Erreur de parsing JSON sur le projet {title}. JSON brut: {clean_json}")
            # Fallback trivial or return error
            return {"error": "parsing_failed", "raw": generated_text}
