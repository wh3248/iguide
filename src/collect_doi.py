"""
    Scrap document DOIs from the parflow publications URL.
"""
import requests

def main():
    publications_url = "https://parflow.org/#publications"
    response = requests.get(publications_url)
    if response.status_code != 200:
        print(f"Error ({response.status_code}) while reading '{publications_url}")
        return
    content = str(response.content).replace("\\n", "\n")
    found_publications_start = False
    for line in content.split("\n"):
        if line.find("List of publications") >= 0:
            found_publications_start = True
        if found_publications_start and line.startswith("<li>"):
            scrap_entry(line)

def scrap_entry(line):
    # Strip <li> tag from line
    line = line[len("<li>"):]
    line = line[0:-len("</li>")]
    a_start = line.find("<a")
    a_body_end = line.find(">", a_start)
    a_end = line.find("</a>")
    a_body = line[a_start:a_body_end]
    a_body_quote_start = a_body.find("\"")
    doi_url = a_body[a_body_quote_start+1:-1]
    title = line[a_body_end+1:a_end]
    author_year = line[0: a_start].strip()
    year_start = author_year.find("(")
    year_end = author_year.find(")") if year_start > 0 else 0
    if year_start > 0 and year_end > 0:
        author = author_year[0:year_start]
        year = author_year[year_start+1:year_end]
    else:
        author = author_year
        year = ""

    collect_entry(author, year, title, doi_url)

def collect_entry(author, year, title, doi_url):
    print("DOI:", doi_url)
    print("Author:", author)
    print("Title:", title)
    print()
main()
