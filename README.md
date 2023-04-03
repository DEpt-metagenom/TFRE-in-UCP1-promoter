# UCP1-promoter
Identification of TFs in the promoter of the human, mouse and rat UCP1, UCP2 and UCP3 genes by in silico studies that possess a DNA-binding element and therefore potentially play a role in the direct regulation of the gene expression.

## How to execute the literature mining script
`python3 literature_miner.py factors.txt keywords.txt`
The file `factors.txt` is a raw text file that contains the search expression (typically the abbreviation) for each transciption factor to be searched for on a separate line. When searching for complexes of transcription factors, the factors must be separated by a space rather than other symbols like `/` or `:`, for example `EWSR1 FLI1`. When searching for an abbreviation that is identical or similar to a normal English word, e.g. `REST` or `MAX`, further terms which help to disambiguate the abbreviation should be added to the search expression, e.g. `REST RE1` or `MAX myc x`, otherwise a lot of irrelevant hits are returned.

The file `keywords.txt` contains two rows. Both rows are comma-separated lists of keywords to be searched for. For every transcription factor, the script searches for each keyword on the first row of this file, which should contain the keywords immediately relevant to the research topic. If the total number of search results for the given factor and these keywords is zero, then the script continues with the keywords on the second line, which should be terms less closely related but still potentially relevant to the research question. The abstracts for the first `RESULTS_MAX`, e.g. the first 50 total hits for all such search expressions are downloaded from PubMed and saved in the output text file. The value of this variable can be changed by editing the corresponding row of `literature_miner.py`.

The script searches for all combinations of factor search term and keywords, i.e. factor1+keyword1, factor1+keyword2, ... factor2+keyword1, factor2+keyword2 ..., and saves the search results in a separate text file for each factor, i.e. for each line of the `factors.txt` file.
