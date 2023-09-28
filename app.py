from playwright.sync_api import sync_playwright
from flask import Flask, render_template, request

W = "https://cernyrytir.cz/index.php3?akce=3"
BL = "https://www.blacklotus.cz/magic-kusove-karty/"


def extract_numbers_from_string(input_list:list) -> None:
    i = 1
    current_number = ""
    while i < len(input_list):
        for char in input_list[i]:
            if char.isdigit():
                current_number += char
        if len(current_number) > 0:
            input_list[i] = current_number + " ks"
        else:
            input_list[i] = "0 ks"
        current_number = ""
        i += 4

def insert_blank_if_not_present(input_list:list, check_string:str) -> None:
    i = 3
    while i < len(input_list):
        if check_string not in input_list[i]:
            input_list.insert(i, "")
        else:
            index = input_list[i].index(check_string)
            input_list[i] = (input_list[i][index + len(check_string):]).strip()
            input_list[i] = input_list[i].replace(".", "")

        i += 4

def black_lotus(url:str, search_query:str, exclude_zero:bool) -> list:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.type('input[name="string"]', search_query)
        page.press('input[name="string"]', 'Enter')
        page.wait_for_load_state('domcontentloaded')

        target_class = 'search-results'
        text_values = page.evaluate(f'''() => {{const divs = Array.from(document.querySelectorAll('.{target_class}'));return divs.map(div => div.innerText);}}''')
        
        browser.close()
        
        filtered_data = [item for item in text_values[0].split('\n') if 'DETAIL' not in item]
        filtered_data = [item for item in filtered_data if item]
        insert_blank_if_not_present(filtered_data, "z edice")
        extract_numbers_from_string(filtered_data)

        splitlist = [filtered_data[i:i + 4] for i in range(0, len(filtered_data), 4)]
        data = []
        
        for item in splitlist:
            if exclude_zero and "0" in item[1]:
                pass
            else:
                category_data = {
                    "Shop": "Black lotus",
                    "Name": item[0],
                    "Set": item[3],
                    "Type": "",
                    "Rarity": "",
                    "Quantity": item[1],
                    "Price": item[2]}
                data.append(category_data)

        return data


def cerny_rytir(url:str, search_query:str, exclude_zero:bool) -> list:
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
                            "Shop": "Černý rytíř",
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
                cernyrytir = cerny_rytir(W, entry, exclude_zero)
                blacklotus = black_lotus(BL, entry, exclude_zero)

                results.extend(cernyrytir)
                results.extend(blacklotus)


        return render_template('table.html', data=results)

    return render_template('form.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


