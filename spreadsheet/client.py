import csv

import gspread
from oauth2client.service_account import ServiceAccountCredentials


class SpreadsheetClient:
    def __init__(
        self,
        gcp_sa_key: str,
    ):
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        sa_cred = ServiceAccountCredentials.from_json_keyfile_name(gcp_sa_key, scopes)
        self.client = gspread.authorize(sa_cred)
        return

    def get_workbook(self, spreadsheet_key):
        workbook = self.client.open_by_key(spreadsheet_key)
        return workbook

    def get_worksheet(self, spreadsheet_key, spreadsheet_name):
        workbook = self.get_workbook(spreadsheet_key)
        worksheet = workbook.worksheet(spreadsheet_name)
        return worksheet

    def write_worksheet_csv(self, worksheet, file_path):
        with open(file_path, 'w', newline='') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerows(worksheet.get_all_values())
        return True
