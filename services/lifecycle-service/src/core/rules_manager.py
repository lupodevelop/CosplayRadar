"""
Rules Manager per il Lifecycle Service
Gestisce le regole e configurazioni per le decisioni del lifecycle
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LifecycleRulesManager:
    """Gestisce le regole di configurazione del lifecycle"""
    
    DEFAULT_CONFIG = {
        "periods": {
            "grace_period_days": 42,
            "extended_grace_days": 28,
            "cleanup_days": 90
        },
        "thresholds": {
            "keep_active": {
                "min_composite_score": 50.0,
                "min_popularity": 30.0,
                "min_favourites": 100,
                "min_character_trending": 70.0
            },
            "extend_grace": {
                "min_composite_score_ratio": 0.7
            }
        },
        "scoring": {
            "weights": {
                "popularity": 0.3,
                "favourites": 0.2,
                "trending": 0.2,
                "character_count_multiplier": 5,
                "avg_character_trending": 0.2,
                "max_character_trending": 0.1
            },
            "bonus_conditions": {
                "high_character_engagement": {
                    "bonus_multiplier": 1.2
                },
                "seasonal_relevance": {
                    "bonus_multiplier": 1.1
                }
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = self._load_config()
        logger.info(f"📋 Rules Manager inizializzato con config: {config_path or 'default'}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Carica la configurazione dal file o usa quella di default"""
        if not self.config_path:
            logger.info("📋 Uso configurazione di default")
            return self.DEFAULT_CONFIG.copy()
        
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"📋 Configurazione caricata da {self.config_path}")
                
                # Merge con default per eventuali chiavi mancanti
                return self._merge_with_default(config)
            else:
                logger.warning(f"⚠️  File config {self.config_path} non trovato, uso default")
                return self.DEFAULT_CONFIG.copy()
                
        except Exception as e:
            logger.error(f"❌ Errore caricamento config {self.config_path}: {e}")
            logger.info("📋 Fallback alla configurazione di default")
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_with_default(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge della configurazione caricata con quella di default"""
        merged = self.DEFAULT_CONFIG.copy()
        
        def deep_merge(default_dict: Dict, config_dict: Dict):
            for key, value in config_dict.items():
                if key in default_dict and isinstance(default_dict[key], dict) and isinstance(value, dict):
                    deep_merge(default_dict[key], value)
                else:
                    default_dict[key] = value
        
        deep_merge(merged, config)
        return merged
    
    def get_grace_period_days(self) -> int:
        """Ottieni il numero di giorni del periodo di grazia"""
        return self.config['periods']['grace_period_days']
    
    def get_extended_grace_days(self) -> int:
        """Ottieni il numero di giorni del periodo di grazia estesa"""
        return self.config['periods']['extended_grace_days']
    
    def get_cleanup_days(self) -> int:
        """Ottieni il numero di giorni dopo cui fare cleanup"""
        return self.config['periods']['cleanup_days']
    
    def get_thresholds(self) -> Dict[str, Any]:
        """Ottieni le soglie per le decisioni"""
        return self.config['thresholds']
    
    def get_scoring_weights(self) -> Dict[str, float]:
        """Ottieni i pesi per il calcolo dello score composito"""
        return self.config['scoring']['weights']
    
    def get_bonus_conditions(self) -> Dict[str, Any]:
        """Ottieni le condizioni per i bonus al punteggio"""
        return self.config['scoring']['bonus_conditions']
    
    def get_current_config(self) -> Dict[str, Any]:
        """Ottieni la configurazione completa corrente"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Aggiorna la configurazione (runtime)"""
        try:
            self.config = self._merge_with_default(new_config)
            logger.info("📋 Configurazione aggiornata in runtime")
            return True
        except Exception as e:
            logger.error(f"❌ Errore aggiornamento configurazione: {e}")
            return False
    
    def save_config(self, save_path: Optional[str] = None) -> bool:
        """Salva la configurazione corrente su file"""
        try:
            path = save_path or self.config_path
            if not path:
                logger.error("❌ Nessun path specificato per salvare la configurazione")
                return False
            
            config_file = Path(path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Configurazione salvata in {path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio configurazione: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """Valida la configurazione corrente"""
        issues = []
        warnings = []
        
        # Valida periodi
        if self.get_grace_period_days() < 7:
            issues.append("Periodo di grazia troppo breve (< 7 giorni)")
        if self.get_grace_period_days() > 90:
            warnings.append("Periodo di grazia molto lungo (> 90 giorni)")
        
        # Valida soglie
        thresholds = self.get_thresholds()
        if thresholds['keep_active']['min_composite_score'] <= 0:
            issues.append("Soglia composita per keep_active deve essere > 0")
        
        # Valida pesi
        weights = self.get_scoring_weights()
        total_weight = sum([v for k, v in weights.items() if k != 'character_count_multiplier'])
        if abs(total_weight - 1.0) > 0.1:
            warnings.append(f"Somma pesi scoring non è 1.0: {total_weight}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    def get_rule_explanation(self, rule_type: str) -> str:
        """Ottieni spiegazione di una regola specifica"""
        explanations = {
            'grace_period': f"Serie appena rilasciate rimangono attive per {self.get_grace_period_days()} giorni",
            'keep_active': f"Serie mantenute attive se score >= {self.get_thresholds()['keep_active']['min_composite_score']}",
            'extend_grace': f"Grazia estesa se score >= {self.get_thresholds()['keep_active']['min_composite_score'] * self.get_thresholds()['extend_grace']['min_composite_score_ratio']:.1f}",
            'cleanup': f"Serie archiviate da più di {self.get_cleanup_days()} giorni vengono pulite"
        }
        
        return explanations.get(rule_type, "Regola non trovata")
