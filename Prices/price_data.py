import pandas as pd

def split_value_chain(df):
    df['Farmgate Price'] = None
    df['Collector Price'] = None
    df['Trader Price'] = None   
    for index, row in df.iterrows():
        value_chain = row['Value Chain'].split()
        # Determine if specific value chain stages are present
        has_farmgate = 'Farmgate' in value_chain
        has_collector = 'Collector' in value_chain
        has_trader = 'Trader' in value_chain

        # Assign Farmgate Price
        if has_farmgate:
            df.at[index, 'Farmgate Price'] = row['Low Price']
        # Assign Trader Price
        if has_trader:
            df.at[index, 'Trader Price'] = row['High Price']
        # Assign Collector Price based on the presence of farmgate or trader
        if has_collector:
            if not has_farmgate:
                df.at[index, 'Collector Price'] = row['Low Price']
            elif not has_trader:
                df.at[index, 'Collector Price'] = row['High Price']
        if not has_collector and not has_farmgate and not has_trader:
            df.at[index, 'Trader Price'] = row['High Price']
    return df

def parse_information(inf):
    # Check if the information is empty or NaN
    if pd.isna(inf) or inf == '':
        return None, ''

    species = None
    value_chain = ''

    inf = inf.lower()

    if 'cottonii' in inf or 'cottoni' in inf:
        species = 'Cottonii'
    elif 'grailaria' in inf or 'gracilaria' in inf or 'glacilaria' in inf:
        species = 'Gracilaria'
    elif 'spinosum' in inf:
        species = 'Spinosum'

    if 'farmer' in inf:
        value_chain += 'Farmgate '
    if 'collector' in inf or 'LC' in inf:
        value_chain += 'Collector '
    if 'trader' in inf:
        value_chain += 'Trader'
    
    return species, value_chain.strip()



def main():
    '''
    This script joins data from Jasuda and Whatsapp (and other potential data sources),
    it then formats the data according to a set of assumptions:
    Assumptions about the data in jasuda.xlsx:
        1. The price range pertains to the ranges of price in the value-chain specified (farmer -> collector -> trader)
        2. The date of pricing is updated on average biweekly, therefore the data in that date can be centralized between that date and the last date

    Assumption about the data in whatsapp.xlsx:
        All of the data is from traders (inter-trading data)
    '''


    j_df = pd.read_excel('/Users/elissamskog/VSC/alginnova/Prices/Data/jasuda.xlsx')
    w_df = pd.read_excel('/Users/elissamskog/VSC/alginnova/Prices/Data/whatsapp.xlsx', usecols=['Date', 'Location', 'Information', 'Average Price'])

    w_df['Date'] = pd.to_datetime(w_df['Date'], format='%d/%m/%Y').dt.strftime('%d-%m-%Y')  # Standardize the date format
    w_df['Information'] = 'Trader ' + w_df['Information'].astype(str)

    j_df['Average MC'] = j_df['Average MC'].astype(float).apply(lambda x: x/100 if x > 1 else x)   # Convert all moisture contents to decimals
    df = pd.concat([j_df, w_df], ignore_index=True)
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
    df.sort_values(by='Date', inplace=True)


    # Splits "Information" column into relevant information
    result = df['Information'].apply(parse_information)
    df['Species'], df['Value Chain'] = zip(*result)
    df = df.drop(columns=['Unnamed: 0', 'RL PRICE (Rp/Kg)', 'MC (%)', 'DC(%)', 'Information'])

    # Splits "Location" column into regional and provincial data
    location_mapping_df = pd.read_excel('/Users/elissamskog/VSC/alginnova/Prices/Data/location_mapping.xlsx')
    location_mapping_df = location_mapping_df.drop_duplicates()
    location_mapping_df.columns = ['Region', 'Province', 'Location']
    df = df.merge(location_mapping_df, on='Location', how='left')


    df = split_value_chain(df)
    df = df.drop(columns=['Low Price', 'High Price', 'Location', 'Value Chain'])


    species_list = ['Cottonii', 'Gracilaria', 'Spinosum', None]  # Including None as a species
    species_dfs = {species: df[df['Species'] == species] for species in species_list}

    # Outputting the first few rows of each DataFrame as an example
    gracilaria_df = species_dfs['Gracilaria']
    cottonii_df = species_dfs['Cottonii']
    spinosum_df = species_dfs['Spinosum']
    nullval_df = df[df['Species'].isnull()]

    return gracilaria_df, cottonii_df, spinosum_df, nullval_df


if __name__ == '__main__':
    main()