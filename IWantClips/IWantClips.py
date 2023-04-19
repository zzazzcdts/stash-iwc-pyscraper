import os
import sys
import json
import datetime

# to import from a parent directory we need to add that directory to the system path
csd = os.path.dirname(
    os.path.realpath(__file__))  # get current script directory
parent = os.path.dirname(csd)  # parent directory (should be the scrapers one)
sys.path.append(
    parent
)  # add parent dir to sys path so that we can import py_common from there

try:
    # Import Stash logging system from py_common
    from py_common import log
except ModuleNotFoundError:
    print(
        "You need to download the folder 'py_common' from the community repo. (CommunityScrapers/tree/master/scrapers/py_common)",
        file=sys.stderr)
    sys.exit()

try:
    # Import necessary modules.
    from lxml import html
    import requests
    from requests import utils
    from requests import cookies
    import re
    from urllib.parse import urlparse
    from bs4 import BeautifulSoup

    # Set headers with user agent to avoid Cloudflare throwing a hissy fit.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Accept-Language": "en-US,en;q=0.8",
        "Content-Type": "application/json"
    }
    # Establish session and implement headers.
    session = requests.Session()
    session.headers.update(headers)

# If one of these modules is not installed:
except ModuleNotFoundError:
    log.error(
        "You need to install the python modules mentioned in requirements.txt"
    )
    log.error(
        "If you have pip (normally installed with python), run this command in a terminal from the directory the scraper is located: pip install -r requirements.txt"
    )
    sys.exit()

# The purpose of this function is to retrieve the API key for the Algolia search system. This is necessary to form a search request.
def GetAlgoliaApiKeys():
    # Load the front page.
    iwc = session.get("https://iwantclips.com")
    iwc_page = iwc.content.decode('utf-8')
    # Look for the Javascript function that defines the API keys.
    match = re.search(r"(?<=searchClient: )algoliasearch\((.*?)\)", iwc_page)
    # If we find it:
    if match:
        # Grab the result.
        arg_string = match.group(1)
        # Strip out quotation marks and other such junk.
        args = [arg.strip("\"'") for arg in arg_string.split(",")]
        args[1] = args[1].replace("'", "").replace('"', '').strip()
        # Return an array of the client ID and key.
        return args
    else:
        # Return None if no match is found
        return None


# This function retrieves the search results using the Algolia system used by the site.
def scrape_search(query):
    # Call the function to retrieve the Algolia API keys.
    apikeys = GetAlgoliaApiKeys()

    # Set the Algolia agent, app ID and API key.
    algolia_agent = "Algolia for JavaScript (3.33.0); Browser (lite); instantsearch.js (3.4.0); JS Helper 2.26.1"
    algolia_app_id = apikeys[0]
    algolia_api_key = apikeys[1]
    # Create the query URL using this information
    url = f"https://{apikeys[0]}-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent={algolia_agent}&x-algolia-application-id={algolia_app_id}&x-algolia-api-key={algolia_api_key}"
    # Create a POST request with our search query
    payload = {
        "requests": [
            {
                "indexName": "prod_content",
                "params": f"query={query}&maxValuesPerFacet=20&page=0&highlightPreTag=__ais-highlight__&highlightPostTag=__%2Fais-highlight__&clickAnalytics=true&facets=%5B%22categories%22%2C%22price%22%2C%22keywords%22%5D&tagFilters="
            }
        ]
    }

    # Send the POST request.
    response = session.post(url, json=payload)
    # These are the fields we're interested in to return meaningful search results.
    fields_to_keep = ['title', 'description', 'publish_date', 'model_username', 'thumbnail_url',
                      'content_url']
    # Load the JSON content from our POST request into a variable.
    json_data = json.loads(response.content)
    # Filter to just the 'hits' segment.
    hits = json_data.get('results', [])[0].get('hits', {})
    filtered_hits = []
    # Only keep the fields we defined earlier.
    for hit in hits:
        filtered_hit = {k: v for k, v in hit.items() if k in fields_to_keep}
        filtered_hits.append(filtered_hit)
    # Call the function to refactor the JSON into a Stash-friendly format and print.
    output_json_search(filtered_hits)

# This function refactors the JSON retrieved by the RetrieveSearchResults function and converts it into a Stash-friendly format.
def output_json_search(search_json):
    refactored_json = []
    # Build the JSON according to Stash requirements. Loop over all search results, appending each to the end.
    for data in search_json:
        refactored_data = {
            "title": data["title"],
            "details": data["description"],
            "url": data["content_url"],
            "date": datetime.datetime.fromtimestamp(data["publish_date"]).strftime("%Y-%m-%d"),
            "image": data["thumbnail_url"],
            "studio": {"name": data["model_username"]},
        }
        refactored_json.append(refactored_data)
    # Print the refactored data.
    print(json.dumps(refactored_json, indent=4))


def output_json_url(title, tags, url, image, studio, performers, description, date):
    # Split the tags into a list (comma-separated), stripping away any trailing full stops or tags which are just "N/A"
    tag_list = [tag.strip().rstrip('.') for tag in tags.split(",") if tag.strip() != "N/A"]
    # Create a tag dictionary from the tag list.
    tag_dicts = [{"name": tag} for tag in tag_list]
    # We're only using the value of 'performers' for our performer list. Kept for future-proofing, and also because I couldn't get it to work any other way.
    performer_list = [performers]
    performer_dicts = [{"name": performer} for performer in performer_list]
    # Dump all of this as JSON data.
    return json.dumps({
        "title": title,
        "tags": tag_dicts,
        "url": url,
        "image": image,
        "studio": {"name": studio},
        "performers": performer_dicts,
        "details": description,
        "date": date
    }, indent=4)


def scrape_scene(scene_url: str) -> dict:
    # Retrieve the page for the clip in question. Parse the HTML using BeautifulSoup.
    data = session.get(scene_url)
    soup = BeautifulSoup(data.content, 'lxml')

    # Retrieve title
    div_tag = soup.find('div', class_='col-md-12 col-sm-12 col-xs-12 title')
    span_tag = div_tag.find('span')
    title = span_tag.text

    # Retrieve description
    div_tag = soup.find('div', class_='col-xs-12 description fix')
    span_tag = div_tag.find('span')
    for br_tag in span_tag.find_all('br'):
        br_tag.replace_with('\n')
    description = span_tag.text.replace("  ", " ")
    description = re.sub(r'\n{3,}', '\n\n', description)

    description = "\n".join(line.strip() for line in description.split("\n"))

    # Retrieve date
    date_div = soup.find('div', class_='col-xs-12 date fix')
    date_span = date_div.find('span')
    date_str = date_span.text.replace("Published ", "").strip()
    date_obj = datetime.datetime.strptime(date_str, '%b %d, %Y')
    date = datetime.datetime.strftime(date_obj, '%Y-%m-%d')

    # Retrieve studio
    model_div = soup.find('div', class_='modelName')
    studio = model_div.find('a').text

    # Retrieve thumbnail
    video_tag = soup.find('video', class_='video-js embed-responsive-item')
    image_original = video_tag.get('poster')
    # The thumbnail being displayed on the page is usually an animated GIF, but 99% of the time there is a still image available. This script favours using the still image wherever possible, as it is usually of significantly higher quality.
    image_jpg = image_original.replace(".gif", ".jpg")
    # Test to see if the still image is available.
    response = requests.get(image_jpg)
    # If it isn't:
    if response.status_code == 404:
        # Fall back to using the original.
        image = image_original
    else:
        # Use the still image.
        image = image_jpg

    # Retrieve tags. Here we are combining the category and hashtag sections into one set of tags.
    category_div = soup.find('div', class_='col-xs-12 category fix')
    hashtags_div = soup.find('div', class_='col-xs-12 hashtags fix')
    category_span = category_div.find('span').text.strip()
    hashtags_span = hashtags_div.find('span').text.strip()

    tags = f"{category_span}, {hashtags_span}"
    tags = tags.replace('\n', ' ')
    tags = tags.rstrip(",")

    # Convert into meaningful JSON that Stash can use.
    json_dump = output_json_url(title, tags, scene_url, image, studio,
                                studio, description, date)

    print(json_dump)


def main():
    fragment = json.loads(sys.stdin.read())
    url = fragment.get("url")
    title = fragment.get("title")
    name = fragment.get("name")
    # If nothing is passed to the script:
    if url is None and title is None and name is None:
        log.error("No URL/Title/Name provided")
        sys.exit(1)
    # If we've been given a URL:
    if url is not None:
        scrape_scene(url)
    # If we've been given a name (i.e. this is a search operation).
    if name is not None:
        scrape_search(name)

if __name__ == "__main__":
    main()

# Last updated 2023-04-19
