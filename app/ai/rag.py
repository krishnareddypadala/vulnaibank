"""Simple RAG (Retrieval-Augmented Generation) implementation.

DELIBERATE VULNERABILITY (LLM08): No access controls on document store.
Any user can upload documents that affect all users' AI interactions.
No validation or sanitization of uploaded content.
"""

import json
import numpy as np
from app.models import db, Document


def get_rag_context(query, ai_client=None, max_results=3):
    """Retrieve relevant documents for the query.

    DELIBERATE VULNERABILITY (LLM08): Returns ALL documents regardless of
    user ownership. Poisoned documents affect all queries.
    """
    documents = Document.query.all()
    if not documents:
        return ''

    # Try embedding-based retrieval
    if ai_client:
        try:
            query_embedding = ai_client.embed(query)
            scored_docs = []
            for doc in documents:
                doc_embedding = ai_client.embed(doc.content[:500])
                score = cosine_similarity(query_embedding, doc_embedding)
                scored_docs.append((score, doc))

            scored_docs.sort(key=lambda x: x[0], reverse=True)
            top_docs = scored_docs[:max_results]

            context_parts = []
            for score, doc in top_docs:
                context_parts.append(
                    f"[Document: {doc.filename} | Relevance: {score:.2f}]\n{doc.content}"
                )
            return '\n\n---\n\n'.join(context_parts)
        except Exception:
            pass

    # Fallback: keyword matching (no embeddings)
    query_words = set(query.lower().split())
    scored_docs = []
    for doc in documents:
        doc_words = set(doc.content.lower().split())
        overlap = len(query_words & doc_words)
        scored_docs.append((overlap, doc))

    scored_docs.sort(key=lambda x: x[0], reverse=True)
    top_docs = scored_docs[:max_results]

    context_parts = []
    for score, doc in top_docs:
        context_parts.append(f"[Document: {doc.filename}]\n{doc.content}")
    return '\n\n---\n\n'.join(context_parts)


def cosine_similarity(vec_a, vec_b):
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def add_document(filename, content, user_id=None, doc_type='user_upload'):
    """Add a document to the knowledge base.

    DELIBERATE VULNERABILITY (LLM08): No content validation,
    no access controls, no sanitization.
    """
    doc = Document(
        user_id=user_id,
        filename=filename,
        content=content,
        doc_type=doc_type
    )
    db.session.add(doc)
    db.session.commit()
    return doc
