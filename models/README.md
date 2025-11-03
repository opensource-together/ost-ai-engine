
lid.176.ftz — FastText language identification model
===============================================

What
- A pre-trained FastText language identification model (the "lid.176" model supporting 176 languages).

Why it's in this repo
- The pipeline uses this model to detect the language of repository content and other text assets so it can tag, filter, or route data correctly during processing.

Where it's used
- Loaded by `src/pipeline/assets/core/assets.py` (calls `fasttext.load_model`); the default path in code is `/app/models/lid.176.ftz` and can be overridden via the `fasttext_model_path` configuration key.

How to update or replace the file
- Download the official model from fastText (see: https://fasttext.cc/docs/en/language-identification.html). The file to use is typically named `lid.176.ftz`.
- Place the file at `models/lid.176.ftz` in the project root (or point `fasttext_model_path` in your config to another location).
- Restart the pipeline/Dagster worker to pick up the new model.

Quick example
- Python:
	from fasttext import load_model
	m = load_model("models/lid.176.ftz")
	lang = m.predict("some text")[0][0].replace("__label__","")

Notes
- This is a binary model artifact; keep large model files out of git (see `.gitignore` — `models/*`).
