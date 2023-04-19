# stash-iwc-pyscraper
Python-based IWantClips scraper for Stash

## Dependencies
This is a Python scraper, and as such, Python (Python3) needs to be installed.
- The official Stash docker container already contains python and all needed modules.
- For Windows systems, install python from [python.org](https://www.python.org/downloads/windows/) ([instructions](https://phoenixnap.com/kb/how-to-install-python-3-windows)), NOT from the Windows store.
- For Linux systems please consult the relevant distro instructions.
- For Μac systems either use homebrew eg `brew install python3` or use the python.org installer ([instructions](https://www.lifewire.com/how-to-install-python-on-mac-4781318))

## pip requirements
- bs4
- lxml
- requests

## Features
- Working search functionality utilising IWC's Algolia search API.
- Dynamic selection of best-available thumbnail image, favouring still images over animated GIFs (still needs some tweaking).
- No dependency on a Chrome CDP.

## Pitfalls
- Highly untested - It seems to work fine on my Stash instance and I haven't encountered any issues yet, but this should very much be considered untested.

## Special thanks
I'd like to thank the writers of the following scrapers on the CommunityScrapers git repository - their code has proven very useful in helping this come together:
- bnkai, who wrote the ManyVids Python scraper: https://github.com/stashapp/CommunityScrapers/commits/master/scrapers/ManyVids
- estellaarrieta, who wrote the WowNetworkVenus Python scraper, from which I managed to work out a lot about the structure of Python scrapers, etc.

Also, mention has to go to ChatGPT, without which I wouldn't have been able to fumble blindly through this project.
