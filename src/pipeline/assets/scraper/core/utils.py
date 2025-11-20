import typing as _t
import requests
from urllib.parse import urlparse

# Generic helper: resolve a model attribute on the Prisma client using common
# candidate names (snake_case, camelCase, PascalCase). Returns the model
# object or None.
def _find_model(client_obj, candidates: list[str]):
	for n in candidates:
		if hasattr(client_obj, n):
			return getattr(client_obj, n)
	return None

def _extract_owner_repo(repo_url: str) -> _t.Optional[_t.Tuple[str, str]]:
	try:
		p = urlparse(repo_url)
		parts = [seg for seg in p.path.split("/") if seg]
		if len(parts) >= 2:
			return parts[0], parts[1].replace('.git', '')
	except Exception:
		pass
	return None

def _cosine_sim(a, b) -> float:
	# Import numpy lazily to avoid loading its C extensions at module import
	# time which can cause SIGBUS when using a multiprocess/fork executor.
	import numpy as np
	return float(np.dot(a, b))

def _fetch_repo_languages(owner: str, repo: str, headers: dict, session: requests.Session) -> _t.List[str]:
	out = []
	try:
		lang_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
		r = session.get(lang_url, headers=headers, timeout=10)
		if r.ok:
			out = list(r.json().keys())
	except Exception:
		pass
	return out

def _fetch_repo_topics(owner: str, repo: str, headers: dict, session: requests.Session) -> _t.List[str]:
	out = []
	try:
		topics_url = f"https://api.github.com/repos/{owner}/{repo}/topics"
		r = session.get(topics_url, headers={**headers, "Accept": "application/vnd.github.mercy-preview+json"}, timeout=10)
		if r.ok:
			json_data = r.json()
			out = json_data.get("names") or json_data.get("topics") or []
	except Exception:
		pass
	return out

def _fetch_readme(owner: str, repo: str, headers: dict, session: requests.Session) -> str:
	out = ""
	try:
		readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
		# Prefer raw content when possible
		r = session.get(readme_url, headers={**headers, "Accept": "application/vnd.github.v3.raw"}, timeout=10)
		if r.ok:
			out = r.text
		else:
			# fallback to JSON which may contain base64 encoded content
			r2 = session.get(readme_url, headers=headers, timeout=10)
			if r2.ok:
				try:
					j = r2.json()
					content = j.get("content")
					encoding = j.get("encoding")
					if content and encoding == "base64":
						import base64

						out = base64.b64decode(content.encode("utf-8")).decode("utf-8", errors="ignore")
				except Exception:
					out = ""
	except Exception:
		pass
	return out
