import pandas as pd
from dateutil.parser import parse

# Mapping of Indonesian month names to English
indonesian_to_english_months = {
    'Jan': 'Jan', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Apr', 'Mei': 'May',
    'Jun': 'Jun', 'Jul': 'Jul', 'Agu': 'Aug', 'Sep': 'Sep', 'Okt': 'Oct',
    'Nov': 'Nov', 'Des': 'Dec', 'Januari': 'January', 'Februari': 'February',
    'Maret': 'March', 'April': 'April', 'Juni': 'June', 'Juli': 'July',
    'Agustus': 'August', 'September': 'September', 'Oktober': 'October',
    'Nopember': 'November', 'Desember': 'December', 'Augstus':'August'
}

def convert_date(date_str):
    # Replace Indonesian month names with English equivalents
    for ind_month, eng_month in indonesian_to_english_months.items():
        date_str = date_str.replace(ind_month, eng_month)

    # Parse the date string to a datetime object and format it to dd-mm-yyyy
    return parse(date_str).strftime('%d-%m-%Y')


def split_price_and_average(price_range):
    try:
        low_price, high_price = price_range.split('-')
        low_price = float(low_price.replace(',', '').strip())
        high_price = float(high_price.replace(',', '').strip())
        average_price = (low_price + high_price) / 2
        return low_price, high_price, average_price
    except ValueError:
        return None, None, None


def calculate_average_percentage(percentage_range):
    try:
        # Remove '%' sign and spaces
        percentage_range = percentage_range.replace('%', '').strip()

        # Handle single value
        if '-' not in percentage_range:
            if percentage_range.startswith('<'):
                return float(percentage_range[1:].strip())
            return float(percentage_range)

        # Handle range
        low, high = percentage_range.split('-')
        return (float(low.strip()) + float(high.strip())) / 200
    except:
        return None


df = pd.read_excel('Jasuda Scraping/output.xlsx')

# Apply the conversion function to the 'Date' column
df['Date'] = df['Date'].apply(convert_date)
df[['Low Price', 'High Price', 'Average Price']] = df['RL PRICE (Rp/Kg)'].apply(lambda x: pd.Series(split_price_and_average(x)))
df['Average MC'] = df['MC (%)'].apply(calculate_average_percentage)
df['Average DC'] = df['DC(%)'].apply(calculate_average_percentage)

df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
df.sort_values(by='Date')
df.to_excel('formatted.xlsx')
