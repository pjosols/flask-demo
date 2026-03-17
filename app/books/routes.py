import json
from flask import render_template, request, jsonify
from mongo_datatables import DataTables, Editor, DataField
from app import mongo
from app.books import books

RECORDS_DATA_FIELDS = [
    DataField("artist",  "string"),
    DataField("title",   "string"),
    DataField("label",   "string"),
    DataField("year",    "number"),
    DataField("genre",   "array"),
    DataField("styles",  "array"),
    DataField("format",  "string"),
    DataField("country", "string"),
    DataField("rating",  "number"),
]


@books.route('/')
@books.route('/index')
def index():
    return render_template('books.html')


def _build_datatables(data: dict, **kwargs) -> DataTables:
    row_class = lambda doc: "high-rated" if (doc.get("rating") or 0) >= 4 else ""
    return DataTables(mongo, "records", data, data_fields=RECORDS_DATA_FIELDS,
                      row_class=row_class, **kwargs)


@books.route('/api/books', methods=['POST'])
def books_data():
    data = {}
    try:
        data = request.get_json()
        return jsonify(_build_datatables(data).get_rows())
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'error': str(e), 'data': [],
            'draw': data.get('draw', 1),
            'recordsTotal': 0, 'recordsFiltered': 0
        }), 500


@books.route('/api/books/filtered', methods=['POST'])
def books_data_filtered():
    """Pre-filtered to rating >= 3.5."""
    data = {}
    try:
        data = request.get_json()
        return jsonify(_build_datatables(data, rating={"$gte": 3.5}).get_rows())
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'error': str(e), 'data': [],
            'draw': data.get('draw', 1),
            'recordsTotal': 0, 'recordsFiltered': 0
        }), 500


@books.route('/api/editor/books', methods=['POST'])
def api_editor():
    try:
        data = request.get_json()
        doc_id = request.args.get('id', '')
        options = {
            "genre": [
                {"label": g, "value": g} for g in [
                    "Rock", "Jazz", "Electronic", "Hip Hop", "Soul",
                    "Classical", "Blues", "Reggae", "Folk", "Funk",
                    "R&B", "Country", "Latin", "Pop", "Metal"
                ]
            ],
            "rating": [
                {"label": f"{'★' * int(v)}{'+' if v % 1 else ''} ({v})", "value": v}
                for v in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
            ]
        }
        from mongo_datatables import Editor
        result = Editor(mongo, "records", data, doc_id,
                        data_fields=RECORDS_DATA_FIELDS, options=options).process()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'data': []}), 500
