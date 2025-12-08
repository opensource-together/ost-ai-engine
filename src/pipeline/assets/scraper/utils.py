import typing as _t
import requests
from urllib.parse import urlparse

def _extract_owner_repo(repo_url: str) -> _t.Optional[_t.Tuple[str, str]]:
	try:
		p = urlparse(repo_url)
		parts = [seg for seg in p.path.split("/") if seg]
		if len(parts) >= 2:
			return parts[0], parts[1].replace('.git', '')
	except Exception as e:
		print(f"Error extracting owner/repo from {repo_url}: {e}")
		pass
	return None

def _fetch_repo_languages(owner: str, repo: str, headers: dict, session: requests.Session) -> _t.List[str]:
	out = []
	try:
		lang_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
		r = session.get(lang_url, headers=headers, timeout=10)
		if r.ok:
			out = list(r.json().keys())
		elif r.status_code == 403:
			print(f"RATE LIMIT EXCEEDED (403) fetching languages for {owner}/{repo}")
			# Optionally raise to fail the asset, or just log
		else:
			print(f"Failed to fetch languages for {owner}/{repo}: {r.status_code} - {r.text[:100]}")
	except Exception as e:
		print(f"Error fetching languages for {owner}/{repo}: {e}")
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
		elif r.status_code == 403:
			print(f"RATE LIMIT EXCEEDED (403) fetching topics for {owner}/{repo}")
		else:
			print(f"Failed to fetch topics for {owner}/{repo}: {r.status_code} - {r.text[:100]}")
	except Exception as e:
		print(f"Error fetching topics for {owner}/{repo}: {e}")
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
		elif r.status_code == 403:
			print(f"RATE LIMIT EXCEEDED (403) fetching readme (raw) for {owner}/{repo}")
		else:
			print(f"Failed to fetch readme (raw) for {owner}/{repo}: {r.status_code}")
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
			elif r2.status_code == 403:
				print(f"RATE LIMIT EXCEEDED (403) fetching readme (json) for {owner}/{repo}")
			else:
				print(f"Failed to fetch readme (json) for {owner}/{repo}: {r2.status_code} - {r2.text[:100]}")
	except Exception as e:
		print(f"Error fetching readme for {owner}/{repo}: {e}")
		pass
	return out
