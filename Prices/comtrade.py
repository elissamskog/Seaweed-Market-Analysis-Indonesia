import pandas as pd
import comtradeapicall

subscription_key = '<206b2bb1bc284df0a48db90a837e2557>'  # Replace with your actual key

mydf = comtradeapicall.previewFinalData(typeCode='C', freqCode='A', clCode='HS', period='2020',
                                        reporterCode='360', cmdCode='12', flowCode=None, partnerCode=None,
                                        partner2Code=None, customsCode=None, motCode=None, maxRecords=500, format_output='JSON',
                                        aggregateBy=None, breakdownMode='classic', countOnly=None, includeDesc=True)

if mydf.empty:
    print("Dataframe is empty. No data returned from the API.")
else:
    print("Data returned:")
    print(mydf.head())

mydf.to_excel('UN_volume data.xlsx', index=False)
