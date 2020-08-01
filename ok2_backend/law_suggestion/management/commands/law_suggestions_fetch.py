from django.core.management.base import BaseCommand

import mwparserfromhell as mwp

import requests
import typing
import json
import re
import math

from bs4 import BeautifulSoup

# from law_suggestion.models import Clause, ClauseVersion, Section, Chapter


class LegislationDBParser:

    KNESSET_LEGISLATION_DB_URL = 'https://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawSuggestionsSearch.aspx'
    legislations_in_page = 1
    legislations_number = 1

    def __init__(self):
        legislation_db_main_page = self._get_legislation_db_page()

        self.legislations_in_page = len(legislation_db_main_page.select_one('.rgMasterTable > tbody').findChildren("tr"))
        self.legislations_number = self._get_total_legislation_number(legislation_db_main_page)

    @property
    def pages_number(self):
        return math.ceil(self.legislations_number / self.legislations_in_page)

    def _get_legislation_db_page(self, page_number: int = 1) -> BeautifulSoup:
        if page_number < 1 or page_number > self.pages_number:
            raise ValueError(f"Legislation DB page out of range, page given: {page_number}")

        response = requests.get(self.KNESSET_LEGISLATION_DB_URL, {
            't': 'LawSuggestionsSearch',
            'st': 'AllSuggestions',
            'pn': page_number
        })
        
        return BeautifulSoup(response.text, "lxml")

    def _get_total_legislation_number(self, legislation_db_main_page):
        result_num_text = legislation_db_main_page.select_one('td.clsTotalRows > div > label').text
        matched_number = re.match('נמצאו ([0-9]+) תוצאות', result_num_text).group(1)

        return int(matched_number)


class Command(BaseCommand):
    help = 'Fetch the Knesset legislations suggestions from the Knesset website'

    def handle(self, *args, **kwargs):
        legislation_db_parser = LegislationDBParser()
        print(legislation_db_parser.legislations_number)
