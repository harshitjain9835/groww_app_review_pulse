import logging
import numpy as np
import umap
import hdbscan
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_distances

logger = logging.getLogger(__name__)

class ReviewClustering:
    def __init__(self, min_cluster_size: int = 5):
        self.min_cluster_size = min_cluster_size

    def cluster_reviews(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(reviews) < 20:
            logger.warning("Not enough reviews to perform meaningful clustering. Aborting pipeline.")
            raise ValueError("Minimum 20 reviews required for clustering.")

        embeddings = np.array([r["embedding"] for r in reviews])

        # 1. Dimensionality Reduction
        reducer = umap.UMAP(n_neighbors=15, n_components=5, metric="cosine", random_state=42)
        reduced_embeddings = reducer.fit_transform(embeddings)

        # 2. Clustering
        clusterer = hdbscan.HDBSCAN(min_cluster_size=self.min_cluster_size, metric="euclidean")
        labels = clusterer.fit_predict(reduced_embeddings)

        # Fallback: If all points are classified as noise (-1), try a looser tolerance
        if all(label == -1 for label in labels) and self.min_cluster_size > 3:
            logger.info("All reviews classified as noise. Executing fallback: lowering min_cluster_size to 3.")
            clusterer = hdbscan.HDBSCAN(min_cluster_size=3, metric="euclidean")
            labels = clusterer.fit_predict(reduced_embeddings)

        for i, review in enumerate(reviews):
            review["cluster_id"] = int(labels[i])

        # 3. Grouping and Ranking
        clusters_map = {}
        for review in reviews:
            cid = review["cluster_id"]
            if cid == -1:
                continue  # Discard unclustered noise
                
            if cid not in clusters_map:
                clusters_map[cid] = {"reviews": [], "ratings": []}
            clusters_map[cid]["reviews"].append(review)
            clusters_map[cid]["ratings"].append(review.get("rating", 0))

        ranked_clusters = []
        for cid, data in clusters_map.items():
            size = len(data["reviews"])
            avg_rating = sum(data["ratings"]) / size
            # Ranking formula per architecture
            score = size * (6 - avg_rating)
            
            # 4. Extract Samples (Finding Medoids via cosine distance to cluster centroid)
            cluster_embeddings = np.array([r["embedding"] for r in data["reviews"]])
            centroid = cluster_embeddings.mean(axis=0).reshape(1, -1)
            distances = cosine_distances(cluster_embeddings, centroid).flatten()
            
            for idx, r in enumerate(data["reviews"]):
                r["distance_to_centroid"] = distances[idx]
                
            # Select top 8 samples closest to the geometric center of the cluster
            samples = sorted(data["reviews"], key=lambda x: x["distance_to_centroid"])[:8]
            
            ranked_clusters.append({
                "cluster_id": cid,
                "size": size,
                "avg_rating": round(avg_rating, 2),
                "score": round(score, 2),
                "samples": samples
            })

        # Sort descending by priority score
        return sorted(ranked_clusters, key=lambda x: x["score"], reverse=True)