from pymongo import MongoClient, TEXT


def create_indexes(db=None):
    try:
        if db is None:
            from flask import current_app
            db = current_app.mongo.db  # type: ignore

        col = db["places"]

        col.create_index(
            [("name", TEXT), ("feature_code", TEXT), ("timezone", TEXT)],
            weights={"name": 10, "feature_code": 3, "timezone": 1},
            name="name_text",
        )

        for field in ("name", "country_code", "feature_code",
                      "population", "timezone", "admin1_code"):
            col.create_index(field)

        print("Indexes created.")

    except Exception as e:
        import traceback
        print(f"Error creating indexes: {e}")
        print(traceback.format_exc())


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", default="mongodb://localhost:27017/geonames_demo")
    args = parser.parse_args()
    client = MongoClient(args.uri)
    create_indexes(client.get_database())


if __name__ == "__main__":
    main()
