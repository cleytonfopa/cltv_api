import sys
from flask import Flask, request
from joblib import load
from utils import calculate_recency
import pandas as pd
import numpy as np
import datetime

app = Flask(__name__)

@app.route("/predict_cltv", methods=["POST"])
def predict():
    # catching json:
    json_ = request.get_json()
    # convert to DF:
    df = pd.DataFrame(json_)
    # convert to date:
    df["data"] = pd.to_datetime(df["data"])
    df["Deposit_Date"] = pd.to_datetime(df["Deposit_Date"])
    # Filterig for the max date:
    dt_max_bet = datetime.datetime.today()
    df = df.query("data <= @dt_max_bet")
    ## Calculate Recency:
    recency_df = (
      df
      .groupby("Username")
      .apply(
        calculate_recency, 
        date_max= dt_max_bet
      )
    )
    recency_df = recency_df.reset_index()
    recency_df.columns = ["Username", "recency_value"]
    ## Calculate Frequency:
    frequency_df = df.groupby("Username")["n_bets"].sum()
    frequency_df = frequency_df.reset_index()
    frequency_df.columns = ["Username", "frequency_value"]
    ## Calculate Monetary value:
    monetary_df = df.groupby("Username")["ggr"].sum()
    monetary_df = monetary_df.reset_index()
    monetary_df.columns = ["Username", "monetary_value"]
    # Calculate turnover value:
    turnover_df = df.groupby("Username")["turnover"].sum()
    turnover_df = turnover_df.reset_index()
    turnover_df.columns = ["Username", "turnover_value"]
    # merging:
    rfm_df = recency_df.merge(frequency_df, on="Username")
    rfm_df = rfm_df.merge(monetary_df, on="Username")
    rfm_df = rfm_df.merge(turnover_df, on="Username")
    # calculando ticket medio
    rfm_df["ticket_medio"] = rfm_df["turnover_value"] / rfm_df["frequency_value"]
    # fill na with 0:
    rfm_df["ticket_medio"] = rfm_df["ticket_medio"].fillna(0)
    # adding info about the player:
    rfm_df = rfm_df.merge(
        df[["Username", "age", "ftd_value"]].drop_duplicates(),
        on="Username"
    )
    ## predicting:
    vars_ = [
      'recency_value', 'frequency_value', 'monetary_value', 'turnover_value',
      'ticket_medio', 'ftd_value', 'age'
    ]
    # predicting LTV
    rfm_df["ltv_pred"] = rgr.predict(rfm_df[vars_])
    # rounding:
    rfm_df["ltv_pred"] = np.round(rfm_df["ltv_pred"], 2)
    # returning:
    return rfm_df[["Username", "ltv_pred"]].to_json(orient="records")


if __name__ == '__main__':
    # If you don't provide any port the port will be set to 500
    try:
        port = int(sys.argv[1])
    except:
        port = 1234    
    # loading models:
    rgr = load("cltv_model.joblib")
    # running debug mode:
    app.run(port=port, debug=True)

