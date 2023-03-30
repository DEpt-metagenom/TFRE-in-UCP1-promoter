from urllib.request import urlopen
from bs4 import BeautifulSoup
from time import sleep


RESULTS_MAX = 50
SEARCH_BASE = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?retmax={}&term={}'
PUBMED_BASE = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id='
PROXIMITY = 0
PUBMED_DELAY = 0.3
AUTHORS_MAX = 3

keywords_narrow = ['thermogenesis', 'UCP1']
keywords_broad = ['adipocyte', 'browning', 'obesity', 'diabetes']
tr_factors = 'ASCL1, CTCFL, ESR2, ESRRB, Esrrg, EWSR1 FLI1, FIGLA, HNF4G,\
              ID4, IRF1, KLF16, KLF5, MZF1, NR2C2, NR4A2, Nr5a2, PBX3, PLAG1,\
              Pparg Rxra, RARA, Rarg, RBPJ, REST RE1, RREB1, Sox3, SP1, SP2,\
              SP4, SP8, SPIB, Stat5a, Stat5b, TBX15, TBX5, TCF3, TCF4,\
              ZBTB18, ZEB1, ZNF263, SP3, NEUROD1, TFAP2A, TFAP2B'
tr_factors = [trf.strip() for trf in tr_factors.split(',')]


def main():
    for tf in tr_factors:
        print(f"Searching for {tf}")
        tf_ids = {}
        for kw in keywords_narrow:
            collect_ids(tf, kw, tf_ids)
        if len(tf_ids) == 0:
            for kw in keywords_broad:
                collect_ids(tf, kw, tf_ids)
        print(f"{len(tf_ids)} items for {tf}")
        print()

        tf_file = open(f"{tf.replace(' ', '_')}.txt", 'w', encoding='utf-8')
        for i, id in enumerate(list(tf_ids.keys())[:RESULTS_MAX]):
            pubmed_sum = None
            while pubmed_sum is None:
                try:
                    pubmed_sum = urlopen(PUBMED_BASE + id)
                except TimeoutError:
                    sleep(5)
            pubmed_bs = BeautifulSoup(pubmed_sum, 'xml')

            authors = pubmed_bs.find_all("Author")
            if len(authors) > AUTHORS_MAX:
                authors_list = authors[0].LastName.text + " et al."
            else:
                authors_list = []
                for author in authors:
                    try:
                        authors_list.append(author.LastName.text)
                    except AttributeError:
                        authors_list.append(author.CollectiveName.text)
                authors_list = ' & '.join(authors_list)
            title = pubmed_bs.ArticleTitle.text
            try:
                journal = pubmed_bs.Journal.ISOAbbreviation.text
            except AttributeError:
                journal = ''
            try:
                year = pubmed_bs.PubDate.Year.text
            except AttributeError:
                year = pubmed_bs.PubDate.MedlineDate.text
            print(f"{i + 1}.", file=tf_file)
            print(f"{authors_list}: {title}\n{journal} {year}", file=tf_file)
            print("Abstract", file=tf_file)
            try:
                print("\n".join(f"{abs_sec['Label']}: {abs_sec.text}"
                                for abs_sec
                                in pubmed_bs.Abstract.find_all('AbstractText')),
                      file=tf_file)
            except KeyError:
                print(pubmed_bs.AbstractText.text, file=tf_file)
            except AttributeError:
                print("No Abstract", file=tf_file)
            print("Search keywords:", ", ".join(skw for skw in tf_ids[id]),
                  file=tf_file)
            try:
                print("Keywords:",
                      ", ".join(kw.text.strip()
                                for kw in pubmed_bs.KeywordList),
                      file=tf_file)
            except TypeError:
                pass
            print(f"URL: https://pubmed.ncbi.nlm.nih.gov/{id}", file=tf_file)
            try:
                print("Full text: https://www.ncbi.nlm.nih.gov/pmc/articles/"
                      + pubmed_bs.PubmedData.ArticleIdList
                        .find("ArticleId", {'IdType': "pmc"}).text,
                      file=tf_file)
            except AttributeError:
                pass
            print(file=tf_file)
            sleep(PUBMED_DELAY)

        tf_file.close()


def collect_ids(tf, kw, tf_ids):
    term = '+'.join(tf.split(' ') + [kw])
    if PROXIMITY:
        term = f'"{term}"[Title/Abstract:~{PROXIMITY}]'
    search_res = urlopen(SEARCH_BASE.format(RESULTS_MAX, term))
    search_bs = BeautifulSoup(search_res, 'xml')
    results_count = int(search_bs.Count.text)
    print(f"Hits for {kw}: {results_count}")
    if results_count > RESULTS_MAX:
        print(f"Number of search hits for {term} is {results_count},"
              + f" but only {RESULTS_MAX} can be retrieved from the database")
    sleep(PUBMED_DELAY)
    for pmid in search_bs.find_all('Id'):
        try:
            tf_ids[pmid.text].append(kw)
        except KeyError:
            tf_ids[pmid.text] = [kw]


if __name__ == '__main__':
    main()
