import numpy as np
from sklearn.cluster import DBSCAN
from typing import List, Dict, Any

class SpatialClustering:
    def __init__(self, eps_meters=50, min_samples=2):
        # Convert eps from meters to decimal degrees (approximate)
        # 1 degree of latitude is ~111,111 meters
        # This is a simple approximation suitable for DBSCAN on local scale
        self.eps_degrees = eps_meters / 111111.0 
        self.min_samples = min_samples

    def cluster_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups issues geographically using DBSCAN.
        Input issues should have 'id', 'latitude', 'longitude', 'issue_type', 'priority_score'.
        """
        if not issues or len(issues) < self.min_samples:
            return []

        # Extract coordinates
        coords = np.array([[issue['latitude'], issue['longitude']] for issue in issues])
        
        # We can use Haversine distance metric for actual earth distances in radians,
        # but for small radii < 1km, simple Euclidean on degrees is fast and often 'good enough' 
        # given the abstract requirements.
        db = DBSCAN(eps=self.eps_degrees, min_samples=self.min_samples).fit(coords)
        
        labels = db.labels_
        
        # Post-process clusters
        clusters = {}
        for i, label in enumerate(labels):
            if label == -1:
                continue # Noise point
                
            if label not in clusters:
                clusters[label] = {
                    "cluster_id": int(label),
                    "issues": [],
                    "issue_ids": [],
                    "categories": set(),
                    "priority_scores": [],
                    "center_lat": 0.0,
                    "center_lng": 0.0
                }
                
            issue = issues[i]
            clusters[label]["issues"].append(issue)
            clusters[label]["issue_ids"].append(issue['id'])
            clusters[label]["categories"].add(issue['issue_type'])
            clusters[label]["priority_scores"].append(issue.get('priority_score', 0))
            
        # Finalize cluster metadata
        result = []
        for label, cluster in clusters.items():
            num_points = len(cluster["issues"])
            
            # Calculate centroid
            cluster["center_lat"] = sum(iss['latitude'] for iss in cluster["issues"]) / num_points
            cluster["center_lng"] = sum(iss['longitude'] for iss in cluster["issues"]) / num_points
            
            # Calculate metrics
            avg_priority = sum(cluster["priority_scores"]) / num_points if num_points > 0 else 0
            
            result.append({
                "cluster_id": cluster["cluster_id"],
                "issue_count": num_points,
                "center": {"lat": cluster["center_lat"], "lng": cluster["center_lng"]},
                "categories": list(cluster["categories"]),
                "issue_ids": cluster["issue_ids"],
                "avg_priority": round(avg_priority, 2),
                "max_priority": max(cluster["priority_scores"]) if cluster["priority_scores"] else 0
            })
            
        return result
