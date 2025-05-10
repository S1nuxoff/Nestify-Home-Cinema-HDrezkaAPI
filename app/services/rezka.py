import requests
from bs4 import BeautifulSoup
import re
import base64
import datetime
import urllib.parse
from app.utils.utils import check_video_exists, get_imdb_id
from app.services.themoviedb import get_themoviedb_movie


HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

COOKIES = {
    "dle_user_taken": "1",
    "dle_user_token": "f180bd36dc008da51faad98427b570d0",
    "_ym_uid": "170013727236723950",
    "_ym_d": "1707264293",
    "newest_tab": "1",
    "PHPSESSID": "j84n05bk59vvi1re6p6g623i8n",
    "_ym_isad": "1",
    "_clck": "kjpfz3%7C2%7Cfjv%7C0%7C1526",
    "_ym_visorc": "b",
    "_clsk": "xqz05e%7C1709773264570%7C5%7C1%7Cv.clarity.ms%2Fcollect",
}


def extract_id_from_url(url: str) -> str:
    """
    Извлекает ID из URL, если HTML-элемент отсутствует.
    """
    parts = url.strip("/").split("/")
    for part in reversed(parts):
        match = re.search(r"(\d+)", part)
        if match:
            return match.group(1)
    return ""


def safe_get_film_id(soup: BeautifulSoup, url: str) -> str:
    """
    Безопасно получает film_id — либо из DOM, либо из URL.
    """
    tag = soup.select_one(".b-sidelinks__link")
    if tag and tag.get("data-id"):
        return tag["data-id"]
    return extract_id_from_url(url)


async def get_page(url):
    """
    Парсит главную страницу (новые фильмы) и сохраняет данные.
    Возвращает список фильмов с типом 'newest-card'.
    """
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    newest_films = []
    film_items = soup.select(".b-content__inline_items .b-content__inline_item")

    for element in film_items:
        a_tag = element.select_one(".b-content__inline_item-link a")
        if not a_tag or not a_tag.get("href"):
            continue
        # Формируем ссылку (предполагается, что нужно добавить базовый URL)
        film_link = a_tag.get("href")

        img_tag = element.select_one(".b-content__inline_item-cover a img")
        film_image = img_tag.get("src") if img_tag else ""

        film_title = a_tag.get_text(strip=True)
        desc_div = element.select_one(".b-content__inline_item-link div")
        film_description = desc_div.get_text(strip=True) if desc_div else ""

        film_type = "newest-card"
        film_id = film_link.rstrip("/").split("/")[-1]

        film_object = {
            "filmLink": film_link,
            "filmImage": film_image,
            "filmName": film_title,
            "filmDecribe": film_description,
            "type": film_type,
            "filmId": film_id,
        }

        # Проверяем на дублирование по filmId
        if not any(existing.get("filmId") == film_id for existing in newest_films):
            newest_films.append(film_object)

    return newest_films


async def search(url):
    """
    Парсит страницу поиска фильмов.
    Возвращает список фильмов с типом 'search-card'.
    """
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    films = []
    film_items = soup.select(".b-content__inline_item")

    for element in film_items:
        film_type = "search-card"
        a_tag = element.select_one("div.b-content__inline_item-link a")
        film_name = a_tag.get_text(strip=True) if a_tag else ""

        desc_div = element.select_one("div.b-content__inline_item-link div")
        film_decribe = desc_div.get_text(strip=True) if desc_div else ""

        film_id = element.get("data-id") or extract_id_from_url(film_link)

        link_tag = element.find("a")
        film_link = link_tag.get("href") if link_tag else ""
        img_tag = element.find("img")
        film_image = img_tag.get("src") if img_tag else ""

        film_object = {
            "filmName": film_name,
            "filmId": film_id,
            "filmLink": film_link,
            "filmImage": film_image,
            "filmDecribe": film_decribe,
            "type": film_type,
        }

        if not any(existing.get("filmId") == film_id for existing in films):
            films.append(film_object)

    # Обновляем файл данных, добавляя новые записи без дубликатов

    return films


async def get_search(title):
    response = requests.post(
        "https://hdrezka.ag/engine/ajax/search.php", headers=HEADERS, data={"q": title}
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    films = []

    list_items = soup.select(".b-search__section_list > li")

    for li in list_items:
        a_tag = li.select_one("a")
        title_tag = li.select_one("span.enty")

        if a_tag and title_tag:
            # Вся строка текста внутри <a> (включает title, description и rating)
            full_text = a_tag.get_text(" ", strip=True)
            title_text = title_tag.get_text(strip=True)

            # Description — это весь текст после названия
            # Удаляем title из full_text, остальное — description
            description = full_text.replace(title_text, "", 1).strip()

            films.append(
                {
                    "title": title_text,
                    "description": description,
                    "filmLink": a_tag["href"],
                }
            )

    return {"results": films}


async def film_poster_parser(url):
    """
    Парсит страницу постера фильма и возвращает URL постера.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        img_tag = soup.select_one(
            "article.shortstory div.short span.like-count-wrap a.fancybox img"
        )
        film_poster_url = img_tag.get("src") if img_tag else ""
        return {"filmPosterUrl": film_poster_url}
    except Exception as e:
        print("Error in film_poster_parser:", e)
        raise


async def get_movie_ifo(url):
    """
    Парсит детальную информацию о фильме.
    Возвращает список (обычно с одним элементом) с информацией о фильме.
    """
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    film_info = []

    film_image_tag = soup.select_one("div.b-sidecover a")
    film_image = film_image_tag.get("href") if film_image_tag else ""

    duration_tag = soup.select_one('td[itemprop="duration"]')
    duration = duration_tag.get_text(strip=True).rstrip(".") if duration_tag else ""

    trailer_tag = soup.select_one("div.ps-trailer-player iframe")
    trailer = trailer_tag.get("src") if trailer_tag else ""
    trailer = check_video_exists(trailer)
    body_html = str(soup.body) if soup.body else ""
    match = re.search(r"sof\.tv\.[^\.]*\((\d+), (\d+), (\d+), (\d+)", body_html)

    film_rate_tag = soup.select_one(".b-post__rating span span")
    film_rate = film_rate_tag.get_text(strip=True) if film_rate_tag else ""

    film_id = safe_get_film_id(soup, url)

    name_film_tag = soup.select_one("div.b-post__title h1")
    name_film = name_film_tag.get_text(strip=True) if name_film_tag else ""

    name_origin_film_tag = soup.select_one("div.b-post__origtitle")
    name_origin_film = (
        name_origin_film_tag.get_text(strip=True) if name_origin_film_tag else ""
    )

    description_tag = soup.select_one("div.b-post__description_text")
    description = description_tag.get_text(strip=True) if description_tag else ""

    ctrl_favs = soup.select_one("#ctrl_favs")
    ctrl_favs_value = ctrl_favs.get("value") if ctrl_favs else ""

    translator_ids = []
    translator_elements = soup.select(".b-translator__item")
    for element in translator_elements:
        translator_id = element.get("data-translator_id", "")
        translate_name = element.get_text(strip=True)
        translate_object = {
            "translator_id": translator_id,
            "translateName": translate_name,
        }
        if translator_id or translate_name:
            translator_ids.append(translate_object)

    season_ids = []
    season_elements = soup.select(".simple-seasons-tabs .b-simple_season__item")
    for element in season_elements:
        season_id = element.get("data-tab_id")
        if season_id:
            season_ids.append(season_id)

    episodes = []
    episode_elements = soup.select(".b-simple_episodes__list .b-simple_episode__item")
    for element in episode_elements:
        season_id = element.get("data-season_id")
        episode_id = element.get("data-episode_id")
        if season_id and episode_id:
            episodes.append({"season_id": season_id, "episode_id": episode_id})

    action = (
        "get_movie"
        if match and "initCDNMoviesEvents" in match.group(0)
        else "get_stream"
    )

    film_object = {
        "film_image": film_image,
        "action": action,
        "duration": duration,
        "film_id": film_id,
        "name_film": name_film,
        "name_origin_film": name_origin_film,
        "translator_ids": translator_ids,
        "translatorName": [],  # Оставлено для совместимости с оригиналом
        "season_ids": season_ids,
        "episodes": episodes,
        "film_rate": film_rate,
        "film_description": description,
        "trailer": trailer,
        "favs": ctrl_favs_value,
    }

    if not any(existing.get("film_id") == film_id for existing in film_info):
        film_info.append(film_object)

    return film_info


def parse_schedule_tables(soup: BeautifulSoup) -> list:
    schedule_tables = soup.select(".b-post__schedule_table")
    if not schedule_tables:
        return []
    seasons_dict = {}
    for table in schedule_tables:
        rows = table.select("tr")
        for row in rows:
            td1 = row.select_one(".td-1")
            if not td1:
                continue
            text_td1 = td1.get_text(strip=True)
            match_se_ep = re.search(
                r"(\d+)\s+сезон\s+(\d+)\s+серия", text_td1, re.IGNORECASE
            )
            if not match_se_ep:
                continue
            season_number = int(match_se_ep.group(1))
            episode_number = int(match_se_ep.group(2))
            episode_id = td1.get("data-id", "")
            td2 = row.select_one(".td-2")
            title = (
                td2.find("b").get_text(strip=True) if td2 and td2.find("b") else None
            )
            original_title = (
                td2.find("span").get_text(strip=True)
                if td2 and td2.find("span")
                else None
            )
            td4 = row.select_one(".td-4")
            air_date = td4.get_text(strip=True) if td4 else None
            episode_obj = {"episode_number": episode_number, "episode_id": episode_id}
            if title:
                episode_obj["title"] = title
            if original_title:
                episode_obj["original_title"] = original_title
            if air_date:
                episode_obj["air_date"] = air_date
            if season_number not in seasons_dict:
                seasons_dict[season_number] = []
            seasons_dict[season_number].append(episode_obj)
    result_seasons = []
    for s_num, episodes_list in sorted(seasons_dict.items()):
        episodes_sorted = sorted(episodes_list, key=lambda e: e["episode_number"])
        result_seasons.append({"season_number": s_num, "episodes": episodes_sorted})
    return result_seasons


def get_basic_data(soup: BeautifulSoup, url: str) -> dict:

    source_link_element = soup.select_one("div.b-sidecover a")
    source_link = source_link_element["href"] if source_link_element else None
    duration_element = soup.find("td", itemprop="duration")
    duration = duration_element.text.strip() if duration_element else None
    match_data = re.search(r"sof\.tv\.([^.]*)\((\d+), (\d+), (\d+), (\d+)", str(soup))
    rate_element = soup.select_one(".b-post__rating span span")
    rate = rate_element.text if rate_element else None
    film_id = safe_get_film_id(soup, url)
    title_element = soup.select_one("div.b-post__title h1")
    title = title_element.text if title_element else None
    origin_name_element = soup.select_one("div.b-post__origtitle")
    origin_name = origin_name_element.text if origin_name_element else None
    description_element = soup.select_one("div.b-post__description_text")
    description = description_element.text if description_element else None
    ctrl_favs_value_element = soup.select_one("#ctrl_favs")
    ctrl_favs_value = (
        ctrl_favs_value_element["value"] if ctrl_favs_value_element else None
    )

    # imdb_link = soup.select_one("span.b-post__info_rates.imdb a")
    # imdb_url = imdb_link.get("href") if imdb_link else None
    # if imdb_url:
    #     imdb_id = get_imdb_id(imdb_url)
    # else:
    #     imdb_id: None

    return {
        "source_link": source_link,
        "duration": duration,
        "match_data": match_data,
        "rate": rate,
        "film_id": film_id,
        "title": title,
        "origin_name": origin_name,
        "description": description,
        "ctrl_favs_value": ctrl_favs_value,
        # "imdb_id": imdb_id,
    }


def get_translators(soup: BeautifulSoup) -> list:
    translators = []
    for item in soup.select(".b-translator__item"):
        t_id = item.get("data-translator_id", "")
        t_name = item.get_text(strip=True)
        translators.append({"id": t_id, "name": t_name})
    return translators


def get_action(soup: BeautifulSoup) -> str:
    return "get_movie" if "initCDNMoviesEvents" in str(soup) else "get_stream"


def get_season_ids(soup: BeautifulSoup) -> list:
    season_ids = []
    for element in soup.select(".simple-seasons-tabs .b-simple_season__item"):
        sid = element.get("data-tab_id")
        if sid:
            season_ids.append(sid)
    return season_ids


def get_simple_episodes(soup: BeautifulSoup) -> list:
    episodes = []
    for ep in soup.select(".b-simple_episodes__list .b-simple_episode__item"):
        season_id = ep.get("data-season_id")
        episode_id = ep.get("data-episode_id")
        if season_id and episode_id:
            episodes.append({"season_id": season_id, "episode_id": episode_id})
    return episodes


def get_trailer(film_id: str) -> str:
    trailer = None
    if film_id:
        trailer_data = {"id": film_id}
        trailer_response = requests.post(
            "https://rezka.ag/engine/ajax/gettrailervideo.php",
            cookies=COOKIES,
            headers=HEADERS,
            data=trailer_data,
        )
        if trailer_response.status_code == 200:
            trailer_src = trailer_response.json()
            code_parameter = trailer_src.get("code")
            if code_parameter:
                trailer = code_parameter.replace(
                    '<iframe width="640" height="360" src="', ""
                ).replace(
                    '" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="background: transparent; position: relative;"></iframe>',
                    "",
                )
    return trailer or ""


def get_source(
    film_id: str,
    translators: list,
    season_from_url: int,
    episode_from_url: int,
    episodes: list,
    ctrl_favs_value: str,
    action: str,
    params: dict,
) -> list:
    filtered_urls = []
    for translator in translators:
        current_translate_id = translator["id"]
        current_translate_name = translator["name"]
        if season_from_url is not None and episode_from_url is not None:
            season_val = season_from_url
            episode_val = episode_from_url
        elif episodes:
            chosen_episode = episodes[0]
            season_val = int(chosen_episode["season_id"])
            episode_val = int(chosen_episode["episode_id"])
        else:
            season_val = 0
            episode_val = 0
        film_data = {
            "id": film_id,
            "translator_id": current_translate_id,
            "favs": ctrl_favs_value,
            "action": action,
            "season": season_val,
            "episode": episode_val,
        }
        film_source_resp = requests.post(
            "https://rezka.ag/ajax/get_cdn_series/",
            params=params,
            cookies=COOKIES,
            headers=HEADERS,
            data=film_data,
        )
        if film_source_resp.status_code == 200:
            json_link_data = film_source_resp.json()
            if "url" not in json_link_data:
                continue
            url_value = json_link_data["url"]
            if not isinstance(url_value, str):
                continue
            trash_list = [
                "//_//QEBAQEAhIyMhXl5e",
                "//_//Xl5eIUAjIyEhIyM=",
                "//_//JCQhIUAkJEBeIUAjJCRA",
                "//_//IyMjI14hISMjIUBA",
                "//_//JCQjISFAIyFAIyM=",
            ]
            newlink = url_value
            for titem in trash_list:
                newlink = newlink.replace(titem, "")
            for titem in trash_list:
                newlink = newlink.replace(titem, "")
            newdata = newlink.replace("#h", "")
            try:
                decoded_url = base64.urlsafe_b64decode(newdata).decode("utf-8")
            except Exception:
                decoded_url = ""
            pattern = r"(\[.*?\])(\bhttps?://\S+\.mp4\b)"
            matches = re.findall(pattern, decoded_url)
            source_links = []
            if matches:
                for match_item in matches:
                    quality = (
                        match_item[0]
                        .replace("[", "")
                        .replace("]", "")
                        .replace(" ", "_")
                    )
                    video_url = match_item[1]
                    source_links.append({"quality": quality, "url": video_url})
            translate_entry = {
                "translate_id": current_translate_id,
                "translate_name": current_translate_name,
                "source_links": source_links,
            }
            filtered_urls.append(translate_entry)
    return filtered_urls


def parse_info_table(soup: BeautifulSoup) -> dict:
    """
    Ищет таблицу с классом .b-post__info и извлекает:
    - дата выхода (release_date)
    - страна (country)
    - жанр (genre)
    - режиссер (director)
    - возраст (age)

    Возвращает словарь вида:
    {
      "release_date": "...",
      "country": "...",
      "genre": ["...", "..."],
      "director": ["...", "..."],
      "age": "0+",
    }
    """
    result = {
        "release_date": None,
        "country": None,
        "genre": [],
        "director": [],
        "age": None,
    }

    info_table = soup.select_one(".b-post__info")
    if not info_table:
        return result

    # Идём по всем <tr>, смотрим, что написано в <td class="l"><h2>...</h2>
    rows = info_table.select("tr")
    for row in rows:
        header_td = row.select_one("td.l h2")
        if not header_td:
            continue
        header_text = header_td.get_text(strip=True).lower()

        # Второй <td> - там сами данные
        data_td = row.select_one("td:not(.l)")
        if not data_td:
            continue
        # Содержимое второго столбца
        data_text = data_td.get_text(" ", strip=True)

        # Смотрим, какой это параметр
        if "дата выхода" in header_text:
            # Пример: "28 ноября 1947 года"
            result["release_date"] = data_text

        elif "страна" in header_text:
            # Пример: "США"
            result["country"] = data_text

        elif "жанр" in header_text:
            # Пример: "Комедии, Семейные, Короткометражные, Зарубежные"
            # но обычно это ссылки. Мы можем взять .get_text(" ", strip=True) и split.
            # Или собрать текст из каждого <a>
            # Ниже пример, как вытащить названия жанров из ссылок
            genre_links = data_td.select("a span[itemprop='genre']")
            if genre_links:
                genres = []
                for g in genre_links:
                    genres.append(g.get_text(strip=True))
                result["genre"] = genres
            else:
                # fallback, берем весь text
                result["genre"] = data_text.split(",")

        elif "режиссер" in header_text:
            # Пример: "Джек Ханна"
            # На сайте может быть несколько режиссёров
            # Ищем .person-name-item
            directors = []
            director_items = data_td.select(".person-name-item span[itemprop='name']")
            for di in director_items:
                d_name = di.get_text(strip=True)
                directors.append(d_name)
            # Если ничего не нашли, fallback из data_text
            if not directors and data_text:
                directors = [data_text]
            result["director"] = directors

        elif "возраст" in header_text:
            # Пример: "0+ можно смотреть всей семьей..."
            # Можно сплитить, или просто взять первую часть до пробела
            # Или взять из <span class="bold" style="color: #666;">0+</span>
            age_span = data_td.select_one("span.bold")
            if age_span:
                result["age"] = age_span.get_text(strip=True)
            else:
                # fallback
                result["age"] = data_text

    return result


async def get_movie(url: str) -> dict:
    parsed_url = urllib.parse.urlparse(url)
    fragment = parsed_url.fragment
    season_from_url = None
    episode_from_url = None
    if fragment:
        frag_match = re.search(r"s:(\d+)-e:(\d+)", fragment)
        if frag_match:
            season_from_url = int(frag_match.group(1))
            episode_from_url = int(frag_match.group(2))

    current_time = datetime.datetime.now()
    params = {"t": current_time}
    response = requests.get(url, cookies=COOKIES, headers=HEADERS)
    if response.status_code != 200:
        return {}

    soup = BeautifulSoup(response.content, "html.parser")

    basic_data = get_basic_data(soup, url)

    translators = get_translators(soup)
    action = get_action(soup)
    season_ids = get_season_ids(soup)
    episodes_schedule = parse_schedule_tables(soup) if action == "get_stream" else []
    trailer = get_trailer(basic_data["film_id"])
    if not translators and basic_data["match_data"]:
        translators.append({"id": basic_data["match_data"].group(3), "name": "default"})
    info_data = parse_info_table(soup)
    # themovie_db = get_themoviedb_movie(
    #     basic_data["origin_name"], imdb_id=basic_data["imdb_id"]
    # )
    # if themovie_db.get("backdrop_path"):
    #     backdrop_path = themovie_db.get("backdrop_path")
    # else:
    #     backdrop_path = None
    result = {
        "id": basic_data["film_id"] or "",
        "title": basic_data["title"] or "",
        "origin_name": basic_data["origin_name"] or "",
        "image": basic_data["source_link"] or "",
        "duration": basic_data["duration"] or "",
        "description": basic_data["description"] or "",
        "rate": basic_data["rate"] or "",
        "translator_ids": translators,
        "trailer": trailer or "",
        "link": url,
        "action": action,
        "favs": basic_data["ctrl_favs_value"] or "",
        "season_ids": season_ids,
        "episodes_schedule": episodes_schedule,
        # "backdrop_path": themovie_db.get("backdrop_path"),
        # Добавляем инфо из parse_info_table
        "release_date": info_data.get("release_date"),
        "country": info_data.get("country"),
        "genre": info_data.get("genre"),  # список
        "director": info_data.get("director"),  # список
        "age": info_data.get("age"),
    }

    return result


def get_categories(url: str) -> dict:
    response = requests.get(url, headers=HEADERS, cookies=COOKIES)
    response.raise_for_status()  # выбросит исключение, если запрос не успешен
    html = response.text

    soup = BeautifulSoup(html, "html.parser")
    categories = []

    # Выбираем все li с классом b-topnav__item, являющиеся непосредственными дочерними элементами ul#topnav-menu
    li_items = soup.select("ul#topnav-menu > li.b-topnav__item")

    for li in li_items:
        # Проверяем наличие подменю
        sub_menu = li.find(class_="b-topnav__sub")
        if not sub_menu:
            continue

        # Извлекаем основной пункт меню (название и ссылку)
        main_link = li.find("a", class_="b-topnav__item-link")
        if not main_link:
            continue
        main_title = main_link.get_text(strip=True)
        main_url = main_link.get("href", "").strip()

        subcategories = []
        # Находим контейнер подменю, где содержатся все пункты (без разделения на левую и правую части)
        sub_inner = sub_menu.find(class_="b-topnav__sub_inner")
        if sub_inner:
            li_subs = sub_inner.find_all("li")
            for li_sub in li_subs:
                a_tag = li_sub.find("a")
                if a_tag:
                    sub_title = a_tag.get_text(strip=True)
                    sub_url = a_tag.get("href", "").strip()
                    if sub_title and sub_url:
                        subcategories.append({"title": sub_title, "url": sub_url})

        if not subcategories:
            continue

        categories.append(
            {"title": main_title, "url": main_url, "subcategories": subcategories}
        )

    return {"categories": categories}
