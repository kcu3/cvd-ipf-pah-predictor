"""Bounded spreadsheet import/export for the local web application."""
import csv
from datetime import datetime, timezone
from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from predictor import MODELS
from schema import DISEASES

MAX_ROWS = 2000
MAX_COLUMNS = 100


def read_upload(upload, disease):
    suffix = Path(upload.filename).suffix.lower()
    payload = upload.read()
    if not payload:
        raise ValueError('The uploaded file is empty.')
    if suffix not in ('.xlsx', '.csv'):
        raise ValueError('Use .xlsx or UTF-8 .csv. Save older .xls files as .xlsx first.')
    book = None
    try:
        if suffix == '.csv':
            try:
                rows = csv.reader(StringIO(payload.decode('utf-8-sig')), strict=True)
            except UnicodeDecodeError as exc:
                raise ValueError('Save the CSV using UTF-8 encoding.') from exc
        else:
            try:
                with ZipFile(BytesIO(payload)) as archive:
                    if sum(i.file_size for i in archive.infolist()) > 64 * 1024 * 1024:
                        raise ValueError('Expanded workbook exceeds 64 MB. Use a smaller file.')
                    if len(archive.infolist()) > 1000:
                        raise ValueError('Workbook has too many internal files.')
                book = load_workbook(BytesIO(payload), read_only=True, data_only=False, keep_links=False)
                sheet = book['Data'] if 'Data' in book.sheetnames else book.worksheets[0]
                # Ignore potentially stale dimensions in exported spreadsheets.
                sheet.reset_dimensions()
                rows = sheet.iter_rows(values_only=True)
            except (BadZipFile, KeyError, OSError) as exc:
                raise ValueError('Cannot read this workbook. Save it as a standard .xlsx file.') from exc
        header = next(rows, None)
        if header is None:
            raise ValueError('No header row found.')
        header = list(header)
        while header and header[-1] is None:
            header.pop()
        names = [str(h).strip() if h is not None else '' for h in header]
        if not names or len(names) > MAX_COLUMNS:
            raise ValueError('Expected 1–100 column headers in row 1.')
        if any(not h for h in names) or len(names) != len(set(names)):
            raise ValueError('Column headers must be nonempty and unique.')
        required = {f['name'] for f in DISEASES[disease]['fields']}
        missing = required-set(names)
        extra = set(names)-set(MODELS[disease]['features'])-{'patient_id'}
        if missing:
            raise ValueError('Missing required columns: ' + ', '.join(sorted(missing)))
        if extra:
            raise ValueError('Unrecognized columns: ' + ', '.join(sorted(extra)) + '. Use the selected disease template.')
        records = []
        for number, row in enumerate(rows, start=2):
            if number > MAX_ROWS+1:
                raise ValueError(f'Maximum {MAX_ROWS} data rows, including intervening blank rows. Split the file.')
            if any(v is not None and str(v).strip() for v in row[len(names):]):
                raise ValueError(f'Row {number} has data outside the named columns.')
            if not any(v is not None and str(v).strip() for v in row):
                continue
            if any(isinstance(v, str) and (len(v) > 32767 or ILLEGAL_CHARACTERS_RE.search(v)) for v in row):
                raise ValueError(f'Row {number} contains text that cannot be stored safely in Excel (control characters or over 32,767 characters).')
            padded = list(row[:len(names)]) + [None]*max(0, len(names)-len(row))
            records.append((number, dict(zip(names, padded))))
        if not records:
            raise ValueError('No data rows. Fill the Data sheet below the headers before uploading.')
        return names, records
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError('The spreadsheet could not be read. Check the file is a valid, unencrypted .xlsx or UTF-8 .csv.') from exc
    finally:
        if book is not None:
            book.close()


def append_values(sheet, values):
    sheet.append(values)
    # Prevent input identifiers/text from becoming executable Excel formulas.
    for cell in sheet[sheet.max_row]:
        if isinstance(cell.value, str):
            cell.data_type = 's'


def style_sheet(sheet, widths=None):
    sheet.freeze_panes = 'A2'
    sheet.auto_filter.ref = sheet.dimensions
    sheet.row_dimensions[1].height = 30
    for cell in sheet[1]:
        cell.fill = PatternFill('solid', fgColor='14213D')
        cell.font = Font(color='FFFFFF', bold=True)
        cell.alignment = Alignment(vertical='center', wrap_text=True)
    for column in range(1, sheet.max_column+1):
        width = widths.get(column, 22) if widths else 22
        sheet.column_dimensions[get_column_letter(column)].width = width
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical='top', wrap_text=True)


def encode(book):
    stream = BytesIO()
    book.save(stream)
    stream.seek(0)
    return stream


def input_dictionary(book, disease):
    sheet = book.create_sheet('Input dictionary')
    append_values(sheet, ['Column', 'Required', 'Meaning / units / coding', 'Accepted values', 'Missing value'])
    append_values(sheet, ['patient_id', 'No', 'Optional identifier; format as Text to preserve leading zeros', 'Text', 'Blank'])
    fields = {f['name']: f for f in DISEASES[disease]['fields']}
    for name in MODELS[disease]['features']:
        if name in fields:
            f = fields[name]
            rule = '; '.join(f'{v} = {label}' for v, label in f['options']) if f['type'] == 'select' else f"{f['min']} to {f['max']}"
            append_values(sheet, [name, 'Yes', f["label"] + ' — ' + f.get('unit', f['range_hint']), rule, 'Row rejected'])
        else:
            append_values(sheet, [name, 'No', 'Additional CVD feature: exact original training units/coding; not documented in supplied files',
                                  'Finite number', MODELS[disease]['medians'][name]])
    style_sheet(sheet, {1: 24, 2: 14, 3: 80, 4: 55, 5: 24})


def add_notes(book, disease, count=None):
    sheet = book.create_sheet('Read me')
    append_values(sheet, ['Item', 'Details'])
    entries = [
        ('Predictor', disease.upper()),
        ('Use', 'Research use only. Not validated for clinical decisions.'),
        ('Input sheet', 'The Data sheet is read if present; otherwise the first worksheet. Row 1 contains exact column names.'),
        ('Limits', f'{MAX_ROWS} data rows; 16 MB upload; .xlsx or UTF-8 comma-separated .csv. Formulas are rejected.'),
        ('Values', 'Use numeric training codes and the stated units. No automatic unit conversion. Core inputs cannot be blank.'),
        ('Sex coding', 'The original website uses different IPF/PAH sex codes. These mappings are preserved but not verified against training code.'),
        ('PAH creatinine', 'CREAT units are not documented in the supplied model bundle. Confirm with the training data dictionary.'),
        ('CVD missing inputs', 'Unprovided optional CVD features use the supplied training medians. Results name every imputed feature.'),
        ('Output interpretation', 'CVD: calibrated_probability is stored from 0 to 1 and displayed as a percentage. IPF/PAH: model_score is stored from 0 to 1 and displayed as a percentage (0–100%).'),
        ('Target', 'Supplied IPF/PAH metadata labels the outcome y10_proxy. Target construction and clinical validity cannot be established from model weights alone.'),
        ('Processing', 'Uploads are processed locally. This application does not retain uploaded files or results on disk.'),
    ]
    if count is not None:
        entries.extend([('Rows returned', count), ('Generated UTC', datetime.now(timezone.utc).isoformat())])
    for item in entries:
        append_values(sheet, item)
    style_sheet(sheet, {1: 28, 2: 110})
    for row in range(2, sheet.max_row+1):
        sheet.row_dimensions[row].height = 44


def template_workbook(disease):
    book = Workbook()
    sheet = book.active
    sheet.title = 'Data'
    required = [f['name'] for f in DISEASES[disease]['fields']]
    names = ['patient_id'] + required + [f for f in MODELS[disease]['features'] if f not in required]
    append_values(sheet, names)
    style_sheet(sheet)
    sheet.column_dimensions['A'].width = 25
    for f in DISEASES[disease]['fields']:
        column = get_column_letter(names.index(f['name'])+1)
        if f['type'] == 'select':
            options = ','.join(v for v, _ in f['options'])
            validation = DataValidation(type='list', formula1=f'"{options}"', allow_blank=False)
        else:
            validation = DataValidation(type='decimal', operator='between', formula1=f['min'], formula2=f['max'], allow_blank=False)
        validation.errorTitle = 'Invalid value'
        validation.error = 'Use the codes and ranges in Input dictionary.'
        validation.showErrorMessage = True
        validation.errorStyle = 'stop'
        sheet.add_data_validation(validation)
        validation.add(f'{column}2:{column}{MAX_ROWS+1}')
    input_dictionary(book, disease)
    add_notes(book, disease)
    return encode(book)


def result_workbook(disease, input_headers, results):
    book = Workbook()
    sheet = book.active
    sheet.title = 'Predictions'
    keys = ['source_row', 'status', 'error', 'calibrated_probability', 'model_score', 'imputed_count', 'imputed_features']
    append_values(sheet, keys + ['input_' + h for h in input_headers])
    for result in results:
        append_values(sheet, [result.get(k) for k in keys] + [result['input'].get(h) for h in input_headers])
    style_sheet(sheet, {3: 65, 4: 28, 7: 70})
    for row in sheet.iter_rows(min_row=2):
        row[3].number_format = '0.00%'
        row[4].number_format = '0.00%'
        if row[1].value == 'invalid':
            row[1].font = Font(color='9B2D2D', bold=True)
    add_notes(book, disease, len(results))
    input_dictionary(book, disease)
    return encode(book)
