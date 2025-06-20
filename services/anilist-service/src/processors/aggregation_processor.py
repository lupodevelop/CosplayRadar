"""
Aggregation processor for historical data management and cleanup
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from ..models import (
    HistoricalData, TrendingScoreData, AggregationPeriod,
    CharacterData, TrendingData, AniListConfig
)


class AggregationProcessor:
    """Process and aggregate historical trending data"""
    
    def __init__(self, config: Optional[AniListConfig] = None):
        self.config = config or AniListConfig()
        self.logger = logging.getLogger(__name__)
        
        # Retention periods from config
        self.daily_retention_days = self.config.daily_retention_days
        self.weekly_retention_weeks = self.config.weekly_retention_weeks
        self.monthly_retention_months = self.config.monthly_retention_months
        self.yearly_retention_years = self.config.yearly_retention_years
    
    def create_historical_data(
        self,
        trending_scores: List[TrendingScoreData],
        period: AggregationPeriod = AggregationPeriod.DAILY
    ) -> List[HistoricalData]:
        """Create historical data entries from trending scores"""
        historical_entries = []
        timestamp = datetime.now()
        
        for score in trending_scores:
            try:
                historical_entry = HistoricalData(
                    timestamp=timestamp,
                    entity_id=score.entity_id,
                    entity_type=score.entity_type,
                    trending_score=score.final_score,
                    popularity_rank=0,  # Will be calculated later
                    aggregation_period=period,
                    data_points=1,
                    metadata={
                        'base_score': score.base_score,
                        'gender_boost': score.gender_boost,
                        'recency_boost': score.recency_boost,
                        'quality_boost': score.quality_boost,
                        'role_boost': score.role_boost,
                        'momentum_boost': score.momentum_boost,
                        'calculation_details': score.calculation_details
                    }
                )
                historical_entries.append(historical_entry)
                
            except Exception as e:
                self.logger.error(f"Error creating historical data for {score.entity_id}: {e}")
                continue
        
        # Calculate popularity ranks
        historical_entries = self._calculate_popularity_ranks(historical_entries)
        
        self.logger.info(f"Created {len(historical_entries)} historical entries for {period.value}")
        return historical_entries
    
    def aggregate_daily_to_weekly(
        self,
        daily_data: List[HistoricalData]
    ) -> List[HistoricalData]:
        """Aggregate daily data into weekly summaries"""
        return self._aggregate_data(daily_data, AggregationPeriod.WEEKLY, days=7)
    
    def aggregate_weekly_to_monthly(
        self,
        weekly_data: List[HistoricalData]
    ) -> List[HistoricalData]:
        """Aggregate weekly data into monthly summaries"""
        return self._aggregate_data(weekly_data, AggregationPeriod.MONTHLY, days=30)
    
    def aggregate_monthly_to_yearly(
        self,
        monthly_data: List[HistoricalData]
    ) -> List[HistoricalData]:
        """Aggregate monthly data into yearly summaries"""
        return self._aggregate_data(monthly_data, AggregationPeriod.YEARLY, days=365)
    
    def cleanup_old_data(
        self,
        historical_data: List[HistoricalData]
    ) -> Tuple[List[HistoricalData], Dict[str, int]]:
        """Remove old data based on retention policies"""
        now = datetime.now()
        kept_data = []
        cleanup_stats = {'daily': 0, 'weekly': 0, 'monthly': 0, 'yearly': 0}
        
        for data in historical_data:
            should_keep = False
            age = now - data.timestamp
            
            if data.aggregation_period == AggregationPeriod.DAILY:
                if age.days <= self.daily_retention_days:
                    should_keep = True
                else:
                    cleanup_stats['daily'] += 1
            
            elif data.aggregation_period == AggregationPeriod.WEEKLY:
                if age.days <= (self.weekly_retention_weeks * 7):
                    should_keep = True
                else:
                    cleanup_stats['weekly'] += 1
            
            elif data.aggregation_period == AggregationPeriod.MONTHLY:
                if age.days <= (self.monthly_retention_months * 30):
                    should_keep = True
                else:
                    cleanup_stats['monthly'] += 1
            
            elif data.aggregation_period == AggregationPeriod.YEARLY:
                if age.days <= (self.yearly_retention_years * 365):
                    should_keep = True
                else:
                    cleanup_stats['yearly'] += 1
            
            if should_keep:
                kept_data.append(data)
        
        total_removed = sum(cleanup_stats.values())
        self.logger.info(f"Cleaned up {total_removed} old records: {cleanup_stats}")
        
        return kept_data, cleanup_stats
    
    def identify_trending_entities(
        self,
        historical_data: List[HistoricalData],
        lookback_days: int = 7,
        min_improvement: float = 20.0
    ) -> List[Dict[str, Any]]:
        """Identify entities with significant trending improvements"""
        trending_entities = []
        
        # Group data by entity
        entity_data = defaultdict(list)
        for data in historical_data:
            entity_data[data.entity_id].append(data)
        
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        for entity_id, data_points in entity_data.items():
            try:
                # Sort by timestamp
                data_points.sort(key=lambda x: x.timestamp)
                
                # Get recent and older data
                recent_data = [d for d in data_points if d.timestamp >= cutoff_date]
                older_data = [d for d in data_points if d.timestamp < cutoff_date]
                
                if not recent_data or not older_data:
                    continue
                
                # Calculate average scores
                recent_avg = statistics.mean([d.trending_score for d in recent_data])
                older_avg = statistics.mean([d.trending_score for d in older_data])
                
                # Calculate improvement
                improvement = recent_avg - older_avg
                improvement_percent = (improvement / older_avg) * 100 if older_avg > 0 else 0
                
                if improvement_percent >= min_improvement:
                    trending_entities.append({
                        'entity_id': entity_id,
                        'entity_type': data_points[0].entity_type,
                        'improvement': improvement,
                        'improvement_percent': improvement_percent,
                        'recent_score': recent_avg,
                        'older_score': older_avg,
                        'data_points': len(data_points)
                    })
                    
            except Exception as e:
                self.logger.error(f"Error analyzing trends for entity {entity_id}: {e}")
                continue
        
        # Sort by improvement percentage
        trending_entities.sort(key=lambda x: x['improvement_percent'], reverse=True)
        
        self.logger.info(f"Identified {len(trending_entities)} trending entities")
        return trending_entities
    
    def calculate_trend_velocity(
        self,
        historical_data: List[HistoricalData],
        entity_id: int,
        lookback_days: int = 14
    ) -> Dict[str, float]:
        """Calculate trend velocity for a specific entity"""
        entity_data = [
            d for d in historical_data 
            if d.entity_id == entity_id and 
            d.timestamp >= datetime.now() - timedelta(days=lookback_days)
        ]
        
        if len(entity_data) < 2:
            return {'velocity': 0.0, 'acceleration': 0.0, 'confidence': 0.0}
        
        # Sort by timestamp
        entity_data.sort(key=lambda x: x.timestamp)
        
        # Calculate velocity (change in score over time)
        scores = [d.trending_score for d in entity_data]
        time_diffs = [
            (entity_data[i].timestamp - entity_data[i-1].timestamp).total_seconds() / 3600  # hours
            for i in range(1, len(entity_data))
        ]
        
        velocities = [
            (scores[i] - scores[i-1]) / time_diffs[i-1] if time_diffs[i-1] > 0 else 0
            for i in range(1, len(scores))
        ]
        
        if not velocities:
            return {'velocity': 0.0, 'acceleration': 0.0, 'confidence': 0.0}
        
        # Average velocity
        avg_velocity = statistics.mean(velocities)
        
        # Calculate acceleration (change in velocity)
        acceleration = 0.0
        if len(velocities) >= 2:
            acceleration = statistics.mean([
                velocities[i] - velocities[i-1]
                for i in range(1, len(velocities))
            ])
        
        # Confidence based on data points and consistency
        confidence = min(1.0, len(entity_data) / 10)  # More data points = higher confidence
        velocity_std = statistics.stdev(velocities) if len(velocities) > 1 else 0
        if velocity_std > 0:
            confidence *= max(0.1, 1 - (velocity_std / abs(avg_velocity))) if avg_velocity != 0 else 0.5
        
        return {
            'velocity': avg_velocity,
            'acceleration': acceleration,
            'confidence': confidence
        }
    
    def generate_aggregation_summary(
        self,
        historical_data: List[HistoricalData]
    ) -> Dict[str, Any]:
        """Generate summary statistics for aggregated data"""
        if not historical_data:
            return {}
        
        # Group by aggregation period
        period_data = defaultdict(list)
        for data in historical_data:
            period_data[data.aggregation_period].append(data)
        
        summary = {
            'total_records': len(historical_data),
            'date_range': {
                'start': min(d.timestamp for d in historical_data),
                'end': max(d.timestamp for d in historical_data)
            },
            'by_period': {},
            'entities': {
                'total': len(set(d.entity_id for d in historical_data)),
                'characters': len(set(d.entity_id for d in historical_data if d.entity_type == 'character')),
                'media': len(set(d.entity_id for d in historical_data if d.entity_type == 'media'))
            }
        }
        
        for period, data_list in period_data.items():
            scores = [d.trending_score for d in data_list]
            summary['by_period'][period.value] = {
                'records': len(data_list),
                'score_stats': {
                    'mean': statistics.mean(scores),
                    'median': statistics.median(scores),
                    'min': min(scores),
                    'max': max(scores),
                    'std': statistics.stdev(scores) if len(scores) > 1 else 0
                },
                'data_points_total': sum(d.data_points for d in data_list)
            }
        
        return summary
    
    def _aggregate_data(
        self,
        data: List[HistoricalData],
        target_period: AggregationPeriod,
        days: int
    ) -> List[HistoricalData]:
        """Internal method to aggregate data by time period"""
        if not data:
            return []
        
        # Group data by entity and time window
        grouped_data = defaultdict(lambda: defaultdict(list))
        
        for item in data:
            # Calculate time window
            time_window = self._get_time_window(item.timestamp, days)
            grouped_data[item.entity_id][time_window].append(item)
        
        aggregated_data = []
        
        for entity_id, time_windows in grouped_data.items():
            for time_window, items in time_windows.items():
                if not items:
                    continue
                
                try:
                    # Calculate aggregated values
                    scores = [item.trending_score for item in items]
                    ranks = [item.popularity_rank for item in items]
                    
                    # Get representative item (most recent)
                    representative = max(items, key=lambda x: x.timestamp)
                    
                    # Create aggregated entry
                    aggregated_entry = HistoricalData(
                        timestamp=time_window,
                        entity_id=entity_id,
                        entity_type=representative.entity_type,
                        trending_score=statistics.mean(scores),
                        popularity_rank=int(statistics.mean(ranks)) if ranks else 0,
                        aggregation_period=target_period,
                        data_points=sum(item.data_points for item in items),
                        metadata={
                            'score_min': min(scores),
                            'score_max': max(scores),
                            'score_std': statistics.stdev(scores) if len(scores) > 1 else 0,
                            'original_entries': len(items),
                            'aggregated_from': items[0].aggregation_period.value if items else None
                        }
                    )
                    
                    aggregated_data.append(aggregated_entry)
                    
                except Exception as e:
                    self.logger.error(f"Error aggregating data for entity {entity_id}: {e}")
                    continue
        
        self.logger.info(f"Aggregated {len(data)} {items[0].aggregation_period.value if data else 'N/A'} entries into {len(aggregated_data)} {target_period.value} entries")
        return aggregated_data
    
    def _get_time_window(self, timestamp: datetime, days: int) -> datetime:
        """Get the start of the time window for aggregation"""
        if days == 7:  # Weekly - start of week (Monday)
            days_since_monday = timestamp.weekday()
            return timestamp - timedelta(days=days_since_monday)
        elif days == 30:  # Monthly - start of month
            return timestamp.replace(day=1)
        elif days == 365:  # Yearly - start of year
            return timestamp.replace(month=1, day=1)
        else:  # Custom period
            return timestamp - timedelta(days=timestamp.timetuple().tm_yday % days)
    
    def _calculate_popularity_ranks(
        self,
        historical_data: List[HistoricalData]
    ) -> List[HistoricalData]:
        """Calculate popularity ranks based on trending scores"""
        if not historical_data:
            return historical_data
        
        # Sort by trending score descending
        sorted_data = sorted(historical_data, key=lambda x: x.trending_score, reverse=True)
        
        # Assign ranks
        for i, data in enumerate(sorted_data):
            data.popularity_rank = i + 1
        
        return historical_data
