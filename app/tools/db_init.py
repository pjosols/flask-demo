from pymongo import MongoClient


def create_indexes(db=None):
    try:
        if db is None:
            from flask import current_app
            db = current_app.mongo.db  # type: ignore

        print("Creating indexes...")

        col = db["records"]

        col.create_index([
            ("artist", "text"),
            ("title",  "text"),
            ("label",  "text"),
            ("genre",  "text"),
            ("styles", "text"),
        ])

        for field in ("artist", "title", "label", "year", "format", "country", "rating"):
            col.create_index(field)

        col.create_index("genre")
        col.create_index("styles")

        print("Indexes created.")

    except Exception as e:
        import traceback
        print(f"Error creating indexes: {e}")
        print(traceback.format_exc())


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", default="mongodb://localhost:27017/vinyl_database")
    args = parser.parse_args()
    client = MongoClient(args.uri)
    create_indexes(client.get_database())


if __name__ == "__main__":
    main()
