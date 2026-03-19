from flask import render_template, request, jsonify
from mongo_datatables import DataTables, DataField
from app import mongo
from app.laureates import laureates

DATA_FIELDS = [
    DataField("name",         "string"),
    DataField("country_code", "keyword"),
    DataField("feature_code", "keyword"),
    DataField("admin1_code",  "keyword"),
    DataField("population",   "number"),
    DataField("timezone",     "string"),
    DataField("latitude",     "number"),
    DataField("longitude",    "number"),
]


@laureates.route('/')
def index():
    return render_template('index.html')


@laureates.route('/api/places', methods=['POST'])
def places_data():
    data = {}
    try:
        data = request.get_json()
        return jsonify(DataTables(mongo, "places", data, data_fields=DATA_FIELDS).get_rows())
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'error': str(e), 'data': [],
            'draw': data.get('draw', 1),
            'recordsTotal': 0, 'recordsFiltered': 0
        }), 500
