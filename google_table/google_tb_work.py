import gspread
from oauth2client.service_account import ServiceAccountCredentials
# from googleapiclient.discovery import build

from config import AUTH_GOOGLE
from loguru import logger
from datetime import datetime as dt


class RWGoogle:
    """
    Класс для чтения и запись данных из(в) Google таблицы(у)
    """
    def __init__(self):
        self.client_id = AUTH_GOOGLE['GOOGLE_CLIENT_ID']
        self.client_secret = AUTH_GOOGLE['GOOGLE_CLIENT_SECRET']
        self._scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self._credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'google_table/credentials.json', self._scope
            # 'credentials.json', self._scope
        )
        self._credentials._client_id = self.client_id
        self._credentials._client_secret = self.client_secret
        self._gc = gspread.authorize(self._credentials)
        self.key_wb = AUTH_GOOGLE['KEY_WORKBOOK']

    def read_sheets(self) -> list[str]:
        """
        Получает данные по всем страницам Google таблицы и возвращает список страниц в виде списка строк
        self.key_wb: id google таблицы.
            Идентификатор таблицы можно найти в URL-адресе таблицы.
            Обычно идентификатор представляет собой набор символов и цифр
            после `/d/` и перед `/edit` в URL-адресе таблицы.
        :return: list[str].
            [
            'Имя 1-ой страницы',
            'Имя 2-ой страницы',
            ...
            'Имя последней страницы'
            ]
        """
        result = []
        try:
            worksheets = self._gc.open_by_key(self.key_wb).worksheets()
            result = [worksheet.title for worksheet in worksheets]
        except gspread.exceptions.APIError as e:
            logger.error(f"Ошибка при получении списка имён страниц: {e}")
        except Exception as e:
            logger.error(f"Ошибка при получении списка имён страниц: {e}")
        return result

    def read_sheet(self, worksheet_id: int) -> list[list[str]]:
        """
        Получает данные из страницы Google таблицы по её идентификатору и возвращает значения в виде списка списков
        self.key_wb: id google таблицы.
            Идентификатор таблицы можно найти в URL-адресе таблицы.
            Обычно идентификатор представляет собой набор символов и цифр
            после `/d/` и перед `/edit` в URL-адресе таблицы.
        :return: List[List[str].
        """
        sheet = []
        try:
            sheet = self._gc.open_by_key(self.key_wb).get_worksheet(worksheet_id)
        except gspread.exceptions.APIError as e:
            logger.error(f"Ошибка при получении списка настроек: {e}")
        except Exception as e:
            logger.error(f"Ошибка при получении списка имён страниц: {e}")
        return sheet.get_all_values()

    def save_cell(self, worksheet_id: int, row: int, col: int, value: str):
        """Записываем данные в ячейку"""
        try:
            sheet = self._gc.open_by_key(self.key_wb).get_worksheet(worksheet_id)
            return sheet.update_cell(row, col, value)

        except gspread.exceptions.APIError as e:
            logger.error(f"Ошибка записи в ячейку: {e}")

        except Exception as e:
            logger.error(f"ООшибка записи в ячейку: {e}")

    def save_batch_old(self, worksheet_id: int, values: list[dict], all_rows: int = 0):
        """
        Записываем данные в разные ячейки
        :param all_rows: количество строк должно быть в таблице для записи
        :param worksheet_id: Номер вкладки
        :param values: [
            {'range': 'A1', 'values': [['Значение 1']]},
            {'range': 'B1', 'values': [['Значение 2']]},
            {'range': 'C1', 'values': [['Значение 3']]}
        ]
        :return:
        """
        try:
            sheet = self._gc.open_by_key(self.key_wb).get_worksheet(worksheet_id)

            if all_rows:
                # Определяем количество существующих строк на странице
                current_row_count = sheet.row_count
                if all_rows > current_row_count:
                    rows_to_add = all_rows - current_row_count
                    sheet.add_rows(rows_to_add)
                    logger.debug(f"Добавлено {rows_to_add} строк.")

            return sheet.batch_update(values)

        except gspread.exceptions.APIError as api_e:
            logger.error(f"Ошибка записи в ячейки: {api_e}")

        except Exception as ex:
            logger.error(f"Ошибка записи в ячейки: {ex}")

    def save_batch(self, worksheet_id: int, values: list[dict], all_rows: int = 0):
        """Записываем формулы"""
        try:
            # Добавляем строки при необходимости
            sheet = self._gc.open_by_key(self.key_wb).get_worksheet(worksheet_id)

            if all_rows:
                # Определяем количество существующих строк на странице
                current_row_count = sheet.row_count
                if all_rows > current_row_count:
                    rows_to_add = all_rows - current_row_count
                    sheet.add_rows(rows_to_add)
                    logger.debug(f"Добавлено {rows_to_add} строк.")

            # Записываем данные в таблицу
            # service = build('sheets', 'v4', credentials=self._credentials)
            #
            # body = {
            #     'valueInputOption': 'USER_ENTERED',
            #     'data': values
            # }
            #
            # request = service.spreadsheets().values().batchUpdate(spreadsheetId=self.key_wb, body=body)
            # response = request.execute()
            # logger.debug(f"Ответ API: {response}")

        except gspread.exceptions.APIError as api_e:
            logger.error(f"Ошибка записи в ячейки: {api_e}")

        except Exception as ex:
            logger.error(f"Ошибка записи в ячейки: {ex}")


class WorkGoogle:
    def __init__(self):
        self._rw_google = RWGoogle()

    def get_franchises(self) -> dict:
        """
        Получаем соответствие клиентов и менеджеров из Google таблицы
        :return: Словарь, где ключом является идентификатор клиента, а значением идентификатор менеджера
        """

        return {item[0]: item[2] for item in self._rw_google.read_sheet(6)[1:]}
