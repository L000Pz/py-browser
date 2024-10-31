import requests
import threading
import multiprocessing
from multiprocessing import Queue, Manager
from bs4 import BeautifulSoup
from termcolor import colored

def fetch_url_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        def parse_element(element):
            display_text = ''
            if isinstance(element, str): 
                return element.strip() + '\n'
            if element.name in ['script', 'style']:
                return display_text 
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                display_text += f"\033[91m{element.get_text(strip=True)}\033[0m\n\n"
            elif element.name == 'hr':
                display_text += '-' * 40 + '\n\n'
            elif element.name == 'p':
                display_text += f"{element.get_text()}\n\n"
            elif element.name == 'ul':
                for li in element.find_all('li', recursive=False):
                    display_text += f"* {li.get_text()}\n"
            elif element.name == 'li':
                display_text += f"* {element.get_text()}\n"
            else:
                for child in element.children:
                    display_text += parse_element(child)
            return display_text

        styled_html = ""
        for tag in soup.children:
            styled_html += parse_element(tag)

        return styled_html
    except requests.exceptions.RequestException as e:
        return f"Failed to fetch {url}: {e}"

def tab_interaction(tab_id, queue, html_storage):
    def user_input_thread():
        while True:
            url = queue.get()
            if url.lower() == 'exit':
                print(f"Tab {tab_id} is closing...")
                break
            html_content = fetch_url_content(url)
            html_storage[tab_id] = html_content

    input_thread = threading.Thread(target=user_input_thread)
    input_thread.start()
    input_thread.join()

def main_menu():
    manager = Manager()
    html_storage = manager.dict()
    tabs = []
    tab_counter = 1

    while True:
        print("\nMain Menu:")
        print("1. New Tab")
        print("2. List Tabs")
        print("3. Send URL to Tab")
        print("4. View HTML Content of Tab")
        print("5. Close Tab")
        print("6. Exit")

        choice = input("Choose an option: ")
        if choice == '1':
            queue = Queue()
            new_tab = multiprocessing.Process(target=tab_interaction, args=(tab_counter, queue, html_storage))
            new_tab.start()
            tabs.append((tab_counter, new_tab, queue))
            tab_counter += 1
        elif choice == '2':
            print("\nCurrent Tabs:")
            for tab_id, tab_proc, _ in tabs:
                print(f"Tab {tab_id} (PID: {tab_proc.pid})")
        elif choice == '3':
            tab_id = int(input("Enter Tab ID to send URL: "))
            url = input("Enter URL (or type 'exit' to close the tab): ")
            for tid, _, queue in tabs:
                if tid == tab_id:
                    queue.put(url)
                    break
        elif choice == '4':
            tab_id = int(input("Enter Tab ID to view HTML content: "))
            if tab_id in html_storage:
                print(f"\nHTML Content of Tab {tab_id}:\n")
                print(html_storage[tab_id])
            else:
                print(f"No HTML content available for Tab {tab_id}.")
        elif choice == '5':
            tab_id = int(input("Enter Tab ID to close: "))
            for i, (tid, tab_proc, queue) in enumerate(tabs):
                if tid == tab_id:
                    queue.put('exit')
                    tab_proc.join()
                    tabs.pop(i)
                    html_storage.pop(tab_id, None)  
                    print(f"Tab {tab_id} closed.")
                    break
        elif choice == '6':
            print("Exiting...")
            for tab_id, tab_proc, queue in tabs:
                queue.put('exit')
                tab_proc.join()
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == '__main__':
    main_menu()