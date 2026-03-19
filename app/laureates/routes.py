from flask import render_template, request, jsonify
from mongo_datatables import DataTables, DataField
from app import mongo
from app.laureates import laureates

DATA_FIELDS = [
    DataField("name",          "string"),
    DataField("birth_country", "string"),
    DataField("year",          "number"),
    DataField("category",      "string"),
    DataField("motivation",    "string"),
    DataField("share",         "number"),
]


@laureates.route('/')
def index():
    return render_template('index.html')


@laureates.route('/api/laureates', methods=['POST'])
def laureates_data():
    data = {}
    try:
        data = request.get_json()
        return jsonify(DataTables(mongo, "laureates", data, data_fields=DATA_FIELDS).get_rows())
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'error': str(e), 'data': [],
            'draw': data.get('draw', 1),
            'recordsTotal': 0, 'recordsFiltered': 0
        }), 500
