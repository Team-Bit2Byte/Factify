"""
Ensemble Model for Fake News Detection
Combines multiple specialized models with weighted voting
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
import numpy as np

from .credibility_scorer import CredibilityScorer, CredibilityScore
from .source_ranker import SourceRanker


@dataclass
class EnsembleResult:
    """Complete ensemble analysis result"""
    final_score: float
    credibility_analysis: CredibilityScore
    source_analysis: Dict
    model_predictions: Dict[str, float]
    consensus_level: str  # high, medium, low


class EnsembleModel:
    """
    Ensemble model combining multiple approaches:
    1. Content Analysis (linguistic patterns, sentiment)
    2. Source Credibility (domain reputation)
    3. Fact Verification (cross-referencing)
    4. Network Analysis (spread patterns)
    """
    
    def __init__(self):
        self.credibility_scorer = CredibilityScorer()
        self.source_ranker = SourceRanker()
        
        # Model weights (can be tuned)
        self.weights = {
            'credibility': 0.40,
            'source': 0.30,
            'fact_check': 0.20,
            'network': 0.10
        }
    
    def predict(self, analysis_data: Dict) -> EnsembleResult:
        """
        Run ensemble prediction
        
        Args:
            analysis_data: Dictionary containing:
                - text: str
                - source: str
                - entities: Dict
                - metadata: Dict
                - external_checks: Dict (optional)
                - social_signals: Dict (optional)
        
        Returns:
            EnsembleResult with comprehensive analysis
        """
        
        # 1. Get credibility score
        credibility_result = self.credibility_scorer.calculate_score(analysis_data)
        
        # 2. Get source analysis
        source = analysis_data.get('source', '')
        source_result = self.source_ranker.get_source_score(source)
        
        # 3. Aggregate fact-checking results (if available)
        fact_check_score = self._aggregate_fact_checks(
            analysis_data.get('external_checks', {})
        )
        
        # 4. Network analysis score (from credibility scorer)
        network_score = credibility_result.breakdown['network']
        
        # Store individual model predictions
        model_predictions = {
            'credibility': credibility_result.overall_score,
            'source': source_result['score'],
            'fact_check': fact_check_score,
            'network': network_score
        }
        
        # Calculate weighted ensemble score
        final_score = (
            credibility_result.overall_score * self.weights['credibility'] +
            source_result['score'] * self.weights['source'] +
            fact_check_score * self.weights['fact_check'] +
            network_score * self.weights['network']
        )
        
        # Calculate consensus level (how much models agree)
        consensus = self._calculate_consensus(model_predictions)
        
        return EnsembleResult(
            final_score=round(final_score, 2),
            credibility_analysis=credibility_result,
            source_analysis=source_result,
            model_predictions=model_predictions,
            consensus_level=consensus
        )
    
    def _aggregate_fact_checks(self, external_checks: Dict) -> float:
        """
        Aggregate results from multiple fact-checking sources
        
        Returns:
            Average fact-check score (0-100)
        """
        if not external_checks:
            return 50.0  # Neutral if no data
        
        fact_checks = external_checks.get('fact_checks', [])
        if not fact_checks:
            return 50.0
        
        # Average the ratings
        ratings = [fc.get('rating', 50) for fc in fact_checks]
        return sum(ratings) / len(ratings)
    
    def _calculate_consensus(self, predictions: Dict[str, float]) -> str:
        """
        Calculate consensus level between models
        
        Returns:
            'high', 'medium', or 'low'
        """
        scores = list(predictions.values())
        std_dev = np.std(scores)
        
        if std_dev < 10:
            return 'high'
        elif std_dev < 20:
            return 'medium'
        else:
            return 'low'
    
    def explain_prediction(self, result: EnsembleResult) -> Dict:
        """
        Generate explanation for the prediction
        
        Returns:
            Dictionary with human-readable explanation
        """
        explanation = {
            'verdict': result.credibility_analysis.verdict.value,
            'confidence': result.credibility_analysis.confidence.value,
            'reasons': [],
            'supporting_evidence': []
        }
        
        # Add reasons based on scores
        if result.model_predictions['credibility'] < 50:
            explanation['reasons'].append(
                f"Content analysis flagged suspicious linguistic patterns "
                f"(score: {result.model_predictions['credibility']:.1f}/100)"
            )
        
        if result.model_predictions['source'] < 50:
            explanation['reasons'].append(
                f"Source credibility is questionable "
                f"(score: {result.model_predictions['source']:.1f}/100)"
            )
        
        if result.model_predictions['fact_check'] < 50:
            explanation['reasons'].append(
                f"Claims could not be verified through fact-checking "
                f"(score: {result.model_predictions['fact_check']:.1f}/100)"
            )
        
        # Add supporting evidence
        if result.credibility_analysis.flags:
            explanation['supporting_evidence'].extend(
                result.credibility_analysis.flags
            )
        
        return explanation


# Example usage
if __name__ == "__main__":
    ensemble = EnsembleModel()
    
    # Example input
    test_data = {
        'text': "BREAKING: Scientists discover cure for all diseases! Doctors don't want you to know this shocking secret!",
        'source': 'fake-news-site.com',
        'entities': {
            'people': ['Scientists'],
            'organizations': [],
            'locations': []
        },
        'metadata': {
            'domain_age_days': 15,
            'has_ssl': False,
            'is_blacklisted': False
        },
        'external_checks': {
            'fact_checks': [
                {'source': 'snopes', 'rating': 20, 'verdict': 'false'},
                {'source': 'factcheck', 'rating': 15, 'verdict': 'fake'}
            ]
        },
        'social_signals': {
            'bot_score': 0.9,
            'coordinated_spread': True,
            'engagement_ratio': 0.85
        }
    }
    
    result = ensemble.predict(test_data)
    explanation = ensemble.explain_prediction(result)
    
    print(f"Final Score: {result.final_score}/100")
    print(f"Consensus: {result.consensus_level}")
    print(f"\nModel Predictions:")
    for model, score in result.model_predictions.items():
        print(f"  {model}: {score:.1f}/100")
    
    print(f"\nVerdict: {explanation['verdict']}")
    print(f"Confidence: {explanation['confidence']}")
    print(f"\nReasons:")
    for reason in explanation['reasons']:
        print(f"  - {reason}")
