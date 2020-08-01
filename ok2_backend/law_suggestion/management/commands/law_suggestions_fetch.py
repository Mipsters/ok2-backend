from django.core.management.base import BaseCommand

import mwparserfromhell as mwp

import requests
import typing
import json
import re
import math

from bs4 import BeautifulSoup
import threading

# from law_suggestion.models import Clause, ClauseVersion, Section, Chapter


class LegislationDBParser:

    KNESSET_LEGISLATION_DB_BASE = 'https://main.knesset.gov.il/Activity/Legislation/Laws/Pages/'
    KNESSET_LAW_SUGGESTIONS_SEARCH_URL = KNESSET_LEGISLATION_DB_BASE + 'LawSuggestionsSearch.aspx'

    def __init__(self):
        self.legislations_in_page = 1
        self.legislations_number = 1

        legislation_db_main_page = self._get_legislation_db_page()

        self.legislations_in_page = len(legislation_db_main_page.select_one('.rgMasterTable > tbody').findChildren("tr"))
        self.legislations_number = self._get_total_legislation_number(legislation_db_main_page)

    @property
    def pages_number(self) -> int:
        return math.ceil(self.legislations_number / self.legislations_in_page)

    def _get_legislation_db_page(self, page_number: int = 1) -> BeautifulSoup:
        if page_number < 1 or page_number > self.pages_number:
            raise ValueError(f"Legislation DB page out of range, page given: {page_number}")

        response = requests.get(self.KNESSET_LAW_SUGGESTIONS_SEARCH_URL, {
            't': 'LawSuggestionsSearch',
            'st': 'AllSuggestions',
            'pn': page_number
        })
        
        return BeautifulSoup(response.text, "lxml")

    def _get_total_legislation_number(self, legislation_db_main_page: BeautifulSoup) -> int:
        result_num_text = legislation_db_main_page.select_one('td.clsTotalRows > div > label').text
        matched_number = re.match('נמצאו ([0-9]+) תוצאות', result_num_text).group(1)

        return int(matched_number)

    def _get_law_suggestions_pages(self) -> typing.Generator[BeautifulSoup, None, None]:
        for page_index in range(1, self.pages_number):
            yield self._get_legislation_db_page(page_index)
    
    @staticmethod
    def get_law_suggestions_links(page: BeautifulSoup, num) -> typing.Generator[str, None, None]:
        for a in page.select("table.rgMasterTable > tbody > tr.rgRow >td:nth-child(2) > a"):
            print(str(num) + ' link')
            response = requests.get(LegislationDBParser.KNESSET_LEGISLATION_DB_BASE + a.attrs['href'])
            yield BeautifulSoup(response.text, "lxml")


def tmp(page, count):
    print('Page ' + str(count))
    list(LegislationDBParser.get_law_suggestions_links(page, count))

class Command(BaseCommand):
    help = 'Fetch the Knesset legislations suggestions from the Knesset website'

    def handle(self, *args, **kwargs):
        legislation_db_parser = LegislationDBParser()
        procs = []
        count = 0
        for page in legislation_db_parser._get_law_suggestions_pages():
            print('Thread ' + str(count))
            proc = threading.Thread(target=tmp, args=(page, count))
            procs.append(proc)
            proc.start()
            count = count + 1
        
        count = 0
        for proc in procs:
            print('Thread join ' + str(count))
            count = count + 1
            proc.join()
        
        print(legislation_db_parser.legislations_number)
