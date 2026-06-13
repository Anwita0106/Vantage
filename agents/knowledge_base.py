"""
knowledge_base.py

Foundry IQ retrieval wrapper.

In production, this would query a Foundry IQ knowledge base (vector
search over the markdown documents in /knowledge_base) and return
grounded passages with citations.

Local retrieval fallback used for offline execution,
testing, and public deployment environments,
this module performs simple keyword-based retrieval directly over the
markdown files, returning the same shape of result. Swapping in real
Foundry IQ search later only requires changing the implementation of
`search()` -- the calling agents are unaffected.
"""

import os
import re

KB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base")


def _load_all_docs():
    docs = {}
    for filename in os.listdir(KB_DIR):
        if filename.endswith(".md"):
            with open(os.path.join(KB_DIR, filename), "r") as f:
                docs[filename] = f.read()
    return docs


_DOCS = _load_all_docs()


def _split_sections(text):
    """Split a markdown doc into (heading, content) sections by ## headers."""
    sections = []
    current_heading = "Overview"
    current_content = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_content:
                sections.append((current_heading, "\n".join(current_content).strip()))
            current_heading = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections.append((current_heading, "\n".join(current_content).strip()))

    return sections


def search(query: str, top_k: int = 3):
    """
    Simple keyword-overlap retrieval over the knowledge base markdown docs.

    Returns a list of dicts:
        {
            "document": filename,
            "doc_id": extracted Document ID,
            "section": heading,
            "content": section text,
            "score": overlap score
        }

    This mirrors the shape of a Foundry IQ grounded retrieval result
    (source document + section + content), enabling agents to cite
    specific documents and sections in their output.
    """
    query_terms = set(re.findall(r"\w+", query.lower()))
    results = []

    for filename, text in _DOCS.items():
        doc_id_match = re.search(r"\*\*Document ID:\*\*\s*(\S+)", text)
        doc_id = doc_id_match.group(1) if doc_id_match else filename

        for heading, content in _split_sections(text):
            section_terms = set(re.findall(r"\w+", (heading + " " + content).lower()))
            overlap = len(query_terms & section_terms)
            if overlap > 0:
                results.append({
                    "document": filename,
                    "doc_id": doc_id,
                    "section": heading,
                    "content": content,
                    "score": overlap,
                })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]


def get_document(filename: str) -> str:
    """Return the full text of a knowledge base document by filename."""
    return _DOCS.get(filename, "")


if __name__ == "__main__":
    results = search("intern admin access critical resource dormant")
    for r in results:
        print(f"[{r['doc_id']}] {r['section']} (score={r['score']})")
        print(r["content"][:200])
        print()
