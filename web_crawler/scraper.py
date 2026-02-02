from entity import RecipeEntity
from bs4 import BeautifulSoup, Tag
from db_utils import PostgreDB, RecipeModel, RecipeChunkModel
from typing import List
import httpx, re


def get_tags(soup: BeautifulSoup) -> List[str]:
    return [tag.text for tag in soup.select_one('div[class="p-tags"]').find_all('a') if tag.text != "看影片學做菜"]

def get_steps(soup: BeautifulSoup) -> list:
    steps_tag = soup.select_one('section[class="l-single-recipe"]')
    return [
        {
            "img": step.select_one('img')['src'],
            "step": f"{step.select_one('span').text}. {step.select_one('p').text}",
        }
        for step in steps_tag.select('dl')
    ]

def get_seasoning(ingredients_content_tag: Tag) -> list:
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


def get_ingredients(ingredients_content_tag: Tag) -> list:
    return [
            {
                "name": items.select('p')[0].get_text(strip=True),
                "amount": items.select('p')[1].get_text(strip=True)
            }
            for items in ingredients_content_tag.select_one('dd[class="p-meet-dd"]').select('div[class="list"]')
        ]

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

    recipe_info["ingredients"] = get_ingredients(ingredients_content)
    seasoning = get_seasoning(ingredients_content)

    if seasoning:
        recipe_info["seasoning"] = seasoning

    recipe_info["steps"] = get_steps(soup)
    recipe_info["tags"] = get_tags(soup)

    return recipe_info

def scrape_recipe(url):
    page = httpx.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    recipe = get_recipe_info(soup)

    # print(json.dumps(recipe, ensure_ascii=False, indent=2))

    return recipe

def fetch_recipes(url):
    # with open("cookies.json", "r") as file:
    #     file = file.read()

    # soup = BeautifulSoup(file, "html.parser")

    page = httpx.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    recipes_tags = soup.select_one('main[class="p-main p-archive"]').select('article')

    return [
        recipe.select_one('a[class="u-loader"]')['href']
        for recipe in recipes_tags
    ]


def save_to_postgre(id, data):
    recipe = RecipeEntity(id, data)
    chunks = recipe.to_chunks()

    db = PostgreDB()
    db.add_recipe(RecipeModel(**recipe.to_document().to_dict()))
    for chunk in chunks:
        db.add_chunk(RecipeChunkModel(**chunk.to_dict()))

    db.commit()
    db.close()

if __name__ == "__main__":

    url = "https://tasty-note.com/teriyaki-tofu-stake-2/"
    data = scrape_recipe(url)

    # id = urlparse(url).path.split("/")[1]
    # fetch_recipes("https://tasty-note.com/tag/ten-minutes/1")
