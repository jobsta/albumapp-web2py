def data():
    """Returns available albums from the database. Can be optionally filtered by year.

    This is called from views/album/index.html when the year input is changed.
    """
    year = None
    if request.vars.year:
        try:
            year = int(request.vars.year)
        except (ValueError, TypeError):
            raise HTTP(400, 'invalid year parameter')
    return json.dumps(get_albums(year), default=json_default)


def edit():
    """Shows an edit form to add new or edit an existing album."""
    rv = dict()
    rv['menu_items'] = get_menu_items('album')
    if request.args(0):
        try:
            album_id = int(request.args(0))
        except (ValueError, TypeError):
            raise HTTP(400, 'invalid argument')
        album = db(db.album.id == album_id).select(db.album.ALL).first()
        if not album:
            redirect(URL('album', 'index'))
        rv['is_new'] = False
        rv['album'] = json.dumps(album.as_dict())
    else:
        rv['is_new'] = True
        rv['album'] = json.dumps(dict(id='', name='', year=None, best_of_compilation=False))
    return rv


def index():
    """Shows a page where all available albums are listed."""
    rv = dict()
    rv['menu_items'] = get_menu_items('album')
    rv['albums'] = json.dumps(get_albums(), default=json_default)
    return rv


def report():
    """Prints a pdf file with all available albums.

    The albums can be optionally filtered by year. reportbro-lib is used to
    generate the pdf file. The data itself is retrieved
    from the database (*get_albums*). The report_definition
    is also stored in the database and is created on-the-fly if not present (to make
    this Demo App easier to use).
    """
    from reportbro import Report, ReportBroError

    year = None
    if request.vars.year:
        try:
            year = int(request.vars.year)
        except (ValueError, TypeError):
            raise HTTP(400, 'invalid year parameter')

    # NOTE: these params must match exactly with the parameters defined in the
    # report definition in ReportBro Designer, check the name and type (Number, Date, List, ...)
    # of those parameters in the Designer.
    params = dict(year=year, albums=get_albums(year), current_date=request.now)

    if db(db.report_definition.report_type == 'albums_report').count() == 0:
        create_album_report_template()

    report_definition = db(db.report_definition.report_type == 'albums_report').select(
        db.report_definition.id, db.report_definition.report_definition).first()
    if not report_definition:
        raise HTTP(500, 'no report_definition available')

    try:
        report = Report(report_definition.report_definition, params)
        if report.errors:
            # report definition should never contain any errors,
            # unless you saved an invalid report and didn't test in ReportBro Designer
            raise ReportBroError(report.errors[0])

        pdf_report = report.generate_pdf()
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename="albums.pdf"'
        return pdf_report
    except ReportBroError as ex:
        raise HTTP(500, 'report error: ' + str(ex.error))
    except Exception as ex:
        raise HTTP(500, 'report exception: ' + str(ex))


def save():
    """Saves a music album in the db."""
    album = request.vars.album
    if not isinstance(album, dict):
        raise HTTP(400, 'invalid values')
    album_id = None
    if album.get('id'):
        try:
            album_id = int(album.get('id'))
        except (ValueError, TypeError):
            raise HTTP(400, 'invalid album id')

    values = dict(best_of_compilation=album.get('best_of_compilation'))
    rv = dict(errors=[])

    # perform some basic form validation
    if not album.get('name'):
        rv['errors'].append(dict(field='name', msg=str(T('error.the field must not be empty'))))
    else:
        values['name'] = album.get('name')
    if not album.get('artist'):
        rv['errors'].append(dict(field='artist', msg=str(T('error.the field must not be empty'))))
    else:
        values['artist'] = album.get('artist')
    if album.get('year'):
        try:
            values['year'] = int(album.get('year'))
            if values['year'] < 1900 or values['year'] > 2100:
                rv['errors'].append(dict(field='year', msg=str(T('error.the field must contain a valid year'))))
        except (ValueError, TypeError):
            rv['errors'].append(dict(field='year', msg=str(T('error.the field must contain a number'))))
    else:
        values['year'] = None

    if not rv['errors']:
        # no validation errors -> save album
        if album_id:
            db(db.album.id == album_id).update(**values)
        else:
            db.album.insert(**values)
    return json.dumps(rv)


def get_albums(year=None):
    """Returns available albums from the database. Can be optionally filtered by year.

    This function is not callable from web request (because function has a parameter),
    only used within this controller.
    """
    filter_expr = (db.album.id > 0) if year is None else (db.album.year == year)
    return db(filter_expr).select(db.album.ALL, orderby=db.album.name).as_list()
