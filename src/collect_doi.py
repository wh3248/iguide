"""
    Scrap document DOIs from the parflow publications URL.
"""

# pylint:   disable=C0301,W3101,W1514,R0913,R0917,W0718
import urllib
import requests


def main():
    """Main function to generate a .csv file with publication information."""

    publications_url = "https://parflow.org/#publications"
    response = requests.get(publications_url)
    if response.status_code != 200:
        print(f"Error ({response.status_code}) while reading '{publications_url}'")
        return
    content = response.content.decode("utf-8").replace("\\n", "\n")
    found_publications_start = False
    entry_index = 0
    output_csv_filename = "paper_doi_entries.csv"
    with open(output_csv_filename, "w+") as fout:
        fout.write("paper_doi_url,image_url,title,author,year\n")
        for line in content.split("\n"):
            if line.find("List of publications") >= 0:
                found_publications_start = True
            if found_publications_start and line.startswith("<li>"):
                entry_index = entry_index + 1
                scrap_entry(line, entry_index, fout)


def scrap_entry(line: str, entry_index: int, fout):
    """
    Scrap information from a line with publication information.
    Parameters:
        line:           A line with the publication information.
        entry_index:    The number of the line index for debugging
        fout:           A file pointer used to write to .csv file
    """
    # Strip <li> tag from line
    line = line[len("<li>") :]
    line = line[0 : -len("</li>")]

    # Find anchor tag information
    a_start = line.find("<a")
    a_body_end = line.find(">", a_start)
    a_end = line.find("</a>")
    a_body = line[a_start:a_body_end]
    a_body_quote_start = a_body.find('"')

    # Get DOI, title, author and year from line
    doi_url = a_body[a_body_quote_start + 1 : -1]
    title = line[a_body_end + 1 : a_end]
    author_year = line[0:a_start].strip()
    year_start = author_year.find("(")
    year_end = author_year.find(")") if year_start > 0 else 0
    if year_start > 0 and year_end > 0:
        author = author_year[0:year_start]
        year = author_year[year_start + 1 : year_end]
    else:
        author = author_year
        year = ""
    if entry_index < 500:
        write_csv_row(author, year, title, doi_url, entry_index, fout)


def write_csv_row(author, year, title, doi_url, entry_index, fout):
    """
    Write a csv row for the publication information.
    Parameters:
        author:     The author(s) of the publication.
        year:       The year of the publication.
        title:      The title of the publication.
        entry_index:The index of the publication from the original source
        fout:       The file pointer to use to write the .csv file
    """

    image_url = find_doi_image(doi_url)
    if image_url:
        fout.write(f'{doi_url},{image_url},"{title}","{author},{year}"\n')
    else:
        print(f"*** Skipped DOI({entry_index}):", doi_url)


def find_doi_image(doi_url, following_redirect=False):
    """
    Find an image by reading the contents of the paper.
    Parameters:
        doi_url:        The URL to the contents of the publication.
        following_redirect: True if this is a indirect request after following redirects.
    Returns:
        A URL of an image from the document or else a default image URL.
    """
    try:
        response = requests.get(doi_url)
    except Exception:
        if following_redirect:
            image_url = "https://parflow.org/img/pf3d.png"
            return image_url
        print(f"**** Document does not exist for '{doi_url}' so skipping it.")
        return None
    if response.status_code not in (200, 403):
        if following_redirect:
            image_url = "https://parflow.org/img/pf3d.png"
            return image_url
        print(
            f"**** Document returns an error ({response.status_code}) for '{doi_url}' so skipping it."
        )
        return None
    found_abstract = False
    content = response.content.decode("utf-8").replace("\\n", "\n")
    image_url = ""
    for line in content.split("\n"):
        if "Abstract" in line:
            found_abstract = True
        if line.find("<img") >= 0 and not "logo" in line and not "license" in line:
            image_url = find_tag_attribute(line, "src")
            if found_abstract and image_url:
                break
        if (
            not following_redirect
            and line.find('<input type="hidden" name="redirectURL') >= 0
        ):
            encoded_url = find_tag_attribute(line, "value")
            redirect_url = urllib.parse.unquote(encoded_url)
            image_url = find_doi_image(redirect_url, True)
    if not image_url:
        image_url = "https://parflow.org/img/pf3d.png"
    elif not image_url.startswith("http"):
        image_url = "https:" + image_url
    return image_url


def find_tag_attribute(line, attribute):
    """
    Find the attribute value from a html tag in the line.
    Parameters:
        line:       A line containing a HTML entry
        attribute:  The name of an attribute of the HTML entry.
    Returns:
        The value of the specified attribute of the first HTML entry in the line.
    """
    result = ""
    src_start = line.find(f'{attribute}="')
    if src_start > 0:
        line = line[src_start + len(attribute) + 2 :]
        src_end = line.find('"')
        if src_end >= 0:
            result = line[0:src_end]
    return result


if __name__ == "__main__":
    main()
