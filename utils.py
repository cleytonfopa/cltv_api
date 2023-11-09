import pandas as pd 
import numpy as np

def clean_DF(dataset):
    # copying
    dataset = dataset.copy() 
    # rename columns
    dataset = dataset.rename(columns={"DOB": "birthDate", "Amount": "ftd_value"})
    # convert to date:
    dataset["data"] = pd.to_datetime(dataset.data).dt.date
    dataset["Deposit_Date"] = pd.to_datetime(dataset["Deposit_Date"]).dt.date
    dataset["birthDate"] = pd.to_datetime(dataset["birthDate"])
    # sort values:
    dataset = dataset.sort_values(by=["Deposit_Date", "Username"])
    # calculating age:
    dataset["age"] = pd.to_datetime(dataset["data"]).dt.year - dataset["birthDate"].dt.year
    # dropping:
    dataset = dataset.drop("birthDate", axis=1)
    dataset = dataset.reset_index(drop=True)
    return dataset

# função para calcular Recency
def calculate_recency(df, date_max):
    recency_value = date_max - df.query("n_bets > 0")["data"].max()
    # Se naT (nao houve nenhuma aposta):
    if pd.isnull(recency_value):
        recency_value = date_max - df["Deposit_Date"].max()
    recency_value = recency_value.days
    return recency_value
