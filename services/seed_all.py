"""Unified seed — populates both Cosmos DB and Azure AI Search index.

Seeds the full demo dataset in one command:

    1. Cosmos DB  — assets, sources, tags, L1 rules, L2 rules
    2. AI Search  — golden-tag embeddings into the ``golden-tags`` index

Usage:
    cd services
    uv run python -m seed_all
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Cosmos DB and AI Search")
    parser.add_argument(
        "--cosmos-only", action="store_true",
        help="Seed Cosmos DB only (skip AI Search)",
    )
    parser.add_argument(
        "--search-only", action="store_true",
        help="Seed AI Search index only (skip Cosmos DB)",
    )
    args = parser.parse_args()

    if not args.search_only:
        print("=" * 60)
        print("  STEP 1 — Seeding Cosmos DB")
        print("=" * 60)
        from database.seed import seed as seed_cosmos
        seed_cosmos()

    if not args.cosmos_only:
        print("\n" + "=" * 60)
        print("  STEP 2 — Seeding AI Search index")
        print("=" * 60)
        try:
            from search.seed_index import seed as seed_search
            seed_search()
        except Exception as exc:
            print(f"\n⚠️  AI Search seeding failed: {exc}")
            print("   (Cosmos DB was seeded successfully)")
            print("   Make sure SEARCH_ENDPOINT and PROJECT_ENDPOINT are set.")
            sys.exit(1)

    print("\n" + "🎉" + " " + "=" * 57)
    print("  All done! Both datastores are seeded.")
    print("=" * 60)


if __name__ == "__main__":
    main()
