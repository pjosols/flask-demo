$(function () {
    var editorAvailable = typeof $.fn.dataTable.Editor !== 'undefined';
    var editor;

    if (editorAvailable) {
        editor = new $.fn.dataTable.Editor({
            ajax: function(method, url, data, success, error) {
                var action = data.action;
                var ajaxUrl = '/api/editor/books';
                var ids = [];

                if (action === 'remove') {
                    if (data.id && data.id.length > 0) ids = data.id;
                    if (ids.length > 0) ajaxUrl += '?id=' + ids.join(',');
                } else if (action === 'edit') {
                    for (var id in data.data) {
                        if (data.data.hasOwnProperty(id)) ids.push(id);
                    }
                    if (ids.length > 0) ajaxUrl += '?id=' + ids.join(',');
                }

                $.ajax({
                    url: ajaxUrl, type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(data),
                    success: function(json) { success(json); table.ajax.reload(); },
                    error: function(xhr, status, err) { error(xhr, status, err); }
                });
            },
            table: '#novels_table',
            fields: [
                { label: "Artist",  name: "artist",  type: "text" },
                { label: "Title",   name: "title",   type: "text" },
                { label: "Label",   name: "label",   type: "text" },
                { label: "Year",    name: "year",    type: "text", attr: { type: "number" } },
                { label: "Genre",   name: "genre",   type: "select", multiple: true },
                { label: "Format",  name: "format",  type: "select" },
                { label: "Country", name: "country", type: "text" },
                { label: "Rating",  name: "rating",  type: "select" },
            ]
        });
    }

    var ajaxUrl = '/api/books';
    var highRatedActive = false;

    var tableConfig = {
        layout: {
            top1: 'searchBuilder',
            top:  'buttons',
            topStart: null,
            topEnd: 'search',
            bottomEnd: null,
            bottomStart: {
                rowClass: 'dt-info-row',
                features: ['info']
            },
        },
        searchBuilder: { depthLimit: 2 },
        serverSide:    true,
        processing:    true,
        stateSave:     true,
        stateSaveParams: function(settings, data) {
            // Don't persist column searches — footer inputs don't restore from state
            data.columns.forEach(function(col) { col.search.search = ''; });
            data.search.search = '';
        },
        scroller:      { rowHeight: 46 },
        scrollY:       '62vh',
        scrollCollapse: false,
        deferRender:   true,
        pageLength:    50,
        select:        true,
        rowId:         '_id',
        autoWidth:     false,
        order:         [[1, 'asc']],
        buttons: editorAvailable ? [
            { extend: 'create', editor: editor },
            { extend: 'edit',   editor: editor },
            { extend: 'remove', editor: editor }
        ] : [
            'copy', 'excel', 'pdf', 'print'
        ],
        ajax: function(data, callback) {
            var payload = Object.assign({}, data, {
                search: Object.assign({}, data.search, {
                    regex: $('#toggle-regex').is(':checked'),
                    caseInsensitive: !$('#toggle-case').is(':checked')
                }),
                columns: data.columns.map(function(col, i) {
                    if (i === 7 && highRatedActive) {
                        return Object.assign({}, col, { searchFixed: { essential: '4|' } });
                    }
                    return col;
                })
            });
            $.ajax({
                url: ajaxUrl, method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(payload),
                dataType: 'json',
                success: callback
            });
        },
        columns: [
            {
                // Cover art thumbnail
                data: 'coverUrl',
                orderable: false,
                searchable: false,
                width: '68px',
                className: 'dt-center',
                render: function(data, type, row) {
                    if (!data) {
                        return '<div class="cover-placeholder"><i class="bi bi-vinyl"></i></div>';
                    }
                    return '<img class="cover-thumb" src="' + data + '" alt="' + row.artist + '">';
                }
            },
            { data: 'artist', width: '14%' },
            { data: 'title',  width: '20%' },
            { data: 'label',  width: '13%' },
            { data: 'year',   width: '58px', className: 'dt-center' },
            {
                data: 'genre',
                orderable: false,
                width: '14%',
                render: function(data) {
                    if (!data) return '';
                    var arr = Array.isArray(data) ? data : [data];
                    return arr.map(function(g) {
                        return '<span class="genre-badge">' + g + '</span>';
                    }).join('');
                }
            },
            {
                data: 'format',
                width: '65px',
                className: 'dt-center',
                render: function(data) {
                    return data ? '<span class="format-badge">' + data + '</span>' : '';
                }
            },
            {
                data: 'rating',
                width: '90px',
                className: 'dt-center',
                render: function(data) {
                    if (data == null || data === 0) return '<span class="text-muted">—</span>';
                    var full = Math.floor(data), half = (data % 1) >= 0.5;
                    return '<span class="star-rating">' +
                        '★'.repeat(full) + (half ? '½' : '') +
                        '</span> <small class="text-muted">' + data.toFixed(1) + '</small>';
                }
            },
        ]
    };

    var table = $('#novels_table').DataTable(tableConfig);

    // Move SearchBuilder into the collapse container
    var $sbEl = $('#novels_table').closest('.dt-container').find('.dtsb-searchBuilder');
    if ($sbEl.length) {
        var $sbRow = $sbEl.closest('.dt-layout-row');
        $('#search-builder-collapse').append($sbEl);
        $sbRow.remove();
    }

    // Move DT buttons into sidebar export slot
    var $dtBtns = $('#novels_table').closest('.dt-container').find('.dt-buttons');
    if ($dtBtns.length) {
        var $btnRow = $dtBtns.closest('.dt-layout-row');
        $dtBtns.addClass('btn-group-sm w-100');
        $('#export-slot').append($dtBtns);
        $btnRow.remove();
    }

    // Move DT search into sidebar search slot
    var $dtSearch = $('#novels_table').closest('.dt-container').find('.dt-search');
    if ($dtSearch.length) {
        var $searchRow = $dtSearch.closest('.dt-layout-row');
        var $searchInput = $dtSearch.find('input').attr('placeholder', 'Search...').addClass('form-control-sm').detach();
        $dtSearch.find('label').remove();
        $('#search-slot').append($searchInput);
        if (!$searchRow.children().length) $searchRow.remove();
    }

    if (!editorAvailable) {
        $('#novels_table').closest('.card').after(
            '<div class="alert alert-info mt-3 small">' +
            '<strong>Note:</strong> Editing is disabled in this demo. ' +
            'Uncomment the Editor imports in books.html to enable it.' +
            '</div>'
        );
    }

    // Column footer search inputs
    var numericCols = [4, 7]; // Year, Rating
    table.columns().every(function() {
        var col = this;
        var idx = col.index();
        var footer = $(col.footer());
        if (idx === 0) return; // skip cover column

        var ph = numericCols.indexOf(idx) !== -1 ? 'min|max' : 'Search...';
        var input = $('<input type="text" class="form-control form-control-sm" placeholder="' + ph + '" />');
        footer.empty().append(input);
        var timer;
        input.on('input', function() {
            clearTimeout(timer);
            var val = this.value;
            timer = setTimeout(function() {
                if (col.search() !== val) col.search(val).draw();
            }, 300);
        });
    });

    // custom_filter toggle
    $('[data-url]').on('click', function() {
        $('[data-url]').removeClass('active');
        $(this).addClass('active');
        ajaxUrl = $(this).data('url');
        table.ajax.reload();
    });

    // Regex / case-sensitive toggles
    $('#toggle-regex, #toggle-case').on('change', function() {
        table.draw();
    });

    // searchFixed: essential records
    $('#btn-high-rated').on('click', function() {
        $(this).toggleClass('active');
        highRatedActive = $(this).hasClass('active');
        table.draw();
    });

    // Surface server errors
    table.on('xhr', function() {
        var json = table.ajax.json();
        if (json && json.error) {
            $('#server-error').text(json.error);
            $('#server-error-alert').removeClass('d-none');
        } else {
            $('#server-error-alert').addClass('d-none');
        }
    });
});
