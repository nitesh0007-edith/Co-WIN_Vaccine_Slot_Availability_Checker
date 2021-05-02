import datetime
import json
import numpy as np
import requests
import pandas as pd
import streamlit as st
from copy import deepcopy

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_mapping():
    df = pd.read_csv("district_mapping.csv")
    return df

def filter_column(df, col, value):
    df_temp = deepcopy(df.loc[df[col] == value, :])
    return df_temp


mapping_df = load_mapping()

mapping_dict = pd.Series(mapping_df["district id"].values,
                         index = mapping_df["district name"].values).to_dict()

rename_mapping = {
    'date': 'Date',
    'min_age_limit': 'Minimum Age Limit',
    'available_capacity': 'Available Capacity',
    'pincode': 'Pincode',
    'name': 'Hospital Name',
    'state_name' : 'State',
    'district_name' : 'District',
    'block_name': 'Block Name',
    'fee_type' : 'Fees'
    }

st.title('CoWIN Vaccination Slot Availability')

# numdays = st.sidebar.slider('Select Date Range', 0, 100, 10)
unique_districts = list(mapping_df["district name"].unique())
unique_districts.sort()


left_column_1, right_column_1 = st.beta_columns(2)
with left_column_1:
    numdays = st.slider('Select Date Range', 0, 100, 5)


with right_column_1:
    dist_inp = st.selectbox('Select District', unique_districts)

DIST_ID = mapping_dict[dist_inp]

base = datetime.datetime.today()
date_list = [base + datetime.timedelta(days=x) for x in range(numdays)]
date_str = [x.strftime("%d-%m-%Y") for x in date_list]

final_df = None
for INP_DATE in date_str:
    URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(DIST_ID, INP_DATE)
    response = requests.get(URL)
    if response.ok:
        resp_json = json.loads(response.text)['centers']
        df = pd.DataFrame(resp_json)
        if len(df):
            df = df.explode("sessions")
            df['min_age_limit'] = df.sessions.apply(lambda x: x['min_age_limit'])
            df['available_capacity'] = df.sessions.apply(lambda x: x['available_capacity'])
            df['date'] = df.sessions.apply(lambda x: x['date'])
            df = df[["date", "available_capacity", "min_age_limit", "pincode", "name", "state_name", "district_name", "block_name", "fee_type"]]
            if final_df is not None:
                final_df = pd.concat([final_df, df])
            else:
                final_df = deepcopy(df)
        else:
            st.error("No rows in the data Extracted from the API")
    else:
        st.error("Invalid response")

if len(final_df):
    final_df.drop_duplicates(inplace=True)
    final_df.rename(columns=rename_mapping, inplace=True)

    left_column_2, right_column_2 = st.beta_columns(2)
    with left_column_2:
        valid_pincodes = list(np.unique(final_df["Pincode"].values))
        pincode_inp = st.selectbox('Select Pincode', [""] + valid_pincodes)
        if pincode_inp != "":
            final_df = filter_column(final_df, "Pincode", pincode_inp)

    table = deepcopy(final_df)
    table.reset_index(inplace=True, drop=True)
    st.table(table)
else:
    st.error("No Data Found")
