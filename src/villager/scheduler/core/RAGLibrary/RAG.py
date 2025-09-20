import os

import loguru

from scheduler.core.RAGLibrary.RAGL_Calc import RAGEmbeddingWork, read_RAGL_sqlite
from scheduler.core.RAGLibrary.exceptions.NoSuchRAGLFileException import NoSuchRAGLFileException


class RAGManager:
    def __init__(self, RAGL_path="RAGL.sqlite"):
        if not os.path.exists(RAGL_path):
            raise NoSuchRAGLFileException(f"RAGL file not found at {RAGL_path}")
        loguru.logger.info("RAGEmbeddingWork starting...")
        self.EW = RAGEmbeddingWork()
        loguru.logger.info("Reading RAGL.sqlite...")
        self.article_list = read_RAGL_sqlite(RAGL_path)
        loguru.logger.info("Searching for the most relevant article...")
        self.combine_article_list = [f"{title}\n{body}" for title, body in self.article_list]

    def search_top_k_article(self, query_keywords: str, k: int = 3):
        """
        Search for the top k articles based on the query keywords.
        :param query_keywords: Search query string.
        :param k: Number of top results to return.
        :return:
        """
        return self.EW.search_nearest_with_TF_IDF(self.combine_article_list, query=query_keywords, k=k)


if __name__ == '__main__':
    RM = RAGManager(RAGL_path='statics/RAGL.sqlite')
    print(RM.search_top_k_article("Vmware VCenter 漏洞"))
