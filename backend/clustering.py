"""
Clustering module for grouping tweets by location and disaster type
"""
import numpy as np
from typing import List, Dict, Tuple
from scipy.spatial.distance import cdist
from collections import defaultdict
import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth
    Returns distance in kilometers
    """
    R = 6371  # Earth radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def cluster_by_location(tweets: List[Dict], max_distance_km: float = 10.0) -> List[Dict]:
    """
    Cluster tweets by geographic location using distance-based clustering
    
    Args:
        tweets: List of tweets with lat/lon
        max_distance_km: Maximum distance (km) for tweets to be in same cluster
        
    Returns:
        List of cluster dictionaries
    """
    if not tweets:
        return []
    
    # Filter tweets with valid coordinates
    valid_tweets = [
        t for t in tweets
        if t.get("lat") is not None and t.get("lon") is not None
        and t.get("disaster_label") == 1  # Only disaster tweets
    ]
    
    if not valid_tweets:
        return []
    
    # Group by category first, then cluster locations within each category
    clusters = []
    category_groups = defaultdict(list)
    
    for tweet in valid_tweets:
        category = tweet.get("category", "Unknown")
        category_groups[category].append(tweet)
    
    # Cluster each category separately
    for category, category_tweets in category_groups.items():
        if len(category_tweets) == 1:
            # Single tweet - create cluster
            t = category_tweets[0]
            clusters.append({
                "cluster_type": "location",
                "center_lat": t["lat"],
                "center_lon": t["lon"],
                "category": category,
                "severity": t.get("severity", "Unknown"),
                "tweet_count": 1,
                "tweet_ids": [t.get("id")],
                "tweets": [t]
            })
        else:
            # Multiple tweets - cluster by distance
            category_clusters = _cluster_points(
                category_tweets,
                max_distance_km,
                category
            )
            clusters.extend(category_clusters)
    
    return clusters


def _cluster_points(tweets: List[Dict], max_distance_km: float, category: str) -> List[Dict]:
    """Helper function to cluster points using simple distance-based algorithm"""
    clusters = []
    used = set()
    
    for i, tweet in enumerate(tweets):
        if i in used:
            continue
        
        # Start new cluster
        cluster_tweets = [tweet]
        used.add(i)
        
        # Find nearby tweets
        for j, other_tweet in enumerate(tweets):
            if j in used or i == j:
                continue
            
            distance = haversine_distance(
                tweet["lat"], tweet["lon"],
                other_tweet["lat"], other_tweet["lon"]
            )
            
            if distance <= max_distance_km:
                cluster_tweets.append(other_tweet)
                used.add(j)
        
        # Calculate cluster center (average of coordinates)
        if cluster_tweets:
            avg_lat = sum(t["lat"] for t in cluster_tweets) / len(cluster_tweets)
            avg_lon = sum(t["lon"] for t in cluster_tweets) / len(cluster_tweets)
            
            # Calculate average severity (use most severe)
            severities = [t.get("severity", "Low") for t in cluster_tweets]
            severity_order = {"High": 3, "Medium": 2, "Low": 1, "Unknown": 0}
            max_severity = max(severities, key=lambda s: severity_order.get(s, 0))
            
            clusters.append({
                "cluster_type": "location",
                "center_lat": avg_lat,
                "center_lon": avg_lon,
                "category": category,
                "severity": max_severity,
                "tweet_count": len(cluster_tweets),
                "tweet_ids": [t.get("id") for t in cluster_tweets],
                "tweets": cluster_tweets
            })
    
    return clusters


def calculate_credibility_score(cluster: Dict) -> float:
    """
    Calculate credibility score for a cluster based on:
    - Number of tweets (more tweets = higher credibility)
    - Consistency of category (all same category = higher)
    - Average confidence (higher confidence = higher credibility)
    - Recency (recent tweets = higher credibility)
    
    Returns:
        Credibility score between 0.0 and 1.0
    """
    tweet_count = cluster.get("tweet_count", 1)
    tweets = cluster.get("tweets", [])
    
    if not tweets:
        return 0.0
    
    # Base score from tweet count (logarithmic scale)
    # 1 tweet = 0.2, 5 tweets = 0.6, 10+ tweets = 0.9+
    count_score = min(0.9, 0.2 + (math.log10(max(1, tweet_count)) * 0.3))
    
    # Consistency score (all same category)
    categories = [t.get("category") for t in tweets if t.get("category")]
    if categories:
        unique_categories = len(set(categories))
        consistency_score = 1.0 / unique_categories  # 1.0 if all same, lower if mixed
    else:
        consistency_score = 0.5
    
    # Average confidence score
    confidences = [t.get("confidence", 0.5) for t in tweets if t.get("confidence")]
    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
    else:
        avg_confidence = 0.5
    
    # Severity boost
    severity = cluster.get("severity", "Low")
    severity_multiplier = {"High": 1.2, "Medium": 1.1, "Low": 1.0, "Unknown": 0.9}
    severity_boost = severity_multiplier.get(severity, 1.0)
    
    # Calculate final score
    credibility = (count_score * 0.4 + consistency_score * 0.2 + avg_confidence * 0.4) * min(severity_boost, 1.0)
    
    return min(1.0, max(0.0, credibility))


def determine_alert_level(cluster: Dict) -> str:
    """
    Determine alert level based on cluster characteristics
    Requires minimum 10 tweets in same/nearby area for same disaster type
    
    Returns:
        Alert level: "Low", "Medium", "High", or "Critical"
        Returns "Low" if tweet_count < 10 (no alert generated)
    """
    credibility = cluster.get("credibility_score", 0.0)
    tweet_count = cluster.get("tweet_count", 1)
    severity = cluster.get("severity", "Low")
    
    # REQUIREMENT: Minimum 10 tweets for any alert
    if tweet_count < 10:
        return "Low"  # No alert generated
    
    # Critical: High credibility + 10+ tweets + high severity
    if credibility >= 0.8 and tweet_count >= 10 and severity == "High":
        return "Critical"
    
    # High: Good credibility + 10+ tweets
    if credibility >= 0.7 and tweet_count >= 10:
        return "High"
    
    # Medium: Some credibility + 10+ tweets
    if credibility >= 0.6 and tweet_count >= 10:
        return "Medium"
    
    # Low: 10+ tweets but low credibility (still no alert)
    return "Low"


def process_clusters(tweets: List[Dict]) -> List[Dict]:
    """
    Process tweets and create clusters with credibility scores
    Only generates alerts for clusters with 10+ tweets in same/nearby area
    
    Args:
        tweets: List of tweets with location data
        
    Returns:
        List of processed clusters with credibility and alert levels
    """
    # Cluster by location (groups by same disaster type in nearby areas)
    clusters = cluster_by_location(tweets, max_distance_km=10.0)
    
    # Calculate credibility and alert level for each cluster
    for cluster in clusters:
        cluster["credibility_score"] = calculate_credibility_score(cluster)
        cluster["alert_level"] = determine_alert_level(cluster)
    
    # Filter: Only return clusters with 10+ tweets (alerts only)
    # This ensures alerts are only generated when there are 10+ tweets
    alert_clusters = [c for c in clusters if c.get("tweet_count", 0) >= 10]
    
    # Sort by credibility (highest first)
    alert_clusters.sort(key=lambda c: c.get("credibility_score", 0), reverse=True)
    
    return alert_clusters

