import hashlib

import faiss


def merge_indices(title_index, body_index):
    """
    Merges two FAISS indexes (title and body) into one.
    :param title_index: FAISS index for titles.
    :param body_index: FAISS index for bodies.
    :return: Combined FAISS index containing both titles and bodies.
    """
    dimension = title_index.d
    combined_index = faiss.IndexFlatL2(dimension)
    combined_index.add(title_index.reconstruct_n(0, title_index.ntotal))
    combined_index.add(body_index.reconstruct_n(0, body_index.ntotal))
    return combined_index


def calc_md5(*args):
    return hashlib.md5(str(args).encode()).hexdigest()
