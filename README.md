# mongo-datatables Flask Demo

A minimal Flask app demonstrating server-side DataTables powered by
[mongo-datatables](https://github.com/pjosols/mongo-datatables).

## Quickstart

1. Clone and install:
   ```bash
   git clone https://github.com/pjosols/flask-demo.git
   cd flask-demo
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Seed the database (requires MongoDB running locally):
   ```bash
   python seed_data.py
   ```

3. Run:
   ```bash
   cd app
   flask run
   ```

Open [http://localhost:5000](http://localhost:5000).

## Custom MongoDB connection

```bash
python seed_data.py --connection "mongodb://user:password@host:port/"
```

Set `MONGO_URI` in the environment to point the app at a different instance.

## Project structure

```
flask-demo/
├── app/
│   ├── __init__.py          # app factory
│   ├── app.py               # entry point
│   ├── config.py            # configuration
│   ├── laureates/
│   │   ├── __init__.py      # blueprint
│   │   └── routes.py        # views + API endpoint
│   ├── static/js/table.js   # DataTables init
│   ├── templates/index.html # page template
│   └── tools/db_init.py     # index creation
├── data/laureates.json      # Nobel Prize data (1901–present)
├── seed_data.py             # loads data into MongoDB
└── requirements.txt
```

## How it works

`routes.py` defines the data fields and passes the DataTables request to `mongo-datatables`:

```python
DATA_FIELDS = [
    DataField("name",          "string"),
    DataField("gender",        "string"),
    DataField("birth_country", "string"),
    DataField("year",          "number"),
    DataField("category",      "string"),
    DataField("motivation",    "string"),
    DataField("share",         "number"),
]

@laureates.route('/api/laureates', methods=['POST'])
def laureates_data():
    data = request.get_json()
    return jsonify(DataTables(mongo, "laureates", data, data_fields=DATA_FIELDS).get_rows())
```

`table.js` points DataTables at that endpoint:

```javascript
$('#laureates_table').DataTable({
    serverSide: true,
    ajax: {
        url: '/api/laureates',
        type: 'POST',
        contentType: 'application/json',
        data: function (d) { return JSON.stringify(d); }
    },
    columns: [
        { data: 'year' },
        { data: 'category' },
        { data: 'name' },
        // ...
    ]
});
```

That's the entire integration.

## License

MIT
