project:
  goal: generate a clean, handover-ready prototype for a social-media moderation and persuasion system

pipeline:
  stages:
    - ingestion: POST /ingest receives posts from a mock stream
    - classifier_binary: decides whether a post is harmful
    - classifier_typed:  if harmful, picks a harm type and a strategy hint
    - rag:               optional retrieval of corpus snippets by harm type
    - responder:         picks a responder by harm type and produces a reply draft
    - moderation:        reply drafts may be queued for a human reviewer
    - session:           depressive / self-harm harm types spawn multi-turn counseling sessions

coding:
  rules:
    - keep files small and focused
    - avoid global state
    - prefer simple functions over classes unless necessary
    - write docstrings for every function

architecture:
  rules:
    - separate classifier, responder, and pipeline orchestration
    - no LLM calls inside classifier fallbacks, store, or api layers
    - no hardcoded prompts inside business logic; prompts live in app/prompts/*.yaml and are loaded by key
    - llm access always goes through llm.base.LLMClient; never instantiate vendor SDKs in business logic
    - responder dispatch is a registry keyed by HarmType; there is no separate router module

modules:
  owners:
    classifier_binary: member-A
    classifier_typed:  member-B
    rag:               member-C
    llm_rlhf:          member-D
    integration:       owner
  contract: each module implements the Protocol in its base.py; dummy.py provides a working stub so the pipeline runs end-to-end before real models land

moderation:
  rules:
    - every reply draft is persisted before it is published
    - decisions are audited (who, when, action, before text, after text)
    - the moderator console can view full label history per post

output:
  rules:
    - always explain file structure before writing code
    - do not generate unnecessary features
