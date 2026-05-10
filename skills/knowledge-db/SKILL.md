---
name: knowledge-db
description: Qdrant-backed Knowledge DB CRUD with dedupe (content_hash) and forced provenance payload (source_url, citation, retrieved_at). Use when storing/retrieving knowledge chunks across wiki/papers/oss/dev_docs/code/notes/topics collections.
---

# knowledge-db

Reads and writes the Qdrant-backed Knowledge DB. All upserts enforce dedupe via `content_hash` and require source provenance fields. Use `kb_search` for retrieval (Wiki-First → KB-Second pattern), `kb_upsert` for storage.

Functions: kb_search, kb_upsert, kb_topic_register, kb_topic_list, kb_stats. See kb_tools.py.

Collections (12): wiki_entities, wiki_concepts, wiki_architecture, kb_papers, kb_oss_projects, kb_industry_solutions, kb_lessons_learned, kb_dev_docs, mythrill_code, chat_memory, personal_notes, topics.

Forced payload: source_url, content_hash, retrieved_at, citation, relevance_topics, language, embedding_model, confidence.
