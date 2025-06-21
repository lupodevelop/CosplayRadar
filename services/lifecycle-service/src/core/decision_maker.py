"""
Decision Maker per il Lifecycle Service
Contiene la logica intelligente per decidere il destino delle serie
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LifecycleDecisionMaker:
    """Prende decisioni intelligenti sul lifecycle delle serie"""
    
    def __init__(self, rules_manager):
        self.rules_manager = rules_manager
        logger.info("🧠 Decision Maker inizializzato")
    
    async def make_lifecycle_decision(self, series: Dict) -> Dict[str, Any]:
        """Prende una decisione sul destino di una serie"""
        
        # Calcola score composito
        composite_score = self._calculate_composite_score(series)
        
        # Ottieni soglie dalle regole
        thresholds = self.rules_manager.get_thresholds()
        
        # Logica decisionale
        decision = self._evaluate_decision(series, composite_score, thresholds)
        
        logger.info(f"🎯 {series.get('title', 'Unknown')}: {decision['action']} (score: {composite_score:.1f})")
        
        return {
            'action': decision['action'],
            'reason': decision['reason'],
            'composite_score': composite_score,
            'series_metrics': self._extract_metrics(series),
            'decision_factors': decision.get('factors', {})
        }
    
    def _calculate_composite_score(self, series: Dict) -> float:
        """Calcola lo score composito per la decisione"""
        
        # Estrai metriche
        popularity = float(series.get('popularity', 0) or 0)
        favourites = float(series.get('favourites', 0) or 0)
        trending = float(series.get('trending', 0) or 0)
        character_count = int(series.get('character_count', 0) or 0)
        avg_char_trending = float(series.get('avg_character_trending', 0) or 0)
        max_char_trending = float(series.get('max_character_trending', 0) or 0)
        
        # Ottieni pesi dalla configurazione
        weights = self.rules_manager.get_scoring_weights()
        
        # Calcola score base
        score = (
            (popularity * weights['popularity']) +
            (favourites * weights['favourites']) +
            (trending * weights['trending']) +
            (character_count * weights['character_count_multiplier']) +
            (avg_char_trending * weights['avg_character_trending']) +
            (max_char_trending * weights['max_character_trending'])
        )
        
        # Applica bonus
        score = self._apply_bonus_conditions(series, score)
        
        return round(score, 2)
    
    def _apply_bonus_conditions(self, series: Dict, base_score: float) -> float:
        """Applica condizioni bonus al punteggio"""
        
        bonus_conditions = self.rules_manager.get_bonus_conditions()
        final_score = base_score
        
        # Bonus per personaggi molto trendy
        max_char_trending = float(series.get('max_character_trending', 0) or 0)
        if max_char_trending >= 80:
            final_score *= bonus_conditions.get('high_character_engagement', {}).get('bonus_multiplier', 1.2)
            logger.debug(f"Bonus personaggi trendy applicato: {max_char_trending}")
        
        # Bonus per crescita trend (se abbiamo dati storici)
        # TODO: Implementare quando avremo snapshot storici
        
        # Bonus stagionale (se la serie è della stagione corrente)
        if self._is_current_season(series):
            final_score *= bonus_conditions.get('seasonal_relevance', {}).get('bonus_multiplier', 1.1)
            logger.debug("Bonus stagionale applicato")
        
        return final_score
    
    def _evaluate_decision(self, series: Dict, composite_score: float, thresholds: Dict) -> Dict[str, Any]:
        """Valuta e prende la decisione finale"""
        
        popularity = float(series.get('popularity', 0) or 0)
        favourites = float(series.get('favourites', 0) or 0)
        trending = float(series.get('trending', 0) or 0)
        max_char_trending = float(series.get('max_character_trending', 0) or 0)
        character_count = int(series.get('character_count', 0) or 0)
        
        # Regole per mantenere attivo
        keep_active_threshold = thresholds['keep_active']['min_composite_score']
        min_popularity = thresholds['keep_active']['min_popularity']
        min_favourites = thresholds['keep_active']['min_favourites']
        min_char_trending = thresholds['keep_active']['min_character_trending']
        
        if composite_score >= keep_active_threshold:
            if (popularity >= min_popularity or 
                favourites >= min_favourites or 
                max_char_trending >= min_char_trending):
                
                return {
                    'action': 'KEEP_ACTIVE',
                    'reason': f'Alta performance: score={composite_score}, pop={popularity}, fav={favourites}, char_trending={max_char_trending}',
                    'factors': {
                        'high_composite_score': composite_score >= keep_active_threshold,
                        'sufficient_popularity': popularity >= min_popularity,
                        'sufficient_favourites': favourites >= min_favourites,
                        'high_character_trending': max_char_trending >= min_char_trending
                    }
                }
        
        # Regole per estendere grazia
        extend_grace_ratio = thresholds['extend_grace']['min_composite_score_ratio']
        min_score_for_grace = keep_active_threshold * extend_grace_ratio
        
        if (composite_score >= min_score_for_grace and
            (popularity > 0 or trending > 0 or character_count > 0 or max_char_trending > 0)):
            
            return {
                'action': 'EXTEND_GRACE',
                'reason': f'Performance moderata, estendo grazia: score={composite_score}, attività presente',
                'factors': {
                    'moderate_score': composite_score >= min_score_for_grace,
                    'has_activity': popularity > 0 or trending > 0 or character_count > 0
                }
            }
        
        # Default: archivia
        return {
            'action': 'ARCHIVE',
            'reason': f'Performance insufficiente: score={composite_score} < {min_score_for_grace}',
            'factors': {
                'low_composite_score': composite_score < min_score_for_grace,
                'insufficient_activity': popularity == 0 and trending == 0 and character_count == 0
            }
        }
    
    def _extract_metrics(self, series: Dict) -> Dict[str, Any]:
        """Estrae le metriche chiave della serie per il report"""
        return {
            'popularity': series.get('popularity', 0),
            'favourites': series.get('favourites', 0),
            'trending': series.get('trending', 0),
            'character_count': series.get('character_count', 0),
            'avg_character_trending': series.get('avg_character_trending', 0),
            'max_character_trending': series.get('max_character_trending', 0),
            'days_in_grace': series.get('days_in_grace', 0),
            'status': series.get('status', 'unknown')
        }
    
    def _is_current_season(self, series: Dict) -> bool:
        """Determina se la serie è della stagione corrente"""
        # Logica semplificata: serie che hanno iniziato negli ultimi 3 mesi
        start_date = series.get('start_date')
        if not start_date:
            return False
        
        if isinstance(start_date, str):
            try:
                start_date = datetime.fromisoformat(start_date).date()
            except:
                return False
        
        three_months_ago = datetime.now().date() - timedelta(days=90)
        return start_date >= three_months_ago
    
    async def evaluate_single_series(self, series_id: int, repository) -> Dict[str, Any]:
        """Valuta una singola serie per test/debug"""
        try:
            # Ottieni dati serie dal repository
            series_list = await repository.get_series_by_lifecycle_stage_with_id(series_id)
            if not series_list:
                return {'error': f'Serie {series_id} non trovata'}
            
            series = series_list[0]
            decision = await self.make_lifecycle_decision(series)
            
            return {
                'series_id': series_id,
                'title': series.get('title', 'Unknown'),
                'current_stage': series.get('lifecycle_stage', 'unknown'),
                'decision': decision
            }
            
        except Exception as e:
            logger.error(f"Errore valutazione serie {series_id}: {e}")
            return {'error': str(e)}
