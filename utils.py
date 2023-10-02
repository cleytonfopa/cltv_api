import pandas as pd 
import numpy as np

def clean_DF(df):
    # removing cancelled bets:
    df = df.query("Cancelled == 0")
    # fixing date columns:
    df["Reg_Date"] = pd.to_datetime(df["Reg_Date"])
    df["DOB"] = pd.to_datetime(df["DOB"])
    # date
    df["registration_dt"] = df["Reg_Date"].dt.date
    # idade:
    df["age"] = pd.to_datetime(df["registration_dt"]).dt.year - df["DOB"].dt.year
    # rename
    df.rename(columns={"Amount": "ftd_value"}, inplace=True)
    # columns:
    players_input = ["User_ID", "name", "Username",
                     "registration_dt", "ftd_value",
                     "deposit_dt", "age", "no-affiliate"]
    # fixing numerical values:
    df["Bet"] = df["Bet"].str.replace(",", ".").astype("float")
    df["Win"] = df["Win"].str.replace(",", ".").astype("float")
    df["Cancelled"] = df["Cancelled"].astype("int")
    # date features:
    df["Date_Time"] = pd.to_datetime(df["Date_Time"])
    df["date"] = df["Date_Time"].dt.date
    # ggr
    df["ggr"] = df["Bet"] - df["Win"]
    # renaming
    df.rename(columns={"Bet": "turnover"}, inplace=True)
    return df

# function to guarantee at least 180 days:
def f(x, min_days=181):
    x = pd.merge(
        pd.DataFrame({"t1": range(min_days)}),
        x,
        on="t1",
        how="left"
    )
    if x.dropna().shape[0] == 0:
        return x.dropna()
    else:    
       x["ftd_value"].fillna(x["ftd_value"].dropna().unique()[0], inplace=True)    
       x["age"].fillna(x["age"].dropna().unique()[0], inplace=True)
       x["Username"].fillna(x["Username"].dropna().unique()[0], inplace=True)
       #x["no-affiliate"].fillna(x["no-affiliate"].dropna().unique()[0], inplace=True)
       x["n_bets"].fillna(0, inplace=True)
       x["turnover"].fillna(0, inplace=True)
       x["ggr"].fillna(0, inplace=True)
       return x

# função para calcular Recency
def calculate_recency(df, window=7):
   most_recent_value = df.query("n_bets > 0")["t1"].max()
   recency_value = window-1-most_recent_value
   return recency_value



