import re

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
    recipe_info = {}

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

    ingredient = get_ingredients(ingredients_content)
    seasoning = get_seasoning(ingredients_content)

    if seasoning:
        recipe_info["groups"] = [ingredient, seasoning]
    else:
        recipe_info["groups"] = [ingredient]
    recipe_info["steps"] = get_steps(soup)

    return recipe_info

def scrape_recipe(url):
    page = httpx.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    recipe = get_recipe_info(soup)

    print(json.dumps(recipe, ensure_ascii=False, indent=2))

    return recipe


if __name__ == "__main__":
    scrape_recipe("https://tasty-note.com/teriyaki-tofu-stake-2/")
    # scrape_recipe("https://tasty-note.com/orinishi-shio-kombu-cabbage/")
