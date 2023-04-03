from urllib.request import urlopen
from bs4 import BeautifulSoup
from time import sleep
from sys import argv


RESULTS_MAX = 50
SEARCH_BASE = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?retmax={}&term={}'
PUBMED_BASE = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id='
PROXIMITY = 0
PUBMED_DELAY = 0.3
AUTHORS_MAX = 3
TABLE_MARGIN = 1

def main():
    keywords = {}
    with open(argv[1]) as trf_file:
        tr_factors = trf_file.readlines()
        tr_factors = [trf.strip() for trf in tr_factors]
    with open(argv[2]) as kw_file:
        for kw_type in ('narrow', 'broad'):
            keywords[kw_type] = kw_file.readline()
            keywords[kw_type] = [kw.strip() for kw in keywords[kw_type].split(",")]
    
    tablef = open(argv[1].split(".")[0] + "_summary_table.txt", "w")
    tf_max_len = max(len(tf) for tf in tr_factors)
    table_header = [" " * (tf_max_len + TABLE_MARGIN)]
    col_widths = [tf_max_len + TABLE_MARGIN]
    for kw_list in keywords.values():
        for kw in kw_list:
            table_header.append(" " * TABLE_MARGIN + str(kw) + " " * TABLE_MARGIN)
            col_widths.append(len(kw) + TABLE_MARGIN)
        table_header.append("")
    print("|".join(table_header), file=tablef)

    for tf in tr_factors:
        cws = col_widths.copy()
        table_row = [f"{tf:{cws.pop(0)}}"]
        print(f"Searching for {tf}")
        tf_ids = {}
        for kw in keywords['narrow']:
            count = collect_ids(tf, kw, tf_ids)
            table_row.append(f"{count:{cws.pop(0)}} ")
        table_row.append('')
        if len(tf_ids) == 0:
            for kw in keywords['broad']:
                count = collect_ids(tf, kw, tf_ids)
                table_row.append(f"{count:{cws.pop(0)}} ")
        else:
            for kw in keywords['broad']:
                count = collect_ids(tf, kw, {})
                table_row.append(f"{count:{cws.pop(0)}} ")
        
        print(f"{len(tf_ids)} items for {tf}")
        print("|".join(table_row), file=tablef)

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

    tablef.close()


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
    return results_count


if __name__ == '__main__':
    main()
