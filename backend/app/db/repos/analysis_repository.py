from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger

from ...models.database_models import AIAnalysis


class AnalysisRepository:
    
    @staticmethod
    def create_analysis(
        db: Session,
        symbol: str,
        agent_type: str,
        signal: str,
        confidence: float,
        reasoning: str,
        indicators: dict = None,
        market_conditions: dict = None,
        risk_assessment: dict = None
    ) -> AIAnalysis:
        analysis = AIAnalysis(
            symbol=symbol,
            agent_type=agent_type,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            indicators=indicators,
            market_conditions=market_conditions,
            risk_assessment=risk_assessment
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        logger.debug(f"Saved analysis: {agent_type} for {symbol}")
        return analysis
    
    @staticmethod
    def get_recent_analyses(
        db: Session,
        limit: int = 50,
        symbol: Optional[str] = None
    ) -> List[AIAnalysis]:
        query = db.query(AIAnalysis)
        if symbol:
            query = query.filter(AIAnalysis.symbol == symbol)
        return query.order_by(desc(AIAnalysis.timestamp)).limit(limit).all()
    
    @staticmethod
    def get_analyses_by_timeframe(
        db: Session,
        start_time: datetime,
        end_time: datetime,
        symbol: Optional[str] = None
    ) -> List[AIAnalysis]:
        query = db.query(AIAnalysis).filter(
            AIAnalysis.timestamp >= start_time,
            AIAnalysis.timestamp <= end_time
        )
        if symbol:
            query = query.filter(AIAnalysis.symbol == symbol)
        return query.order_by(desc(AIAnalysis.timestamp)).all()
    
    @staticmethod
    def get_analyses_by_agent(
        db: Session,
        agent_type: str,
        limit: int = 50
    ) -> List[AIAnalysis]:
        return db.query(AIAnalysis).filter(
            AIAnalysis.agent_type == agent_type
        ).order_by(desc(AIAnalysis.timestamp)).limit(limit).all()
    
    @staticmethod
    def delete_old_analyses(db: Session, days: int = 30) -> int:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(AIAnalysis).filter(
            AIAnalysis.timestamp < cutoff_date
        ).delete()
        db.commit()
        logger.info(f"Deleted {deleted} old analyses")
        return deleted
