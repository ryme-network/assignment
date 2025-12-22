import json
import os
import shutil
from embeddings.embedder import Embedder
from embeddings.chroma_store import ChromaVectorStore

from embeddings.schema import (
    creator_content_text,
    creator_values_text,
    creator_audience_text,
    brand_content_query_text,
    brand_values_query_text,
    brand_audience_query_text,
)

from embeddings.filters import apply_hard_filters
from embeddings.must_avoid import violates_must_avoid
from embeddings.ranker import MultiScoreRanker
from embeddings.explain import explain_match


def load_data():
    with open(r"D:\Project\assignment\creators.json", encoding="utf-8") as f:
        creators = json.load(f)

    with open(r"D:\Project\assignment\brands.json", encoding="utf-8") as f:
        brands = json.load(f)

    return creators, brands


def ingest_creators(creators, embedder, store):

    creator_texts = []
    creator_ids = []
    creator_meta = []

    for c in creators:
        creator_id = c["creator_id"]

        creator_texts.append(creator_content_text(c))
        creator_ids.append(f"{creator_id}_content")
        creator_meta.append({
            "embedding_type": "creator_content",
            "creator_id": creator_id
        })

        creator_texts.append(creator_values_text(c))
        creator_ids.append(f"{creator_id}_values")
        creator_meta.append({
            "embedding_type": "creator_values",
            "creator_id": creator_id
        })

        creator_texts.append(creator_audience_text(c))
        creator_ids.append(f"{creator_id}_audience")
        creator_meta.append({
            "embedding_type": "creator_audience",
            "creator_id": creator_id
        })

    embeddings = embedder.encode(creator_texts)

    store.add(
        embeddings=embeddings,
        metadatas=creator_meta,
        documents=creator_texts
    )


def ingest_brands(brands_list, embedder, store):
    brand_texts = []
    brand_meta = []

    for b in brands_list:
        brand_id = b["brand_id"]

        brand_texts.append(brand_content_query_text(b))
        brand_meta.append({
            "embedding_type": "brand_content",
            "brand_id": brand_id
        })

        brand_texts.append(brand_values_query_text(b))
        brand_meta.append({
            "embedding_type": "brand_values",
            "brand_id": brand_id
        })

        brand_texts.append(brand_audience_query_text(b))
        brand_meta.append({
            "embedding_type": "brand_audience",
            "brand_id": brand_id
        })

    if brand_texts:
        embeddings = embedder.encode(brand_texts)
        store.add(
            embeddings=embeddings,
            metadatas=brand_meta,
            documents=brand_texts
        )


def main():
    creators, brands = load_data()
    brand = brands["brands"][0]  
    creators = creators["creators"]

    embedder = Embedder()
    store = ChromaVectorStore(persist_directory="./chroma_db", collection_name="creators")

    ingest_creators(creators, embedder, store)

    filtered_creators = apply_hard_filters(creators, brand)

    filtered_creators = [
        c for c in filtered_creators
        if not violates_must_avoid(c, brand)
    ]

    creator_lookup = {c["creator_id"]: c for c in filtered_creators}

    ranker = MultiScoreRanker(store, embedder)

    if ranker.is_cold_start_brand(brand):
        ranker.weights = {
            "content": 0.55,
            "values": 0.35,
            "audience": 0.10,
        }
    brand_texts = {
        "content": brand_content_query_text(brand),
        "values": brand_values_query_text(brand),
        "audience": brand_audience_query_text(brand),
    }

    ranked = ranker.rank_creators(brand_texts, top_k=20)

    ranked = [
        r for r in ranked
        if r["creator_id"] in creator_lookup
    ]

    final_results = []
    for r in ranked:
        creator = creator_lookup[r["creator_id"]]
        r["explanation"] = explain_match(r, creator, brand)
        final_results.append(r)

    print("\nTop matched creators:\n")
    for r in final_results[:5]:
        print("=" * 80)
        print(f"Creator ID      : {r['creator_id']}")
        print(f"Final Score     : {r['final_score']}")
        print(f"Content Score   : {r['content_score']}")
        print(f"Values Score    : {r['values_score']}")
        print(f"Audience Score  : {r['audience_score']}")
        print(r["explanation"])


if __name__ == "__main__":
    main()
