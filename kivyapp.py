from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from playwright.sync_api import sync_playwright

TOGGLE = ["Exclude not in stock", "Include not in stock"]

def cerny_rytir(search_query:str, exclude_zero:bool) -> list:
    url = "https://cernyrytir.cz/index.php3?akce=3"
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
                        current_lines.insert(0, "Černý rytíř")
                        if exclude_zero and "0" in current_lines[5]:
                            current_lines = []
                        else:
                            data.append(current_lines)
                            current_lines = []
        browser.close()
        return data

class DataVisualizationApp(App):
    def build(self):
        self.data_layout = GridLayout(cols=7, spacing=5)

        button_layout = BoxLayout(orientation='horizontal', padding=10, spacing=0, size_hint=(1, 0.15), pos_hint={'top': 1})
        self.button = Button(text="Display Data", size_hint=(0.2, 1), pos_hint={'center_x': 0.5})
        self.button.bind(on_press=self.toggle_data_display)
        button_layout.add_widget(self.button)

        text_input_layout = BoxLayout(orientation='horizontal', padding=10, spacing=0, size_hint=(1, 0.3), pos_hint={'top': 1})
        self.text_input = TextInput(multiline=True, hint_text='Enter card name...', size_hint=(0.8, 1))
        text_input_layout.add_widget(self.text_input)
        
        self.toggle_state = True
        self.toggle_button = Button(text=TOGGLE[0], on_press=self.toggle_state_change, size_hint=(0.2, 1))
        text_input_layout.add_widget(self.toggle_button)

        main_layout = BoxLayout(orientation='vertical')
        main_layout.add_widget(button_layout)
        main_layout.add_widget(text_input_layout)
        main_layout.add_widget(self.data_layout)

        return main_layout

    def toggle_data_display(self, instance):
        if self.data_layout.children:
            self.data_layout.clear_widgets()
            self.button.text = "Display Data"
        else:
            self.populate_data_layout()
            self.button.text = "Clear"

    def toggle_state_change(self, instance):
        self.toggle_state = not self.toggle_state
        if self.toggle_state:
            self.toggle_button.text = TOGGLE[0]
        else:
            self.toggle_button.text = TOGGLE[1]

    def populate_data_layout(self):
        text = self.text_input.text
        check = self.toggle_state
        data = cerny_rytir(text, check)

        num_rows = len(data)
        num_columns = len(data[0])

        max_widths = [max(len(data[row][col]) for row in range(num_rows)) for col in range(num_columns)]

        for row in range(num_rows):
            for col in range(num_columns):
                label = Label(text=data[row][col], size_hint=(None, None), width=max_widths[col] * 10, halign='left', valign='middle', padding=(10, 10))
                label.bind(texture_size=label.setter('size'))
                self.data_layout.add_widget(label)

if __name__ == "__main__":
    DataVisualizationApp().run()
