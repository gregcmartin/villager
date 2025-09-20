import hashlib
import os
import pickle
import sqlite3
import loguru

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

from scheduler.core.RAGLibrary.tools.misc import calc_md5


def read_RAGL_sqlite(path: str):
    """
    Read sqlite file and fetch RAGL table, returning titles and bodies.
    :param path: SQLite file path.
    :return: List of (title, body) tuples.
    """
    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()
        return cursor.execute('SELECT * FROM RAGL').fetchall()


class RAGEmbeddingWork:
    def __init__(self):
        # self.modal_name = 'all-MiniLM-L6-v2'
        # self.model = SentenceTransformer(self.modal_name)
        self.vectorizer = TfidfVectorizer()  # 计算查询的 TF-IDF 向量(文本频率)

    # def embedding_list(self, raw_list, batch_size=32):
    #     """
    #     Embedding string list.
    #     :param raw_list: List of strings to encode.
    #     :param batch_size: Batch size for encoding.
    #     :return: List of embeddings as numpy array.
    #     """
    #     if os.path.exists(f"{calc_md5(raw_list)}.pkl"):
    #         return np.array(pickle.load(open(f"{calc_md5(raw_list)}.pkl", "rb")))
    #
    #     model = self.model
    #     embeddings_list = []
    #     for i in tqdm(range(0, len(raw_list), batch_size), desc="Encoding Titles in Batches"):
    #         batch = raw_list[i:i + batch_size]
    #         embeddings = model.encode(batch)
    #         embeddings_list.extend(embeddings)
    #
    #     pickle.dump(embeddings_list, open(f"{calc_md5(raw_list)}.pkl", "wb"))
    #     return np.array(embeddings_list)

    # def build_vector_index(self, slice_list):
    #     """
    #     Build a vector index for the slice list.
    #     :param slice_list: List of documents (titles + bodies).
    #     :return: Faiss index.
    #     """
    #     embeddings = self.embedding_list(slice_list)
    #     dimension = embeddings.shape[1]
    #     index = faiss.IndexFlatL2(dimension)
    #     index.add(embeddings)
    #     return index

    def calculate_tfidf_distances(self, articles, query):
        """
        Calculate the cosine similarities between the query and the articles.
        :param articles: List of articles.
        :param query: The search query.
        :return: Cosine similarities and sorted indices.
        """
        articles_tfidf = self.vectorizer.fit_transform(articles)
        query_tfidf = self.vectorizer.transform([query])
        cosine_similarities = cosine_similarity(query_tfidf, articles_tfidf)
        return cosine_similarities[0]

    def search_nearest_with_TF_IDF(self, articles, query: str, k=3):
        """
        Use TfidVectorizer to sort and slice the list with query and filtrate top k.
        :param articles: List of articles.
        :param query: The search query.
        :param k: Number of top results to return.
        :return: Nearest documents with distance and content.
        """
        cosine_similarities = self.calculate_tfidf_distances(articles, query)
        top_indices = np.argsort(cosine_similarities)[::-1][:k]

        nearest = {'items': []}
        for idx in top_indices:
            nearest['items'].append({'distance': float(cosine_similarities[idx]), 'shot_content': articles[idx]})
        return nearest

    # def calculate_nlp_distances(self, slice_list, query, k=3):
    #     """
    #     Calculate the distances between the query and the slice list using NLP model.
    #     :param slice_list: List of documents.
    #     :param query: The search query.
    #     :param k: Number of top results to return.
    #     :return: Distances and indices of the nearest documents.
    #     """
    #     index = self.build_vector_index(slice_list)
    #     query_embedding = self.model.encode([query])
    #     distances, indices = index.search(np.array(query_embedding), k)
    #     return distances[0], indices[0]

    # def search_nearest_with_NLP(self, slice_list, query: str, k=3):
    #     """
    #     Search for the nearest documents based on the query.
    #     :param slice_list: List of documents (titles + bodies).
    #     :param query: Search query string.
    #     :param k: Number of top results to return.
    #     :return: Nearest documents with distance and content.
    #     """
    #     distances, indices = self.calculate_nlp_distances(slice_list, query, k)
    #
    #     nearest = {'items': []}
    #     for i in range(k):
    #         shot = slice_list[indices[i]]
    #         nearest['items'].append({'distance': float(distances[i]), 'shot_content': shot})
    #     return nearest

    # def search_nearest_with_weighted(self, articles, slice_list, query: str, k=3, tfidf_weight=0.5, nlp_weight=0.5):
    #     """
    #     Search for the nearest documents based on the query using both TF-IDF and NLP models with weighted results.
    #     :param articles: List of articles (for TF-IDF).
    #     :param slice_list: List of documents (for NLP).
    #     :param query: Search query string.
    #     :param k: Number of top results to return.
    #     :param tfidf_weight: Weight for the TF-IDF distance.
    #     :param nlp_weight: Weight for the NLP distance.
    #     :return: Nearest documents with distance and content.
    #     """
    #     tfidf_distances = self.calculate_tfidf_distances(articles, query)
    #     nlp_distances, nlp_indices = self.calculate_nlp_distances(slice_list, query, k)
    #     combined_scores = []
    #     for i in range(k):
    #         tfidf_score = tfidf_distances[i] if i < len(tfidf_distances) else 0
    #         nlp_score = nlp_distances[i]
    #         combined_score = tfidf_weight * tfidf_score + nlp_weight * nlp_score  # 计算加权得分
    #         combined_scores.append((combined_score, i, slice_list[nlp_indices[i]]))
    #     combined_scores.sort(key=lambda x: x[0], reverse=True)
    #
    #     nearest = {'items': []}
    #     for score, idx, shot_content in combined_scores[:k]:
    #         nearest['items'].append({'distance': float(score), 'shot_content': shot_content})
    #
    #     return nearest


if __name__ == '__main__':
    loguru.logger.info("RAGEmbeddingWork starting...")
    EW = RAGEmbeddingWork()
    loguru.logger.info("Reading RAGL.sqlite...")
    article_list = read_RAGL_sqlite("RAGL.sqlite")
    loguru.logger.info("Searching for the most relevant article...")
    combine_article_list = [f"{title}\n{body}" for title, body in article_list]

    query = """Geoserver 漏洞"""
    print(f"Most relevant article: {EW.search_nearest_with_TF_IDF(combine_article_list, query=query)}")
