from playwright.sync_api import sync_playwright
from flask import Flask, render_template, request

CR = "https://cernyrytir.cz/index.php3?akce=3"
BL = "https://www.blacklotus.cz/magic-kusove-karty/"
NG = "https://www.najada.games/mtg/singles/bulk-purchase"


def split_list_by_string(input_list:list, split_string:str, occurrences:int=1):
    result = []
    count = 0
    current_sublist = []

    for item in input_list:
        if item.lower() == split_string.lower():
            count += 1
            if count > occurrences:
                result.append(current_sublist)
                current_sublist = []
        current_sublist.append(item)

    if current_sublist:
        result.append(current_sublist)
    return result

def make_proper_list_from_incomplete_info(lst):
    new_list = []
    for sublist in lst:
        if len(sublist) > 7:
            new_sublist = sublist[:4] + sublist[-3:]
            new_sublist[0] = new_sublist[0] + " - FOIL"
            sublist = sublist[:-3]
            new_list.append(sublist)
            new_list.append(new_sublist)
        else:
            new_list.append(sublist)
    return new_list

def najada_games(url:str, search_query:str, exclude_zero:bool) -> list:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state('load')
        page.fill('textarea#cardData', search_query)
        page.click('div.my-5.Button.font-encodeCond.f-15.p-7-44.green')

        selector = "div.BulkPurchaseItemList"
        page.wait_for_selector(selector)

        target_class = 'BulkPurchaseItemTemplate__body'
        text_values = page.evaluate(f'''() => {{const divs = Array.from(document.querySelectorAll('.{target_class}'));return divs.map(div => div.innerText);}}''')

        new_list = text_values[0].split('\n')

        browser.close()

        rem_list = ["-", "+", "Shopping list", "To add an item to the shopping list, please log in.", "Add to shopping list", "Wantlist", "If you want to be notified when a card is added to stock, please register."]
        new_list = [s for s in new_list if all(sub not in s for sub in rem_list)]
        new_list = [item for item in new_list if item]
        new_list = [item for item in new_list if not item.isdigit()]

        split_list = split_list_by_string(new_list, search_query)
        split_list = make_proper_list_from_incomplete_info(split_list)
        
        for each in split_list:
            pos = 5
            current_number = ""
            if len(each) > 0:
                for char in each[pos]:
                    if char.isdigit():
                        current_number += char
                if len(current_number) > 0:
                    each[pos] = current_number + " ks"
                else:
                    each[pos] = "0 ks"
            current_number = ""
        
        for sublist in split_list:
            if len(sublist) >= 6 and "CZK" in sublist[6]:
                sublist[6] = sublist[6].replace(" CZK", " Kč")


        data = []
        
        for item in split_list:
            if exclude_zero and "0" in item[5]:
                pass
            else:
                category_data = {
                    "Shop": "Najada",
                    "Name": item[0],
                    "Set": item[1],
                    "Type": "",
                    "Rarity": item[2],
                    "Quantity": item[5],
                    "Price": item[6]}
                data.append(category_data)

        return data

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
        split_list = [filtered_data[i:i + 4] for i in range(0, len(filtered_data), 4)]

        for i, sublist in enumerate(split_list):
            while len(sublist) < 4:
                sublist.append("")
            split_list[i] = sublist

        data = []
        
        for item in split_list:
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
        errs = []
        for entry in entries:
            entry = entry.strip()
            if entry:
                try:
                    cernyrytir = cerny_rytir(CR, entry, exclude_zero)
                    results.extend(cernyrytir)
                except:
                    errs.append("Failed to get data from" + CR)
                
                try:
                    blacklotus = black_lotus(BL, entry, exclude_zero)
                    results.extend(blacklotus)
                except:
                    errs.append("Failed to get data from" + BL)
                try:
                    najada = najada_games(NG, entry, exclude_zero)
                    results.extend(najada)
                except:
                    errs.append("Failed to get data from" + NG)

        return render_template('table.html', data=results, errors=errs)

    return render_template('form.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


