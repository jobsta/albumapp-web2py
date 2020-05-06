def edit():
    """Shows a page with ReportBro Designer to edit our albums report template.

    The report template is loaded from the db (report_definition table),
    in case no report template exists a hardcoded template is generated in
    *create_album_report_template* for this Demo App. Normally you'd probably
    start with an empty report (empty string, so no report is loaded
    in the Designer) in this case.
    """
    rv = dict()
    rv['menu_items'] = get_menu_items('report')
    if db(db.report_definition.report_type == 'albums_report').count() == 0:
        create_album_report_template()

    # load ReportBro report definition stored in our report_definition table
    row = db(db.report_definition.report_type == 'albums_report').select(
        db.report_definition.id, db.report_definition.report_definition).first()
    rv['report_definition'] = json.dumps(row.report_definition)
    return rv


def run():
    """Generates a report for preview.

    This method is called by ReportBro Designer when the Preview button is clicked,
    the url is defined when initializing the Designer, see *reportServerUrl*
    in views/report/edit.html
    """
    import uuid
    from timeit import default_timer as timer
    from reportbro import Report, ReportBroError

    MAX_CACHE_SIZE = 10 * 1024 * 1024  # keep max. 10 MB of generated pdf files in db

    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, PUT, OPTIONS'
    response.headers[
        'Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, X-HTTP-Method-Override, Content-Type, Accept, Z-Key'
    if request.env.request_method == 'OPTIONS':
        # options request is usually sent by browser for a cross-site request, we only need to set the
        # Access-Control-Allow headers in the response so the browser sends the following get/put request
        return ''

    additional_fonts = []
    # add additional fonts here if additional fonts are used in ReportBro Designer

    output_format = request.vars.outputFormat
    if output_format not in ('pdf', 'xlsx'):
        raise HTTP(400, 'outputFormat parameter missing or invalid')

    if request.env.request_method == 'PUT':
        # all data needed for report preview is sent in the initial PUT request, it contains
        # the format (pdf or xlsx), the report itself (report_definition), the data (test data
        # defined within parameters in the Designer) and is_test_data flag (always True
        # when request is sent from Designer)
        report_definition = request.vars.report
        data = request.vars.data
        is_test_data = bool(request.vars.isTestData)
        try:
            report = Report(report_definition, data, is_test_data, additional_fonts=additional_fonts)
        except Exception as e:
            raise HTTP(400, 'failed to initialize report: ' + str(e))

        if report.errors:
            # return list of errors in case report contains errors, e.g. duplicate parameters.
            # with this information ReportBro Designer can select object containing errors,
            # highlight erroneous fields and display error messages
            return json.dumps(dict(errors=report.errors))
        try:
            # delete old reports (older than 3 minutes) to avoid table getting too big
            db(db.report_request.created_on < (request.now - datetime.timedelta(minutes=3))).delete()

            sum = db.report_request.pdf_file_size.sum()
            total_size = db().select(sum).first()[sum]
            if total_size and total_size > MAX_CACHE_SIZE:
                # delete all reports older than 10 seconds to reduce db size for cached pdf files
                db(db.report_request.created_on < (request.now - datetime.timedelta(seconds=10))).delete()

            start = timer()
            report_file = report.generate_pdf()
            end = timer()
            print('pdf generated in %.3f seconds' % (end-start))

            key = str(uuid.uuid4())
            # add report request into sqlite db, this enables downloading the report by url
            # (the report is identified by the key) without any post parameters.
            # This is needed for pdf and xlsx preview.
            db.report_request.insert(
                key=key, report_definition=json.dumps(report_definition),
                data=json.dumps(data, default=json_default), is_test_data=is_test_data,
                pdf_file=report_file, pdf_file_size=len(report_file), created_on=request.now)
            db.commit()

            return 'key:' + key
        except ReportBroError as err:
            # in case an error occurs during report generation a ReportBroError exception is thrown
            # to stop processing. We return this error within a list so the error can be
            # processed by ReportBro Designer.
            return json.dumps(dict(errors=[err.error]))

    elif request.env.request_method == 'GET':
        key = request.vars.key
        report = None
        report_file = None
        if key and len(key) == 36:
            # the report is identified by a key which was saved
            # in an table during report preview with a PUT request
            row = db(db.report_request.key == key).select(db.report_request.ALL).first()
            if not row:
                raise HTTP(400, 'report not found (preview probably too old), update report preview and try again')
            if output_format == 'pdf' and row['pdf_file']:
                report_file = row['pdf_file']
            else:
                report_definition = json.loads(row.report_definition)
                data = json.loads(row.data)
                is_test_data = row.is_test_data
                report = Report(report_definition, data, is_test_data, additional_fonts=additional_fonts)
                if report.errors:
                    raise HTTP(400, reason='error generating report')
        else:
            # in case there is a GET request without a key we expect all report data to be available.
            # this is NOT used by ReportBro Designer and only added for the sake of completeness.
            report_definition = request.vars.report
            data = request.vars.data
            is_test_data = bool(request.vars.isTestData)
            if not isinstance(report_definition, dict) or not isinstance(data, dict):
                raise HTTP(400, 'report_definition or data missing')
            report = Report(report_definition, data, is_test_data, additional_fonts=additional_fonts)
            if report.errors:
                raise HTTP(400, reason='error generating report')

        try:
            # once we have the reportbro.Report instance we can generate
            # the report (pdf or xlsx) and return it
            if output_format == 'pdf':
                if report_file is None:
                    # as it is currently implemented the pdf file is always stored in the
                    # report_request table along the other report data. Therefor report_file
                    # will always be set. The generate_pdf call here is only needed in case
                    # the code is changed to clear report_request.pdf_file column when the
                    # data in this table gets too big (currently whole table rows are deleted)
                    report_file = report.generate_pdf()
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = 'inline; filename="{filename}"'.format(
                    filename='report-' + str(request.now) + '.pdf')
            else:
                report_file = report.generate_xlsx()
                response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                response.headers['Content-Disposition'] = 'inline; filename="{filename}"'.format(
                    filename='report-' + str(request.now) + '.xlsx')
            return report_file
        except ReportBroError:
            raise HTTP(400, 'error generating report')
    return None


def save():
    """Save report_definition in our db table.

    This method is called by save button in ReportBro Designer.
    The url is called in *saveReport* callback from the Designer,
    see *saveCallback* in views/report/edit.html
    """
    report_type = request.args(0)
    if report_type != 'albums_report':
        #  currently we only support the albums report
        raise HTTP(400, 'report_type not supported')

    # perform some basic checks if all necessary fields for report_definition are present
    if 'docElements' not in request.vars or 'styles' not in request.vars or\
            'parameters' not in request.vars or\
            'documentProperties' not in request.vars or 'version' not in request.vars:
        raise HTTP(400, 'invalid request values')

    report_definition = dict(
        docElements=request.vars.docElements, styles=request.vars.styles, parameters=request.vars.parameters,
        documentProperties=request.vars.documentProperties, version=request.vars.version)

    if db(db.report_definition.report_type == report_type).count() == 0:
        db.report_definition.insert(
            report_type=report_type, report_definition=report_definition, last_modified_at=request.now)
    else:
        db(db.report_definition.report_type == report_type).update(
            report_definition=report_definition, last_modified_at=request.now)
    return json.dumps(dict(status='ok'))
