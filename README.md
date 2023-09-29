# pwset
0.3.1

Simple demo app to get detailed results from cernyrytir.cz webpage based on multiple entries separated by newline with ability to filter unavailable cards. Currently scans:
- cernyrytir.cz
- blacklotus.cz
- najada.games

Due to wild search engines used by each site exact name of cards is preferred (including lower and upper cases).

To run in docker:
- docker build -t mtg-search-app .
- docker run -p 5000:5000 mtg-search-app

To run locally using python:
- pip install -r requirements.txt
- playwright install

Access the resulting Flask access point
- http://localhost:5000
