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
        if doi_url.strip() == "https://doi.org/10.1007/s10596-021-10051-4":
            year = "2021"
        elif doi_url.strip() == "https://www.sciencedirect.com/science/article/abs/pii/S0309170813001322":
            year = "2013"
    author = author.replace(" and ", "")
    author = author.replace(",,", "")
    if entry_index < 500:
        contents = read_url_content(doi_url)
        contents = read_url_redirect(contents)
        write_csv_row(author, year, title, doi_url, contents, entry_index, fout)


def write_csv_row(author, year, title, doi_url, contents, entry_index, fout):
    """
    Write a csv row for the publication information.
    Parameters:
        author:     The author(s) of the publication.
        year:       The year of the publication.
        title:      The title of the publication.
        doi_url:    The URL of the document.
        contents:   The contents of the URL of the document.
        entry_index:The index of the publication from the original source
        fout:       The file pointer to use to write the .csv file
    """

    if contents:
        image_url = find_doi_image(contents)
        fout.write(f'{doi_url},{image_url},"{title}","{author}",{year}\n')
    else:
        print(f"*** Skipped DOI({entry_index}):", doi_url)


def find_doi_image(contents:str):
    """
    Find an image by reading the contents of the paper.
    Parameters:
        doi_url:        The URL to the contents of the publication.
    Returns:
        A URL of an image from the document or else a default image URL.
    """
    found_abstract = False
    image_url = ""
    for line in contents.split("\n"):
        if "Abstract" in line:
            found_abstract = True
        if line.find("<img") >= 0 and not "logo" in line and not "license" in line:
            image_url = find_tag_attribute(line, "src")
            if found_abstract and image_url:
                break
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

def read_url_content(url:str):
    """
        Read the contents of a URL
        Returns:
            the contents as a string or None if unable to get the contents
    """
    result = None
    try:
        response = requests.get(url)
        if response.status_code not in (200, 403):
            print(
                f"**** Document returns an error ({response.status_code}) for '{url}'."
            )
        else:
            result = response.content.decode("utf-8")
    except Exception:
        print(f"**** Document does not exist for '{url}'")
    return result

def read_url_redirect(contents:str):
    """Return the contents unless the contents is a redirect and then read and return the redirect contents."""

    if contents:
        redirect_tag = '<input type="hidden" name="redirectURL'
        redirect_start = contents.find(redirect_tag)
        if redirect_start >= 0:
            redirect_contents = contents[redirect_start + len(redirect_tag):]
            encoded_url = find_tag_attribute(redirect_contents, "value")
            redirect_url = urllib.parse.unquote(encoded_url)
            if redirect_url:
                contents = read_url_content(redirect_url)
    return contents



if __name__ == "__main__":
    main()
