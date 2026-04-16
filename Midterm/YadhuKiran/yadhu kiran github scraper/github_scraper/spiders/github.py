import scrapy


class GithubSpider(scrapy.Spider):
    name = "github"

    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    }

    def start_requests(self):
        url = "https://github.com/YadhuKiran?tab=repositories"
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        repos = response.css('li[itemprop="owns"]')

        for repo in repos:
            repo_link = repo.css('a[itemprop="name codeRepository"]::attr(href)').get()

            if repo_link:
                full_url = response.urljoin(repo_link)
                yield response.follow(full_url, self.parse_repo)

    def parse_repo(self, response):
        item = {}

        # URL
        item['url'] = response.url

        # Repo name
        repo_name = response.css('strong a::text').get(default="").strip()

        # About
        about = response.css('p.f4::text').get()
        is_empty = "This repository is empty" in response.text

        if about and about.strip():
            item['about'] = about.strip()
        else:
            item['about'] = repo_name if not is_empty else ""

        # Last Updated (with fallback)
        last_updated = response.xpath('//relative-time/@datetime').get()
        if not last_updated:
            last_updated = response.xpath('//div[contains(@class,"f6")]//relative-time/@datetime').get()

        item['last_updated'] = last_updated if last_updated else ""

        # Languages and commits
        if not is_empty:
            # Extract and clean languages
            raw_langs = response.css('li.d-inline span::text').getall()
            cleaned_langs = []

            for lang in raw_langs:
                lang = lang.strip()
                if lang and "%" not in lang:
                    cleaned_langs.append(lang)

            item['languages'] = cleaned_langs

            # Extract commits (best possible with Scrapy)
            commits = response.xpath('//a[contains(@href,"/commits")]/span/strong/text()').get()

            if not commits:
                commits = response.xpath('//a[contains(@href,"/commits")]/text()').re_first(r'\d+')

            item['commits'] = commits if commits else ""

        else:
            item['languages'] = []
            item['commits'] = ""

        yield item