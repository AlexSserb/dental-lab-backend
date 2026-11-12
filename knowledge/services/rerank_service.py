import logging
from functools import lru_cache

from django.conf import settings

from knowledge.services.retrieval_service import RetrievedChunk

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_reranker():
    """Load the cross-encoder once per process (the first call downloads the model into RERANK_CACHE_DIR)."""
    from fastembed.rerank.cross_encoder import TextCrossEncoder  # heavy import, only needed when reranking

    logger.info("Loading reranker %s", settings.RERANK_MODEL)
    return TextCrossEncoder(model_name=settings.RERANK_MODEL, cache_dir=settings.RERANK_CACHE_DIR)


class RerankService:
    @staticmethod
    def rerank(query: str, candidates: list[RetrievedChunk], top_n: int) -> list[RetrievedChunk]:
        """Re-score the candidates with a cross-encoder and return the best `top_n`."""
        if not candidates:
            return []
        scores = list(get_reranker().rerank(query, [item.chunk.text for item in candidates]))
        for item, score in zip(candidates, scores):
            item.rerank_score = float(score)
        return sorted(candidates, key=lambda item: item.rerank_score, reverse=True)[:top_n]
