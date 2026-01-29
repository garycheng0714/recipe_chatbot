import re
from unittest import result

import httpx, json
from bs4 import BeautifulSoup, Tag

def get_steps(soup: BeautifulSoup) -> list:
    steps_tag = soup.select_one('section[class="l-single-recipe"]')
    return [
        {
            "img": step.select_one('img')['src'],
            "step": f"{step.select_one('span').text}. {step.select_one('p').text}",
        }
        for step in steps_tag.select('dl')
    ]

def get_seasoning(ingredients_content_tag: Tag) -> dict:
    seasoning = {}

    if ingredients_content_tag.select_one('dd[class="p-meet-dd u-bg-white"]'):
        seasoning = {
            "group": "seasonings",
            "items": [
                {
                    "name": items.select_one('p').get_text(strip=True),
                    "amount": items.select_one('div').get_text(strip=True)
                }
                for items in
                ingredients_content_tag.select_one('dd[class="p-meet-dd u-bg-white"]').select('div[class="list"]')
            ]
        }

    return seasoning


def get_ingredients(ingredients_content_tag: Tag) -> dict:
    return {
        "group": "ingredients",
        "items": [
            {
                "name": items.select('p')[0].get_text(strip=True),
                "amount": items.select('p')[1].get_text(strip=True)
            }
            for items in ingredients_content_tag.select_one('dd[class="p-meet-dd"]').select('div[class="list"]')
        ]
    }

def get_recipe_info(soup: BeautifulSoup) -> dict:
    result = {}

    result["name"] = soup.select_one('h1[class="l-single-header__title"]').text.strip()
    result["category"] = soup.select_one('span[class="l-single-header__tag"]').text.strip()
    result["description"] = soup.select_one('section[class="l-single-content"]').text.strip()

    ingredients_content = soup.select_one('section[class="l-single-meet"]')

    quantity = re.sub(
        re.compile(f'[()（）]'),
        "",
        ingredients_content.select_one("h2 span").get_text(strip=True)
    )

    result["quantity"] = quantity

    ingredient = get_ingredients(ingredients_content)
    seasoning = get_seasoning(ingredients_content)

    if seasoning:
        result["groups"] = [ingredient, seasoning]
    else:
        result["groups"] = [ingredient]
    result["steps"] = get_steps(soup)

    return result

def scrape_recipe(url):
    page = httpx.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    result = get_recipe_info(soup)

    print(json.dumps(result, ensure_ascii=False, indent=2))




if __name__ == "__main__":
    scrape_recipe("https://tasty-note.com/teriyaki-tofu-stake-2/")
    # scrape_recipe("https://tasty-note.com/orinishi-shio-kombu-cabbage/")
