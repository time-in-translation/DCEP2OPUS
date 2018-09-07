# DCEP2OPUS

DCEP2OPUS converts documents from the [DCEP parallel corpus](https://ec.europa.eu/jrc/en/language-technologies/dcep) to the [OPUS](http://opus.nlpl.eu/) format, to allow easier processing in other applications dealing with parallel corpora.

## Installation

DCEP2OPUS requires the following to be installed/downloaded:

* The [DCEP corpus](https://ec.europa.eu/jrc/en/language-technologies/dcep#Download%20the%20DCEP%20corpus).
* [Uplug](https://bitbucket.org/tiedemann/uplug/wiki/Home). Uplug comes with [hunalign](https://github.com/danielvarga/hunalign) installed.
* [TreeTagger](http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/). DCEP2OPUS expects TreeTagger to be installed in `/opt/treetagger/`.

## Details 

The OPUS format is XML-based, while DCEP is text-based.
Since there is already quite some tooling available for parallel corpora in OPUS, we created a Python script which converts the DCEP corpus into the OPUS format.
We apply a little bit of preprocessing to cut out the non-plain-text parts of the DCEP corpus. 
We then use Uplug to tokenize the text, and TreeTagger for part-of-speech tagging.
We also redo the original sentence alignment using hunalign.
The resulting corpus can then be queried using, for example, the [PerfectExtractor](https://github.com/UUDigitalHumanitieslab/perfectextractor/) package.
