from typing import List
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Tag

from web_crawler.detail_crawler import BaseDetailCrawler
from web_crawler.exceptions import ContentParsingError
from web_crawler.schema.tasty_note_detail_schema import TastyNoteRecipe
import re


class TastyNoteDetailCrawler(BaseDetailCrawler):

    def crawl(self, html) -> TastyNoteRecipe:
        try:
            soup = self.get_soup(html)
            recipe = self._get_recipe_info(soup)
            return TastyNoteRecipe(**recipe)
        except Exception as e:
            raise ContentParsingError(f"TastyNote 詳情頁解析失敗: {str(e)}")

    def _get_url(self, soup: BeautifulSoup) -> str:
        return soup.select_one('link[rel="canonical"]')['href']

    def _get_id(self, soup: BeautifulSoup) -> str:
        link = self._get_url(soup)
        id = urlparse(link).path.split("/")[1]
        return id

    def _get_tags(self, soup: BeautifulSoup) -> List[str]:
        return [tag.text for tag in soup.select_one('div[class="p-tags"]').find_all('a') if tag.text != "看影片學做菜"]


    def _get_steps(self, soup: BeautifulSoup) -> list:
        steps_tag = soup.select_one('section[class="l-single-recipe"]')
        return [
            {
                "img": step.select_one('img')['src'],
                "step": f"{step.select_one('span').text}. {step.select_one('p').text}",
            }
            for step in steps_tag.select('dl')
        ]


    def _get_seasoning(self, ingredients_content_tag: Tag) -> list:
        seasoning = []

        if ingredients_content_tag.select_one('dd[class="p-meet-dd u-bg-white"]'):
            seasoning = [
                {
                    "name": items.select_one('p').get_text(strip=True),
                    "amount": items.select_one('div').get_text(strip=True)
                }
                for items in
                ingredients_content_tag.select_one('dd[class="p-meet-dd u-bg-white"]').select('div[class="list"]')
            ]

        return seasoning


    def _get_ingredients(self, ingredients_content_tag: Tag) -> list:
        return [
            {
                "name": items.select('p')[0].get_text(strip=True),
                "amount": items.select('p')[1].get_text(strip=True)
            }
            for items in ingredients_content_tag.select_one('dd[class="p-meet-dd"]').select('div[class="list"]')
        ]

    def _get_recipe_info(self, soup: BeautifulSoup) -> dict:
        recipe_info = {}

        recipe_info["id"] = self._get_id(soup)
        recipe_info["source_url"] = self._get_url(soup)
        recipe_info["name"] = soup.select_one('h1[class="l-single-header__title"]').text.strip()
        recipe_info["category"] = soup.select_one('span[class="l-single-header__tag"]').text.strip()
        recipe_info["description"] = soup.select_one('section[class="l-single-content"]').text.strip()

        ingredients_content = soup.select_one('section[class="l-single-meet"]')

        quantity = re.sub(
            re.compile(f'[()（）]'),
            "",
            ingredients_content.select_one("h2 span").get_text(strip=True)
        )

        recipe_info["quantity"] = quantity

        recipe_info["ingredients"] = self._get_ingredients(ingredients_content)
        seasoning = self._get_seasoning(ingredients_content)

        if seasoning:
            recipe_info["seasoning"] = seasoning

        recipe_info["steps"] = self._get_steps(soup)
        recipe_info["tags"] = self._get_tags(soup)

        return recipe_info