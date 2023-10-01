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

        page.click('.icon.icon_arrow-down')

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

def black_lotus(url:str, search_query:str, exclude_zero:bool) -> list:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.type('input[name="string"]', search_query)
        page.press('input[name="string"]', 'Enter')
        page.wait_for_load_state('domcontentloaded')

        div_elements = page.query_selector_all('.products.products-block div')
        text_values = []
        for div_element in div_elements:
            text_values.append(div_element.inner_text())
        
        browser.close()

        filtered_data = [item.split('\n') for item in text_values if search_query.lower() in item.lower() and len(item.split('\n')) >= 4]

        unique_sublists = set()
        for sublist in filtered_data:
            unique_sublists.add(tuple(sublist))
        unique_sublists = [list(sublist) for sublist in unique_sublists]

        filtered_list = []
        for sublist in unique_sublists:
            filtered_sublist = [item for item in sublist if item and "DETAIL" not in item]
            while len(filtered_sublist) < 4:
                filtered_sublist.append('')
            
            edition_element = filtered_sublist[3]
            if " z edice " in edition_element:
                index = edition_element.find(' z edice ')
                if index != -1:
                    extracted_part = edition_element[index + len(' z edice '):]
                if extracted_part.endswith('.'):
                    extracted_part = extracted_part[:-1]
                filtered_sublist[3] = extracted_part
            
            qty_element = filtered_sublist[1]
            numeric_qty = ""
            if any(char.isdigit() for char in qty_element):
                for char in qty_element:
                    if char.isdigit():
                        numeric_qty += char
            if numeric_qty:
                filtered_sublist[1] = numeric_qty + " ks"
            else:
                filtered_sublist[1] = "0 ks"
            
            filtered_list.append(filtered_sublist)

        data = []
        
        for item in filtered_list:
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
                    errs.append("Failed to get data from: " + CR)
                
                try:
                    najada = najada_games(NG, entry, exclude_zero)
                    results.extend(najada)
                except:
                    errs.append("Failed to get data from: " + NG)
                
                try:
                    blacklotus = black_lotus(BL, entry, exclude_zero)
                    results.extend(blacklotus)
                except:
                    errs.append("Failed to get data from: " + BL)

        return render_template('table.html', data=results, errors=errs)

    return render_template('form.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


