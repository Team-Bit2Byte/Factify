"""
Credibility Scoring Algorithm for Fake News Detection
Multi-factor ranking system with weighted ensemble approach
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence levels for credibility assessment"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Verdict(Enum):
    """Final verdict categories"""
    VERIFIED = "verified"
    LIKELY_TRUE = "likely_true"
    UNCERTAIN = "uncertain"
    SUSPICIOUS = "suspicious"
    LIKELY_FAKE = "likely_fake"
    CONFIRMED_FAKE = "confirmed_fake"


@dataclass
class CredibilityScore:
    """
    Complete credibility analysis result
    """
    overall_score: float  # 0-100
    confidence: ConfidenceLevel
    verdict: Verdict
    breakdown: Dict[str, float]
    flags: List[str]
    recommendations: List[str]


class CredibilityScorer:
    """
    Multi-factor credibility scoring system
    
    Weights:
    - Content Analysis: 30%
    - Source Credibility: 25%
    - Fact Verification: 30%
    - Network Analysis: 15%
    """
    
    # Weights for each factor
    WEIGHTS = {
        'content': 0.30,
        'source': 0.25,
        'facts': 0.30,
        'network': 0.15
    }
    
    # Suspicious keywords that indicate potential fake news
    SUSPICIOUS_KEYWORDS = [
        'shocking', 'unbelievable', 'must see', 'you won\'t believe',
        'doctors hate', 'they don\'t want you to know', 'breaking',
        'urgent', 'leaked', 'secret', 'exposed', 'truth revealed'
    ]
    
    # Emotional manipulation indicators
    EMOTIONAL_TRIGGERS = [
        'outrage', 'furious', 'devastating', 'horrifying', 'terrifying',
        'miracle', 'amazing', 'incredible', 'disaster', 'crisis'
    ]
    
    def __init__(self):
        self.source_database = {}  # Will be loaded from database
        
    def calculate_score(self, analysis_data: Dict) -> CredibilityScore:
        """
        Calculate overall credibility score
        
        Args:
            analysis_data: Dictionary containing:
                - text: str
                - source: str
                - entities: Dict[str, List]
                - metadata: Dict
                - external_checks: Dict (optional)
        
        Returns:
            CredibilityScore object with detailed breakdown
        """
        
        # Calculate individual factor scores
        content_score = self._analyze_content(
            analysis_data.get('text', ''),
            analysis_data.get('entities', {})
        )
        
        source_score = self._analyze_source(
            analysis_data.get('source', ''),
            analysis_data.get('metadata', {})
        )
        
        fact_score = self._verify_facts(
            analysis_data.get('text', ''),
            analysis_data.get('external_checks', {})
        )
        
        network_score = self._analyze_network(
            analysis_data.get('metadata', {}),
            analysis_data.get('social_signals', {})
        )
        
        # Calculate weighted overall score
        overall_score = (
            content_score * self.WEIGHTS['content'] +
            source_score * self.WEIGHTS['source'] +
            fact_score * self.WEIGHTS['facts'] +
            network_score * self.WEIGHTS['network']
        )
        
        # Determine confidence level
        confidence = self._calculate_confidence(analysis_data)
        
        # Determine verdict
        verdict = self._determine_verdict(overall_score)
        
        # Collect flags and recommendations
        flags = self._identify_flags(analysis_data, {
            'content': content_score,
            'source': source_score,
            'facts': fact_score,
            'network': network_score
        })
        
        recommendations = self._generate_recommendations(overall_score, flags)
        
        return CredibilityScore(
            overall_score=round(overall_score, 2),
            confidence=confidence,
            verdict=verdict,
            breakdown={
                'content': round(content_score, 2),
                'source': round(source_score, 2),
                'facts': round(fact_score, 2),
                'network': round(network_score, 2)
            },
            flags=flags,
            recommendations=recommendations
        )
    
    def _analyze_content(self, text: str, entities: Dict) -> float:
        """
        Analyze content quality and linguistic patterns
        
        Factors:
        - Writing quality (40%)
        - Sentiment analysis (30%)
        - Clickbait detection (30%)
        """
        score = 100.0
        
        # Check for suspicious keywords (clickbait)
        clickbait_count = sum(
            1 for keyword in self.SUSPICIOUS_KEYWORDS
            if keyword.lower() in text.lower()
        )
        score -= min(clickbait_count * 10, 30)  # Max -30 points
        
        # Check for emotional manipulation
        emotional_count = sum(
            1 for trigger in self.EMOTIONAL_TRIGGERS
            if trigger.lower() in text.lower()
        )
        score -= min(emotional_count * 5, 20)  # Max -20 points
        
        # Check writing quality (basic heuristics)
        if len(text) < 100:
            score -= 10  # Too short
        
        # Check for ALL CAPS (sensationalism)
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if caps_ratio > 0.3:
            score -= 15
        
        # Check for excessive punctuation (!!!, ???)
        excessive_punct = len(re.findall(r'[!?]{2,}', text))
        score -= min(excessive_punct * 5, 15)
        
        return max(score, 0)
    
    def _analyze_source(self, source: str, metadata: Dict) -> float:
        """
        Analyze source credibility
        
        Factors:
        - Domain reputation (50%)
        - Historical accuracy (30%)
        - Technical indicators (20%)
        """
        score = 50.0  # Start neutral
        
        # Check if source is in known database
        source_data = self.source_database.get(source, {})
        
        if source_data:
            # Use historical data
            score += source_data.get('reputation_score', 0) * 0.5
        else:
            # No data - check basic indicators
            # Check domain age
            domain_age_days = metadata.get('domain_age_days', 0)
            if domain_age_days > 365:
                score += 20
            elif domain_age_days > 90:
                score += 10
            else:
                score -= 10  # Very new domain is suspicious
            
            # Check SSL certificate
            if metadata.get('has_ssl', False):
                score += 5
            else:
                score -= 10
            
            # Check if domain is on blacklist
            if metadata.get('is_blacklisted', False):
                score -= 40
        
        return max(min(score, 100), 0)
    
    def _verify_facts(self, text: str, external_checks: Dict) -> float:
        """
        Verify factual claims
        
        Factors:
        - Cross-reference matches (60%)
        - External API results (40%)
        """
        score = 50.0  # Start neutral
        
        # Check external fact-checking APIs
        if external_checks:
            fact_check_results = external_checks.get('fact_checks', [])
            if fact_check_results:
                # Average the fact check ratings
                avg_rating = sum(
                    r.get('rating', 50) for r in fact_check_results
                ) / len(fact_check_results)
                score = avg_rating
        
        # Check for verifiable entities
        # (If we have dates, people, orgs that can be cross-referenced)
        # This would integrate with knowledge bases
        
        return max(min(score, 100), 0)
    
    def _analyze_network(self, metadata: Dict, social_signals: Dict) -> float:
        """
        Analyze network and social spread patterns
        
        Factors:
        - Spread pattern (50%)
        - Engagement authenticity (50%)
        """
        score = 50.0  # Start neutral
        
        # Check bot-like behavior
        if social_signals.get('bot_score', 0) > 0.7:
            score -= 30
        
        # Check for coordinated behavior
        if social_signals.get('coordinated_spread', False):
            score -= 20
        
        # Check engagement patterns
        engagement_ratio = social_signals.get('engagement_ratio', 0)
        if engagement_ratio > 0.8:  # Suspiciously high
            score -= 15
        
        return max(min(score, 100), 0)
    
    def _calculate_confidence(self, analysis_data: Dict) -> ConfidenceLevel:
        """
        Calculate confidence level based on data availability
        """
        data_points = 0
        
        if analysis_data.get('text'):
            data_points += 1
        if analysis_data.get('source'):
            data_points += 1
        if analysis_data.get('entities'):
            data_points += 1
        if analysis_data.get('external_checks'):
            data_points += 2  # External checks are more valuable
        if analysis_data.get('social_signals'):
            data_points += 1
        
        if data_points >= 5:
            return ConfidenceLevel.HIGH
        elif data_points >= 3:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _determine_verdict(self, score: float) -> Verdict:
        """
        Determine final verdict based on score
        """
        if score >= 80:
            return Verdict.VERIFIED
        elif score >= 65:
            return Verdict.LIKELY_TRUE
        elif score >= 50:
            return Verdict.UNCERTAIN
        elif score >= 35:
            return Verdict.SUSPICIOUS
        elif score >= 20:
            return Verdict.LIKELY_FAKE
        else:
            return Verdict.CONFIRMED_FAKE
    
    def _identify_flags(self, analysis_data: Dict, scores: Dict) -> List[str]:
        """
        Identify specific issues to flag
        """
        flags = []
        
        text = analysis_data.get('text', '').lower()
        
        # Check for clickbait
        if any(kw in text for kw in self.SUSPICIOUS_KEYWORDS):
            flags.append("Clickbait language detected")
        
        # Check for emotional manipulation
        if any(trigger in text for trigger in self.EMOTIONAL_TRIGGERS):
            flags.append("Emotional manipulation indicators")
        
        # Check low source score
        if scores['source'] < 40:
            flags.append("Unreliable source")
        
        # Check low fact score
        if scores['facts'] < 40:
            flags.append("Unverified claims")
        
        # Check network anomalies
        if scores['network'] < 40:
            flags.append("Suspicious spread pattern")
        
        return flags
    
    def _generate_recommendations(self, score: float, flags: List[str]) -> List[str]:
        """
        Generate actionable recommendations
        """
        recommendations = []
        
        if score < 50:
            recommendations.append("Cross-verify with established news sources")
            recommendations.append("Check original sources of quoted information")
        
        if "Unreliable source" in flags:
            recommendations.append("Verify the publisher's credibility")
        
        if "Clickbait language detected" in flags:
            recommendations.append("Be cautious of sensationalized headlines")
        
        if "Unverified claims" in flags:
            recommendations.append("Look for fact-checking site verification")
        
        return recommendations


# Example usage
if __name__ == "__main__":
    scorer = CredibilityScorer()
    
    # Example analysis data
    test_data = {
        'text': "BREAKING: You won't believe what doctors discovered! This shocking treatment changes everything!",
        'source': 'unknown-news-site.com',
        'entities': {
            'people': [],
            'organizations': [],
            'locations': []
        },
        'metadata': {
            'domain_age_days': 30,
            'has_ssl': False,
            'is_blacklisted': False
        },
        'external_checks': {},
        'social_signals': {
            'bot_score': 0.8,
            'coordinated_spread': True
        }
    }
    
    result = scorer.calculate_score(test_data)
    
    print(f"Overall Score: {result.overall_score}/100")
    print(f"Confidence: {result.confidence.value}")
    print(f"Verdict: {result.verdict.value}")
    print(f"\nBreakdown:")
    for factor, score in result.breakdown.items():
        print(f"  {factor}: {score}/100")
    print(f"\nFlags: {', '.join(result.flags)}")
    print(f"\nRecommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")
