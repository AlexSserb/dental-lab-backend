import re

from django.conf import settings

from llm.service import call_text

from knowledge.services.retrieval_service import RetrievalService, RetrievedChunk

FEATURE = "knowledge_ask"
NO_ANSWER = "В базе знаний нет информации по этому вопросу."

SYSTEM_PROMPT = f"""Ты - помощник зуботехнической лаборатории. Отвечай на вопрос сотрудника, используя ТОЛЬКО \
фрагменты базы знаний из сообщения пользователя.
Правила:
1. Если в фрагментах нет ответа, ответь ровно: «{NO_ANSWER}» Ничего не придумывай.
2. После каждого утверждения указывай номер фрагмента в квадратных скобках, например [1] или [2].
3. Отвечай по-русски, кратко и по делу. Шаги и причины оформляй списком.
4. Не ссылайся на фрагменты, которых нет в списке."""

_CITATION_RE = re.compile(r"\[(\d+)\]")


class AnswerService:
    @staticmethod
    def ask(question: str, operation_type: str | None = None, user=None) -> dict:
        """
        RAG: retrieve candidates (hybrid search, then cross-encoder reranking when enabled), drop the fragments that
        are not relevant enough, and let the LLM answer from the rest. If nothing relevant is left the LLM is not
        called at all.
        """
        mode = "rerank" if settings.RERANK_ENABLED else "hybrid"
        retrieved = [
            item for item in RetrievalService.search(question, settings.KNOWLEDGE_TOP_K, operation_type, mode=mode)
            if AnswerService._is_relevant(item)
        ]
        if not retrieved:
            return {"answered": False, "answer": NO_ANSWER, "sources": []}

        answer = call_text(
            feature=FEATURE,
            system=SYSTEM_PROMPT,
            user_text=AnswerService._build_user_message(question, retrieved),
            user=user,
        )
        cited = {int(n) for n in _CITATION_RE.findall(answer)}
        sources = [
            {
                "number": number,
                "document_path": item.chunk.document.path,
                "document_title": item.chunk.document.title,
                "doc_type": item.chunk.document.doc_type,
                "operation_type": item.chunk.document.operation_type,
                "fragment": item.chunk.text,
                "distance": round(item.distance, 3),
                "cited": number in cited,
            }
            for number, item in enumerate(retrieved, 1)
        ]
        return {"answered": True, "answer": answer, "sources": sources}

    @staticmethod
    def _is_relevant(item: RetrievedChunk) -> bool:
        """The cross-encoder score is the better signal when present; otherwise fall back to vector distance."""
        if item.rerank_score is not None:
            return item.rerank_score >= settings.KNOWLEDGE_MIN_RERANK_SCORE
        return item.distance <= settings.KNOWLEDGE_MAX_DISTANCE

    @staticmethod
    def _build_user_message(question: str, retrieved: list[RetrievedChunk]) -> str:
        fragments = "\n\n".join(f"[{number}] {item.chunk.text}" for number, item in enumerate(retrieved, 1))
        return f"Фрагменты базы знаний:\n\n{fragments}\n\nВопрос: {question}"
