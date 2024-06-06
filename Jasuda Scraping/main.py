import requests
from bs4 import BeautifulSoup
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed


LOGIN = 'https://www.jasuda.net/login_fail.php'
columns = ['Date', 'Location', 'RL PRICE (Rp/Kg)', 'MC (%)', 'DC(%)', 'Information']
login = {
    'email': 'elis.samskog@gmail.com',
    'password': 'Sile2000@'
}


def get_data(session):
    index_page = session.get('https://www.jasuda.net/infopasar_free.php/')
    soup = BeautifulSoup(index_page.text, 'html.parser')
    tables = soup.find_all('table', style="border-collapse:collapse")
    table = tables[1]
    rows = []

    for row in table.find_all('tr')[2:]:
        cells = row.find_all('td')
        row_data = []
        if len(cells) > 1:
            for cell in cells[1:]:  # Adjust slicing if necessary
                cell_data = cell.get_text(strip=True)
                row_data.append(cell_data)
        date = row_data[0]
        if len(row_data) == 6:
            rows.append(row_data)
    print(rows)
    return rows


def thread_function(session):
    index_page = session.get('https://www.jasuda.net/infopasar_free.php/')
    soup = BeautifulSoup(index_page.text, 'html.parser')
    return soup


def main():
    data_list = []
    iterations = 4000
    # Number of threads to use
    num_threads = 10

    with requests.Session() as s:
        response = s.post(LOGIN, data=login)

        if response.url == 'https://www.jasuda.net/loginsuk.php':
            print("Successful Login")

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(get_data, s) for _ in range(iterations)]

            for future in as_completed(futures):
                data_list.extend(future.result())

    df = pd.DataFrame(data_list, columns=columns)
    df = df.drop_duplicates(keep='first')
    df.to_excel('alginnova/Jasuda Scraping/output.xlsx', index=False)


if __name__ == '__main__':
    main()
