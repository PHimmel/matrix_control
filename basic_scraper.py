from bs4 import BeautifulSoup as Soup
import urllib
from urllib import request


class Http:
    def __init__(self, link):
        self.link = link
        self.raw_html = self.get_raw_html()
        self.html = self.read_raw_html()

    def get_raw_html(self):
        return urllib.request.urlopen(self.link)

    def read_raw_html(self):
        return self.raw_html.read()


class Parser(Http):
    def __init__(self, link, class_filter):
        super().__init__(link)
        self.class_filter = class_filter
        self.soup = self.make_soup()
        self.text = self.extract_text()

    def make_soup(self):
        return Soup(self.html, 'html.parser')

    def extract_text(self):
        return [title.text for title in self.soup('a', class_=self.class_filter) if len(title.text) > 15]


class Output:
    def __init__(self, link, class_filter):
        # fill in parameter
        self.text = Parser(link, class_filter).extract_text()

    def write_text_to_temp_file(self):
        with open('/home/pi/Programs/Output/Documents/txt/news_headlines.txt', 'w') as file:
            file.write(' »»» '.join(self.text))
            file.close()

    def return_text(self):
        return ' >>> '.join(self.text)


# returns full page headlines
def get_headlines(news_source=None):
    bbc = 'https://www.bbc.com/news'
    bbc_class = 'gs-c-promo-heading gs-o-faux-block-link__overlay-link gel-pica-bold nw-o-link-split__anchor'

    yahoo = 'https://www.news.yahoo.com'
    yahoo_class = 'Fw(b)'

    if news_source == 'yahoo':
        return Parser(yahoo, yahoo_class).extract_text()

    elif news_source == 'bbc':
        return Parser(bbc, bbc_class).extract_text()

    else:
        return Parser(bbc, bbc_class).extract_text()


def main():
    print('main module, main function is empty')
    print(get_headlines())
    print('main module concluded')


if __name__ == '__main__':
    main()
