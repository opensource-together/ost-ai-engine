import typing as _t
import json
from pathlib import Path
# from .utils import _load_model as _load_sentence_model_unused # Removed invalid import 
# The original code had _load_model in assets.py. It uses sentence_transformers.
# Let's put _load_model here as it is specific to categorization/embeddings.

# Globals used by the sentence-transformers based mapping. Initialize here to avoid NameError and to make state explicit before any child process
_SENTENCE_MODEL = None
_CATEGORY_EMBS = None
_CATEGORIES = None

def _load_model():
	# lazy load global model
	global _SENTENCE_MODEL
	# Return already-loaded model if present
	if _SENTENCE_MODEL is not None:
		return _SENTENCE_MODEL

	# Import sentence-transformers normally inside the loader (fail-fast if missing)
	from sentence_transformers import SentenceTransformer
	_SENTENCE_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
	return _SENTENCE_MODEL

def _load_categories_and_embeddings(seed_json_path: str):
	global _CATEGORY_EMBS, _CATEGORIES
	# Fast fast-path when already computed
	if (_CATEGORY_EMBS is not None) and (_CATEGORIES is not None):
		return _CATEGORIES, _CATEGORY_EMBS
	p = Path(seed_json_path)
	cats = []
	if p.exists():
		try:
			cats = [c.get("name") for c in json.loads(p.read_text(encoding="utf-8")) if c.get("name")]
		except Exception:
			cats = []
	if not cats:
		cats = ["Other"]
	_CATEGORIES = cats
	# Require the sentence-transformers model to be present; fail fast if not.
	texts = [c for c in cats]
	model = _load_model()
	try:
		embs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
		_CATEGORY_EMBS = {cats[i]: embs[i] for i in range(len(cats))}
	except Exception as e:
		raise RuntimeError(f"Failed to compute category embeddings: {e}")
	return _CATEGORIES, _CATEGORY_EMBS

from .utils import _cosine_sim

def _map_topics_to_categories(topics: _t.List[str], seed_json_path: str, top_k: int = 2, thresh: float = 0.55) -> _t.List[str]:
	if not topics:
		return []
	# Require model and embeddings to be available; let exceptions propagate so the
	# caller sees a clear error instead of silently proceeding.
	model = _load_model()
	_, cat_embs = _load_categories_and_embeddings(seed_json_path)
	topic_embs = model.encode(topics, convert_to_numpy=True, normalize_embeddings=True)
	matches: set[str] = set()
	for te in topic_embs:
		best = []
		for name, ce in cat_embs.items():
			score = _cosine_sim(te, ce)
			best.append((score, name))
		best.sort(reverse=True, key=lambda x: x[0])
		for score, name in best[:top_k]:
			if score >= thresh:
				matches.add(name)
	return list(matches)

# Helper to compute embeddings for Category rows fetched from the DB.
# Returns (cat_objs, cat_embs) where cat_embs is a numpy array with one
# embedding per category in the same order as cat_objs.
def _get_db_category_embeddings(category_model, context):
	all_categories = category_model.find_many()
	cat_objs = list(all_categories or [])
	if not cat_objs:
		return [], None, None
	try:
		model = _load_model()
		cat_texts = [getattr(c, "name", "") for c in cat_objs]
		cat_embs = model.encode(cat_texts, convert_to_numpy=True, normalize_embeddings=True)
		return cat_objs, cat_embs, model
	except Exception as e:
		context.log.exception(f"_get_db_category_embeddings: failed to load model/compute embeddings: {e}")
		return cat_objs, None, None
