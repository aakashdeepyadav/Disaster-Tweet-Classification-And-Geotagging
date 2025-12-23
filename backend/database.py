# Compatibility shim: re-export new package implementation
from disaster_api.db.database import *
__all__ = [name for name in dir() if not name.startswith("_")]



def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tweets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tweets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tweet_text TEXT NOT NULL,
            disaster_label INTEGER NOT NULL,
            confidence REAL NOT NULL,
            category TEXT,
            severity TEXT,
            risk_level TEXT,
            location_mention TEXT,
            location TEXT,
            lat REAL,
            lon REAL,
            model_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Clusters table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_type TEXT NOT NULL,  -- 'location' or 'disaster'
            center_lat REAL,
            center_lon REAL,
            category TEXT,
            severity TEXT,
            tweet_count INTEGER DEFAULT 1,
            credibility_score REAL DEFAULT 0.0,
            alert_level TEXT DEFAULT 'Low',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Cluster-Tweet mapping
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cluster_tweets (
            cluster_id INTEGER,
            tweet_id INTEGER,
            FOREIGN KEY (cluster_id) REFERENCES clusters(id),
            FOREIGN KEY (tweet_id) REFERENCES tweets(id),
            PRIMARY KEY (cluster_id, tweet_id)
        )
    """)
    
    # Indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_lat_lon ON tweets(lat, lon)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_category ON tweets(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_created ON tweets(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clusters_type ON clusters(cluster_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clusters_alert ON clusters(alert_level)")
    
    conn.commit()
    conn.close()
    print(f"[DB] Database initialized at {DB_PATH}")


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def save_tweet(tweet_data: Dict) -> int:
    """
    Save a tweet to the database
    
    Args:
        tweet_data: Dictionary containing tweet information from predict_single
        
    Returns:
        tweet_id: The ID of the saved tweet
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tweets (
                tweet_text, disaster_label, confidence, category, severity,
                risk_level, location_mention, location, lat, lon, model_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tweet_data.get("tweet"),
            tweet_data.get("disaster_label", 0),
            tweet_data.get("confidence", 0.0),
            tweet_data.get("category"),
            tweet_data.get("severity"),
            tweet_data.get("risk_level"),
            tweet_data.get("location_mention"),
            tweet_data.get("location"),
            tweet_data.get("lat"),
            tweet_data.get("lon"),
            tweet_data.get("model_info", {}).get("model_name") if tweet_data.get("model_info") else None
        ))
        return cursor.lastrowid


def get_recent_tweets(limit: int = 1000, disaster_only: bool = False) -> List[Dict]:
    """
    Get recent tweets from the database
    
    Args:
        limit: Maximum number of tweets to return
        disaster_only: If True, only return disaster tweets
        
    Returns:
        List of tweet dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM tweets"
        if disaster_only:
            query += " WHERE disaster_label = 1"
        query += " ORDER BY created_at DESC LIMIT ?"
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_tweets_with_location(disaster_only: bool = True) -> List[Dict]:
    """
    Get tweets that have location coordinates
    
    Args:
        disaster_only: If True, only return disaster tweets
        
    Returns:
        List of tweets with valid coordinates
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM tweets WHERE lat IS NOT NULL AND lon IS NOT NULL"
        if disaster_only:
            query += " AND disaster_label = 1"
        query += " ORDER BY created_at DESC"
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def save_cluster(cluster_data: Dict) -> int:
    """
    Save or update a cluster
    
    Args:
        cluster_data: Dictionary containing cluster information
        
    Returns:
        cluster_id: The ID of the saved/updated cluster
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if cluster already exists (same type, category, and nearby location)
        existing = None
        if cluster_data.get("center_lat") and cluster_data.get("center_lon"):
            cursor.execute("""
                SELECT id FROM clusters 
                WHERE cluster_type = ? 
                AND category = ?
                AND ABS(center_lat - ?) < 0.01
                AND ABS(center_lon - ?) < 0.01
                LIMIT 1
            """, (
                cluster_data.get("cluster_type"),
                cluster_data.get("category"),
                cluster_data.get("center_lat"),
                cluster_data.get("center_lon")
            ))
            existing = cursor.fetchone()
        
        if existing:
            # Update existing cluster
            cluster_id = existing["id"]
            cursor.execute("""
                UPDATE clusters 
                SET tweet_count = ?,
                    credibility_score = ?,
                    alert_level = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                cluster_data.get("tweet_count", 1),
                cluster_data.get("credibility_score", 0.0),
                cluster_data.get("alert_level", "Low"),
                cluster_id
            ))
        else:
            # Insert new cluster
            cursor.execute("""
                INSERT INTO clusters (
                    cluster_type, center_lat, center_lon, category, severity,
                    tweet_count, credibility_score, alert_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cluster_data.get("cluster_type"),
                cluster_data.get("center_lat"),
                cluster_data.get("center_lon"),
                cluster_data.get("category"),
                cluster_data.get("severity"),
                cluster_data.get("tweet_count", 1),
                cluster_data.get("credibility_score", 0.0),
                cluster_data.get("alert_level", "Low")
            ))
            cluster_id = cursor.lastrowid
        
        return cluster_id


def link_tweet_to_cluster(cluster_id: int, tweet_id: int):
    """Link a tweet to a cluster"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO cluster_tweets (cluster_id, tweet_id)
            VALUES (?, ?)
        """, (cluster_id, tweet_id))


def get_clusters(alert_level: Optional[str] = None) -> List[Dict]:
    """
    Get all clusters, optionally filtered by alert level
    Only returns clusters with 10+ tweets (alerts only)
    
    Args:
        alert_level: Filter by alert level (None for all non-Low alerts)
        
    Returns:
        List of cluster dictionaries (only clusters with 10+ tweets)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Only get clusters with 10+ tweets (alerts)
        query = "SELECT * FROM clusters WHERE tweet_count >= 10"
        params = []
        if alert_level:
            query += " AND alert_level = ?"
            params.append(alert_level)
        else:
            # If no alert_level specified, only return non-Low alerts (which all have 10+ tweets)
            query += " AND alert_level != 'Low'"
        query += " ORDER BY credibility_score DESC, tweet_count DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_cluster_tweets(cluster_id: int) -> List[Dict]:
    """Get all tweets in a cluster"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.* FROM tweets t
            INNER JOIN cluster_tweets ct ON t.id = ct.tweet_id
            WHERE ct.cluster_id = ?
            ORDER BY t.created_at DESC
        """, (cluster_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_serious_alerts(min_credibility: float = 0.7) -> List[Dict]:
    """
    Get serious disaster alerts (high credibility clusters with 10+ tweets)
    
    Args:
        min_credibility: Minimum credibility score
        
    Returns:
        List of alert clusters with tweet details
        Only returns clusters with 10+ tweets in same/nearby area
    """
    # Get all clusters with alert_level != "Low" (which means they have 10+ tweets)
    # Filter by alert level: Critical, High, or Medium (all require 10+ tweets now)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM clusters 
            WHERE alert_level != 'Low' 
            AND tweet_count >= 10
            AND credibility_score >= ?
            ORDER BY credibility_score DESC, tweet_count DESC
        """, (min_credibility,))
        rows = cursor.fetchall()
        clusters = [dict(row) for row in rows]
    
    # Add tweet details to each cluster
    for cluster in clusters:
        cluster["tweets"] = get_cluster_tweets(cluster["id"])
    
    return clusters


def clear_all_data():
    """
    Clear all data from the database (tweets, clusters, and mappings)
    Returns the number of records deleted
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get counts before deletion
        cursor.execute("SELECT COUNT(*) FROM tweets")
        tweet_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM clusters")
        cluster_count = cursor.fetchone()[0]
        
        # Delete in order (respecting foreign keys)
        cursor.execute("DELETE FROM cluster_tweets")
        cursor.execute("DELETE FROM clusters")
        cursor.execute("DELETE FROM tweets")
        
        # Reset auto-increment counters (optional, but clean)
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('tweets', 'clusters', 'cluster_tweets')")
        
        return {
            "tweets_deleted": tweet_count,
            "clusters_deleted": cluster_count,
            "total_deleted": tweet_count + cluster_count
        }

