from playwright.sync_api import sync_playwright
from flask import Flask, render_template, request

W = "https://cernyrytir.cz/index.php3?akce=3"

def cerny_rytir(url:str, search_query:str, exclude_zero:bool):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.type('input[name="jmenokarty"]', search_query)
        page.press('input[name="jmenokarty"]', 'Enter')
        page.wait_for_load_state('domcontentloaded')

        tbody_elements = page.locator('tbody').all()

        if len(tbody_elements) >= 7:
            tbody = tbody_elements[6]

            td_elements = tbody.locator('td').all()

            data = []
            current_lines = []

            for td in td_elements:
                line = td.inner_text().strip()
                line = line.replace('\xa0', ' ')
                if len(line) > 0:
                    current_lines.append(line)
                    if len(current_lines) == 6:
                        category_data = {
                            "Name": current_lines[0],
                            "Set": current_lines[1],
                            "Type": current_lines[2],
                            "Rarity": current_lines[3],
                            "Quantity": current_lines[4],
                            "Price": current_lines[5]}
                        if exclude_zero and "0" in category_data["Quantity"]:
                            current_lines = []
                        else:
                            data.append(category_data)
                            current_lines = []

        browser.close()
        return data

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def display_table():
    if request.method == 'POST':
        search_query = request.form['search_query']
        entries = search_query.strip().split('\n')
        exclude_zero = request.form.get('exclude_zero') == '1'

        results = []
        for entry in entries:
            entry = entry.strip()
            if entry:
                entry_results = cerny_rytir(W, entry, exclude_zero)
                results.extend(entry_results)

        return render_template('table.html', data=results)

    return render_template('form.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


