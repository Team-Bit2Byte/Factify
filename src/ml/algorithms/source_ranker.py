"""
Source Reputation Ranking System
Maintains database of known sources and their historical accuracy
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class SourceProfile:
    """Profile of a news source"""
    domain: str
    name: str
    reputation_score: float  # 0-100
    accuracy_history: List[Dict]
    bias_rating: str  # left, center, right, mixed
    fact_check_count: int
    last_updated: datetime
    is_blacklisted: bool
    category: str  # mainstream, alternative, blog, social


class SourceRanker:
    """
    Manages source credibility rankings and historical data
    """
    
    # Known high-credibility sources
    VERIFIED_SOURCES = {
        'reuters.com': {'score': 95, 'bias': 'center', 'category': 'mainstream'},
        'apnews.com': {'score': 95, 'bias': 'center', 'category': 'mainstream'},
        'bbc.com': {'score': 90, 'bias': 'center', 'category': 'mainstream'},
        'nytimes.com': {'score': 85, 'bias': 'center-left', 'category': 'mainstream'},
        'wsj.com': {'score': 85, 'bias': 'center-right', 'category': 'mainstream'},
        'npr.org': {'score': 85, 'bias': 'center-left', 'category': 'mainstream'},
    }
    
    # Known low-credibility/satirical sources
    BLACKLISTED_SOURCES = {
        'theonion.com': {'reason': 'satire', 'score': 20},
        'clickhole.com': {'reason': 'satire', 'score': 20},
        # Add known fake news domains
    }
    
    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize source ranker
        
        Args:
            database_path: Path to JSON database of source profiles
        """
        self.database_path = database_path
        self.sources = {}
        if database_path:
            self._load_database()
    
    def get_source_score(self, domain: str) -> Dict:
        """
        Get credibility score for a domain
        
        Returns:
            Dict with score, bias, category, and other metadata
        """
        # Check if in verified sources
        if domain in self.VERIFIED_SOURCES:
            return {
                'score': self.VERIFIED_SOURCES[domain]['score'],
                'bias': self.VERIFIED_SOURCES[domain]['bias'],
                'category': self.VERIFIED_SOURCES[domain]['category'],
                'is_verified': True,
                'is_blacklisted': False
            }
        
        # Check if blacklisted
        if domain in self.BLACKLISTED_SOURCES:
            return {
                'score': self.BLACKLISTED_SOURCES[domain]['score'],
                'reason': self.BLACKLISTED_SOURCES[domain]['reason'],
                'is_verified': False,
                'is_blacklisted': True
            }
        
        # Check custom database
        if domain in self.sources:
            profile = self.sources[domain]
            return {
                'score': profile.reputation_score,
                'bias': profile.bias_rating,
                'category': profile.category,
                'is_verified': False,
                'is_blacklisted': profile.is_blacklisted
            }
        
        # Unknown source - return neutral with flag
        return {
            'score': 50,
            'bias': 'unknown',
            'category': 'unknown',
            'is_verified': False,
            'is_blacklisted': False,
            'is_unknown': True
        }
    
    def update_source_score(self, domain: str, accuracy: float, context: Dict):
        """
        Update source score based on new information
        
        Args:
            domain: Source domain
            accuracy: Accuracy rating (0-100) for this article
            context: Additional context about the rating
        """
        if domain not in self.sources:
            # Create new profile
            self.sources[domain] = SourceProfile(
                domain=domain,
                name=context.get('name', domain),
                reputation_score=accuracy,
                accuracy_history=[{
                    'date': datetime.now().isoformat(),
                    'accuracy': accuracy,
                    'context': context
                }],
                bias_rating='unknown',
                fact_check_count=1,
                last_updated=datetime.now(),
                is_blacklisted=False,
                category='unknown'
            )
        else:
            # Update existing profile
            profile = self.sources[domain]
            profile.accuracy_history.append({
                'date': datetime.now().isoformat(),
                'accuracy': accuracy,
                'context': context
            })
            profile.fact_check_count += 1
            
            # Recalculate reputation score (weighted average)
            # Recent checks have more weight
            weights = [0.5 if i == len(profile.accuracy_history) - 1 else 0.5 / (len(profile.accuracy_history) - 1)
                      for i in range(len(profile.accuracy_history))]
            profile.reputation_score = sum(
                h['accuracy'] * w for h, w in zip(profile.accuracy_history, weights)
            )
            profile.last_updated = datetime.now()
    
    def rank_sources(self, domains: List[str]) -> List[tuple]:
        """
        Rank multiple sources by credibility
        
        Returns:
            List of (domain, score) tuples sorted by score descending
        """
        rankings = []
        for domain in domains:
            score_data = self.get_source_score(domain)
            rankings.append((domain, score_data['score']))
        
        return sorted(rankings, key=lambda x: x[1], reverse=True)
    
    def _load_database(self):
        """Load source profiles from database file"""
        try:
            with open(self.database_path, 'r') as f:
                data = json.load(f)
                for domain, profile_data in data.items():
                    self.sources[domain] = SourceProfile(**profile_data)
        except FileNotFoundError:
            print(f"Database file not found: {self.database_path}")
        except Exception as e:
            print(f"Error loading database: {e}")
    
    def save_database(self):
        """Save source profiles to database file"""
        if not self.database_path:
            return
        
        data = {}
        for domain, profile in self.sources.items():
            data[domain] = {
                'domain': profile.domain,
                'name': profile.name,
                'reputation_score': profile.reputation_score,
                'accuracy_history': profile.accuracy_history,
                'bias_rating': profile.bias_rating,
                'fact_check_count': profile.fact_check_count,
                'last_updated': profile.last_updated.isoformat(),
                'is_blacklisted': profile.is_blacklisted,
                'category': profile.category
            }
        
        with open(self.database_path, 'w') as f:
            json.dump(data, f, indent=2)


# Example usage
if __name__ == "__main__":
    ranker = SourceRanker()
    
    # Test some sources
    test_domains = ['reuters.com', 'theonion.com', 'unknown-news.com', 'bbc.com']
    
    print("Source Credibility Rankings:\n")
    for domain in test_domains:
        result = ranker.get_source_score(domain)
        print(f"{domain}:")
        print(f"  Score: {result['score']}/100")
        print(f"  Verified: {result.get('is_verified', False)}")
        print(f"  Blacklisted: {result.get('is_blacklisted', False)}")
        print(f"  Category: {result.get('category', 'unknown')}")
        print()
