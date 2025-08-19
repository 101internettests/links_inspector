from datetime import datetime
from unittest.mock import patch, Mock

import pytest


@patch('multi_site_analyzer_main.requests.get')
def test_main_analyze_url_title_description(mock_get):
    html = b"""
    <html>
      <head>
        <title>OK</title>
        <meta name='description' content='Desc' />
        <meta name='description' content='error' />
      </head>
      <body>
        <h1>H1</h1>
        <h2> </h2>
      </body>
    </html>
    """
    mock_get.return_value = Mock(status_code=200, content=html)

    from multi_site_analyzer_main import analyze_url
    r = analyze_url('https://x')
    assert r['status'] == 'success'
    assert r['headings']['h1_non_empty'] == 1
    assert r['headings']['h2_non_empty'] == 0
    assert r['seo']['title_total'] == 1 and r['seo']['title_non_empty'] == 1
    assert r['seo']['description_total'] == 2 and r['seo']['description_non_empty'] == 1


def test_main_compare_headings_and_seo():
    from multi_site_analyzer_main import compare_headings
    prod = {'headings': {'h1_non_empty': 1, 'total_headings': 1}, 'seo': {'title_non_empty': 1, 'description_non_empty': 0}}
    stage = {'headings': {'h1_non_empty': 0, 'total_headings': 0}, 'seo': {'title_non_empty': 0, 'description_non_empty': 1}}
    c = compare_headings(prod, stage)
    assert c['h1_non_empty']['diff'] == -1
    assert c['total_headings']['diff'] == -1
    assert c['title_non_empty']['diff'] == -1
    assert c['description_non_empty']['diff'] == 1


def test_main_save_to_google_sheets_header(monkeypatch):
    captured = {}

    class DummySheets:
        def __init__(self, *args, **kwargs):
            pass
        def update_sheet(self, spreadsheet_id, range_name, values):
            captured['spreadsheet_id'] = spreadsheet_id
            captured['range_name'] = range_name
            captured['values'] = values

    import multi_site_analyzer_main as mod
    monkeypatch.setattr(mod, 'GoogleSheetsServiceAccount', DummySheets)
    monkeypatch.setattr(mod, 'SPREADSHEET_ID', 'TEST')
    monkeypatch.setattr(mod, 'SHEET_NAME', 'Лист')

    sample = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'prod_url': 'p', 'stage_url': 's',
        'prod_h1': 1, 'prod_h2': 0, 'prod_h3': 0, 'prod_h4': 0, 'prod_h5': 0, 'prod_h6': 0,
        'prod_total': 1, 'prod_total_all': 1,
        'stage_h1': 0, 'stage_h2': 0, 'stage_h3': 0, 'stage_h4': 0, 'stage_h5': 0, 'stage_h6': 0,
        'stage_total': 0, 'stage_total_all': 0,
        'h1_diff': -1, 'h2_diff': 0, 'h3_diff': 0, 'h4_diff': 0, 'h5_diff': 0, 'h6_diff': 0, 'total_diff': -1,
        'prod_title': 1, 'prod_title_all': 1, 'stage_title': 0, 'stage_title_all': 0, 'title_diff': -1,
        'prod_description': 0, 'prod_description_all': 0, 'stage_description': 1, 'stage_description_all': 1, 'description_diff': 1,
        'prod_error': None, 'stage_error': None,
    }
    mod.save_to_google_sheets([sample])

    header = captured['values'][0]
    assert 'Prod Title' in header and 'Description diff' in header
    assert len(captured['values']) == 2

