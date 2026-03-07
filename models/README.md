# Models

Binary model artifacts needed by the pipeline. **Not tracked in git** — downloaded at build time or manually.

## lid.176.ftz

FastText language identification model (176 languages).

**Used by:** `FastTextModelResource` (`src/linker/resources/fasttext_resource.py`)
**Config:** `FASTTEXT_MODEL_PATH` env var (default: `models/lid.176.ftz`)

### Download

```bash
curl -o models/lid.176.ftz https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz
```

### Usage

```python
from fasttext import load_model
m = load_model("models/lid.176.ftz")
lang = m.predict("some text")[0][0].replace("__label__", "")
```
