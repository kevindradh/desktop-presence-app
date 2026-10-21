"""Cosine convention shared with PostgreSQL. No gallery of real subjects here."""
from dataclasses import dataclass
import math
import numpy as np
from ai.recognizer.arcface import unit_embedding


@dataclass(frozen=True)
class MatchDecision:
    member_id: int | None
    similarity: float | None


def cosine_similarity(left,right):
    return float(np.clip(np.dot(unit_embedding(left),unit_embedding(right)),-1,1))


def identify(session,vector,*,model_version,threshold=.60):
    from app.repositories.core import EmbeddingRepository
    if type(threshold) not in (int,float) or not math.isfinite(threshold) or not 0<=threshold<=1:
        raise ValueError("Ambang pengenalan tidak valid.")
    matches=EmbeddingRepository(session).nearest(unit_embedding(vector),model_version=model_version,limit=1)
    if not matches:
        return MatchDecision(None,None)
    first=matches[0]
    return MatchDecision(first.member_id if first.similarity>=threshold else None,first.similarity)
