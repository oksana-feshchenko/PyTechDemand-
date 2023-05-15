import asyncio
import aiohttp
import csv
from dataclasses import dataclass, fields, astuple


from bs4 import BeautifulSoup

URL = "https://djinni.co/jobs/?primary_keyword=Python"

CSV_PATH = "description.csv"


@dataclass
class Job:
    title: str
    description: str


JOB_FIELDS = [field.name for field in fields(Job)]


async def get_num_pages(page_soup: BeautifulSoup) -> int:
    pagination = page_soup.select_one(".pagination")
    if pagination is None:
        return 1
    return int(pagination.select("li a")[-2].text)


async def parse_one_job(job_soup):
    return Job(
        title=job_soup.select_one('div.list-jobs__title a span').text,
        description=job_soup.select_one(".text-card").text.strip().replace("●", ""),
    )


async def get_one_page_jobs(page_soup):
    jobs = page_soup.select(".list-jobs__item, .list__item")
    return await asyncio.gather(*[parse_one_job(job) for job in jobs])


def write_products_to_scv(jobs: [Job]) -> None:
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(JOB_FIELDS)
        writer.writerows([astuple(job) for job in jobs])


async def get_job_descriptions(years_of_experience: int = None) -> None:
    async with aiohttp.ClientSession() as session:
        if years_of_experience:
            params = {"exp_level": str(years_of_experience) + "y"}
            page = await session.get(URL, params=params)
        page = await session.get(URL)
        content = await page.text()
        first_page_soup = BeautifulSoup(content, "html.parser")
        num_pages = await get_num_pages(first_page_soup)
        all_jobs = await get_one_page_jobs(first_page_soup)

        tasks = []
        for i in range(2, num_pages + 1):
            params = {"page": i}
            page = await session.get(URL, params=params)
            content = await page.text()
            page_soup = BeautifulSoup(content, "html.parser")
            tasks.append(get_one_page_jobs(page_soup))

        results = await asyncio.gather(*tasks)
        for jobs in results:
            all_jobs.extend(jobs)

        write_products_to_scv(all_jobs)


if __name__ == '__main__':
    asyncio.run(get_job_descriptions())


