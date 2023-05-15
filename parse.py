import csv
import logging
import sys
from dataclasses import dataclass, fields, astuple


import requests
from bs4 import BeautifulSoup

URL = "https://djinni.co/jobs/?primary_keyword=Python"
CSV_PATH = "description.csv"


@dataclass
class Job:
    title: str
    description: str


JOB_FIELDS = [field.name for field in fields(Job)]

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s] : %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


def get_num_pages(page_soup: BeautifulSoup) -> int:
    pagination = page_soup.select_one(".pagination")
    if pagination is None:
        return 1
    return pagination.select("li a")[-2].text


def parse_one_job(job_soup):
    return Job(
        title=job_soup.select_one('div.list-jobs__title a span').text,
        description=job_soup.select_one(".text-card").text.strip().replace("●", ""),
    )


def get_one_page_jobs(page_soup):
    jobs = page_soup.select(".list-jobs__item, .list__item")
    return [parse_one_job(job) for job in jobs]


def get_job_descriptions():
    page = requests.get(URL).content
    first_page_soup = BeautifulSoup(page, "html.parser")
    num_pages = int(get_num_pages(first_page_soup))
    all_jobs = get_one_page_jobs(first_page_soup)
    for i in range(2, num_pages + 1):
        page = requests.get(URL, {"page": i}).content
        page_soup = BeautifulSoup(page, "html.parser")
        all_jobs.extend(get_one_page_jobs(page_soup))
    return all_jobs


def write_products_to_scv(jobs: [Job]) -> None:
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(JOB_FIELDS)
        writer.writerows([astuple(job) for job in jobs])


if __name__ == '__main__':
    jobs = get_job_descriptions()
    write_products_to_scv(jobs)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
