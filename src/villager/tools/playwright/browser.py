from enum import Enum

import loguru
from playwright.sync_api import sync_playwright, Playwright


class WaitUntilState(Enum):
    LOAD = 'load'
    DOM_CONTENT_LOADED = 'domcontentloaded'
    NETWORK_IDLE = 'networkidle'
    COMMIT = 'commit'


class FILE_TYPE(Enum):
    JPG: str = 'jpg'
    PNG: str = 'png'
    GIF: str = 'gif'
    PDF: str = 'pdf'
    DOC: str = 'doc'
    DOCX: str = 'docx'
    XLS: str = 'xls'
    XLSX: str = 'xlsx'
    PPT: str = 'ppt'
    PPTX: str = 'pptx'
    TXT: str = 'txt'
    ZIP: str = 'zip'
    RAR: str = 'rar'
    GZ: str = 'gz'
    TAR: str = 'tar'
    BZ2: str = 'bz2'
    Z: str = 'z'
    TARGZ: str = 'tar.gz'


class CrawlerBase:
    history_urls: list[str] = []
    thread_count: int = 1
    black_list_file_type: list[FILE_TYPE] = [FILE_TYPE.JPG, FILE_TYPE.PNG, FILE_TYPE.GIF, FILE_TYPE.PDF, FILE_TYPE.DOC,
                                             FILE_TYPE.DOCX, FILE_TYPE.XLS, FILE_TYPE.XLSX, FILE_TYPE.PPT,
                                             FILE_TYPE.PPTX, FILE_TYPE.TXT, FILE_TYPE.ZIP, FILE_TYPE.RAR, FILE_TYPE.GZ,
                                             FILE_TYPE.TAR, FILE_TYPE.BZ2, FILE_TYPE.Z, FILE_TYPE.TARGZ]


class Crawler(CrawlerBase):

    def __init__(self, url):
        self.url = url

        # Initialize the playwright browser
        self.playwright = sync_playwright().start()

    def get_page_content(self, **kwargs):
        """
        Get the page content
        :return: Raw HTML content
        """
        loguru.logger.debug("Getting page content...")
        browser = self.playwright.chromium.launch()
        page = browser.new_page()
        page.goto(self.url, **kwargs)
        content = page.content()
        browser.close()
        loguru.logger.debug("Page content obtained.")
        return content

    def get_page_text(self, **kwargs):
        """
        Get the full text content of the rendered page
        :return: Full text content
        """
        waiting_mode = WaitUntilState.NETWORK_IDLE
        loguru.logger.debug("Getting page text...")
        browser = self.playwright.chromium.launch()
        page = browser.new_page()
        page.goto(self.url, wait_until="networkidle")
        text_content = page.inner_text('body')
        browser.close()
        loguru.logger.debug("Page text obtained.")
        return text_content

    def crawler_for_domain(self, domain_list: list[str]):
        """
        Crawler,enter from url,and crawl the domain_list
        :param domain_list: List of domains, e.g. ['example.com', 'example2.com']
        :return:
        """
        ...


if __name__ == '__main__':
    crawler = Crawler("http://100.64.0.33")
    content = crawler.get_page_content(wait_until="networkidle")
    loguru.logger.info(content)
