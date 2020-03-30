import pandas as pd
import numpy as np

jk_github = "https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_daily_reports"

df = pd.read_html(jk_github)[0]
daily_reports = df.loc[df["Name"].str.contains('.csv', regex=False), "Name"]

df1 = pd.read_html("https://www.thesun.co.uk/news/11233604/which-countries-are-on-coronavirus-lockdown-spain-italy/")

print(df1)
