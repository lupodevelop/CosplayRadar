#!/usr/bin/env python3
"""
Caricatore di configurazione centralizzato per il trending algorithm
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class TrendingConfig:
    """Configurazione centralizzata per il trending algorithm"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Default path: cerca config nella directory del progetto
            current_dir = Path(__file__).parent
            config_path = current_dir / "config" / "trending_config.json"
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carica la configurazione dal file JSON"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File di configurazione non trovato: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Errore parsing JSON: {e}")
    
    # === BASE SCORE ===
    @property
    def favourites_divisor(self) -> int:
        """Divisore per calcolare base score da favourites"""
        return self._config["base_score"]["favourites_divisor"]
    
    @property
    def min_favourites(self) -> int:
        """Minimo numero di favourites"""
        return self._config["base_score"]["min_favourites"]
    
    # === GENDER BOOSTS ===
    def get_gender_boost(self, gender: Optional[str]) -> float:
        """Restituisce il boost per il genere specificato"""
        gender_key = gender if gender else "null"
        return self._config["gender_boosts"].get(gender_key, 1.0)
    
    @property
    def gender_boosts(self) -> Dict[str, float]:
        """Tutti i gender boost disponibili"""
        return {k: v for k, v in self._config["gender_boosts"].items() 
                if k not in ["description", "rationale"]}
    
    # === POPULARITY BOOSTS ===
    def get_popularity_boost(self, favourites: int) -> float:
        """Calcola il boost di popolarità basato sui favourites"""
        tiers = self._config["popularity_boosts"]["tiers"]
        
        # Ordina i tier per favourites decrescenti
        sorted_tiers = sorted(tiers, key=lambda x: x["min_favourites"], reverse=True)
        
        for tier in sorted_tiers:
            if favourites >= tier["min_favourites"]:
                return tier["boost"]
        
        return 1.0  # Default se nessun tier match
    
    # === STATUS BOOSTS ===
    def get_status_boost(self, status: str) -> float:
        """Restituisce il boost per lo status della serie"""
        return self._config["status_boosts"].get(status, {}).get("boost", 1.0)
    
    @property
    def status_boosts(self) -> Dict[str, float]:
        """Tutti gli status boost disponibili"""
        return {k: v["boost"] for k, v in self._config["status_boosts"].items() 
                if isinstance(v, dict) and "boost" in v}
    
    # === RECENCY BOOSTS ===
    def get_recency_boost(self, season_year: Optional[int]) -> float:
        """Calcola il boost di recency basato sull'anno"""
        if not season_year:
            return 1.0
        
        current_year = self._config["recency_boosts"]["current_year"]
        years_ago = current_year - season_year
        
        tiers = self._config["recency_boosts"]["tiers"]
        
        for tier in tiers:
            if years_ago <= tier["max_years_ago"]:
                return tier["boost"]
        
        return 1.0  # Default se nessun tier match
    
    # === FORMAT BOOSTS ===
    def get_format_boost(self, format: str) -> float:
        """Restituisce il boost per il formato della serie"""
        return self._config["format_boosts"].get(format, {}).get("boost", 1.0)
    
    # === ROLE BOOSTS ===
    def get_role_boost(self, role: str) -> float:
        """Restituisce il boost per il ruolo del personaggio"""
        return self._config["role_boosts"].get(role, {}).get("boost", 1.0)
    
    # === SERIES KEYWORDS BOOSTS ===
    def get_series_keywords_boost(self, series_name: str) -> float:
        """Calcola boost basato su keyword nella serie (euristica)"""
        if not series_name:
            return 1.0
        
        series_lower = series_name.lower()
        trending_keywords = self._config["series_keywords_boosts"]["trending_keywords"]
        
        for keyword_config in trending_keywords:
            keywords = keyword_config["keywords"]
            if any(keyword in series_lower for keyword in keywords):
                return keyword_config["boost"]
        
        return self._config["series_keywords_boosts"]["default_boost"]
    
    # === LIMITS ===
    @property
    def max_total_multiplier(self) -> float:
        """Limite massimo per il moltiplicatore totale"""
        return self._config["limits"]["max_total_multiplier"]
    
    @property
    def min_total_multiplier(self) -> float:
        """Limite minimo per il moltiplicatore totale"""
        return self._config["limits"]["min_total_multiplier"]
    
    # === METADATA ===
    @property
    def algorithm_version(self) -> str:
        """Versione corrente dell'algoritmo"""
        return self._config["algorithm_metadata"]["current_version"]
    
    @property
    def algorithm_description(self) -> str:
        """Descrizione dell'algoritmo"""
        return self._config["trending_algorithm"]["description"]
    
    # === UTILITY METHODS ===
    def calculate_total_multiplier(self, 
                                 gender: Optional[str] = None,
                                 favourites: int = 0,
                                 status: Optional[str] = None,
                                 season_year: Optional[int] = None,
                                 format: Optional[str] = None,
                                 role: Optional[str] = None,
                                 series_name: Optional[str] = None) -> float:
        """
        Calcola il moltiplicatore totale applicando tutti i boost
        """
        gender_boost = self.get_gender_boost(gender)
        popularity_boost = self.get_popularity_boost(favourites)
        status_boost = self.get_status_boost(status) if status else 1.0
        recency_boost = self.get_recency_boost(season_year)
        format_boost = self.get_format_boost(format) if format else 1.0
        role_boost = self.get_role_boost(role) if role else 1.0
        keywords_boost = self.get_series_keywords_boost(series_name)
        
        # Calcola moltiplicatore totale
        total = (gender_boost * popularity_boost * status_boost * 
                recency_boost * format_boost * role_boost * keywords_boost)
        
        # Applica i limiti
        return max(self.min_total_multiplier, min(total, self.max_total_multiplier))
    
    def get_boost_breakdown(self, 
                          gender: Optional[str] = None,
                          favourites: int = 0,
                          status: Optional[str] = None,
                          season_year: Optional[int] = None,
                          format: Optional[str] = None,
                          role: Optional[str] = None,
                          series_name: Optional[str] = None) -> Dict[str, float]:
        """
        Restituisce il breakdown dettagliato di tutti i boost applicati
        """
        breakdown = {
            'gender_boost': self.get_gender_boost(gender),
            'popularity_boost': self.get_popularity_boost(favourites),
            'status_boost': self.get_status_boost(status) if status else 1.0,
            'recency_boost': self.get_recency_boost(season_year),
            'format_boost': self.get_format_boost(format) if format else 1.0,
            'role_boost': self.get_role_boost(role) if role else 1.0,
            'keywords_boost': self.get_series_keywords_boost(series_name)
        }
        
        # Calcola totale prima e dopo i limiti
        raw_total = 1.0
        for boost in breakdown.values():
            raw_total *= boost
        
        breakdown['raw_total'] = raw_total
        breakdown['capped_total'] = max(self.min_total_multiplier, 
                                      min(raw_total, self.max_total_multiplier))
        
        return breakdown


# Istanza globale per uso facile
trending_config = TrendingConfig()


# Export
__all__ = ['TrendingConfig', 'trending_config']
