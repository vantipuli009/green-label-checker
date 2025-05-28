
import requests

def get_cid_from_name(name):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/cids/JSON"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    return res.json()['IdentifierList']['CID'][0]

def extract_ghs_statements(cid):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON"
    res = requests.get(url)
    if res.status_code != 200:
        return []

    data = res.json()
    #print(data)
    

    try:
        sections = data['Record']['Section']
        #print(sections)
        for section in sections:
            #print(section["TOCHeading"])
            if section["TOCHeading"] == "Safety and Hazards":
                #print("True")
                for sub_sections in section.get("Section", []):
                    if sub_sections.get("TOCHeading") == "Hazards Identification":
                        for sub_section in sub_sections.get("Section", []):
                            if sub_section.get('TOCHeading') == "GHS Classification":
                                for info in sub_section.get("Information", []):
                                    if info.get("Name") == "GHS Hazard Statements":
                                        # Extract all hazard statement strings
                                        return [item["String"] for item in info["Value"]["StringWithMarkup"]]
    except Exception as e:
        print(f"❌ Error extracting GHS hazard statements: {e}")
        return []

    return []

from bs4 import BeautifulSoup

def scrape_ewg(ingredient):
    # Convert to search-friendly URL
    search_term = ingredient.lower().replace(" ", "+")
    search_url = f"https://www.ewg.org/skindeep/search/?search={search_term}"

    headers = {"User-Agent": "Mozilla/5.0"}
    search_res = requests.get(search_url, headers=headers)

    if search_res.status_code != 200:
        return {"source": "EWG", "safety_level": "unknown", "note": "EWG search failed"}

    soup = BeautifulSoup(search_res.text, "html.parser")
    link_tag = soup.find("a", class_="product-search-result-link")

    if not link_tag:
        return {"source": "EWG", "safety_level": "unknown", "note": "Not found on EWG"}

    ingredient_url = "https://www.ewg.org" + link_tag["href"]
    detail_res = requests.get(ingredient_url, headers=headers)
    if detail_res.status_code != 200:
        return {"source": "EWG", "safety_level": "unknown", "note": "Failed to load ingredient detail"}

    detail_soup = BeautifulSoup(detail_res.text, "html.parser")

    # Extract EWG Score
    score_tag = detail_soup.find("div", class_="score-range-number")
    score = int(score_tag.text.strip()) if score_tag else None

    # Extract concern summary
    summary_tag = detail_soup.find("div", class_="score-concerns-text")
    concern_summary = summary_tag.text.strip() if summary_tag else "No concern summary"

    # Heuristic label
    if score is not None:
        if score <= 3:
            safety = "safe"
        elif score <= 6:
            safety = "moderate"
        else:
            safety = "harmful"
    else:
        safety = "unknown"

    return {
        "source": "EWG",
        "safety_level": safety,
        "note": f"EWG score {score}. {concern_summary}"
    }

