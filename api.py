import sys
from flask import Flask, request
from joblib import load
from utils import f, clean_DF, calculate_recency
import pandas as pd
import numpy as np

app = Flask(__name__)

@app.route("/predict_cltv", methods=["POST"])
def predict():
    # catching json:
    json_ = request.get_json()
    # convert to DF:
    df = pd.DataFrame(json_)
    # cleaning:
    df = clean_DF(df)
    # Calculanto agregados por dia:
    bet_by_day = df.groupby(["Username", "registration_dt", "ftd_value","age", "date"]).agg(n_bets=("turnover", lambda x: np.sum(x>0)), turnover=("turnover", np.sum),  ggr=("ggr", np.sum)).reset_index()
    # merge players and bets:
    bet_by_day.sort_values(by=["Username", "date"], inplace=True)
    # criando index de referencia:
    # t1: numero de dias entre a data da aposta e a data de referencia
    bet_by_day["t1"] = (pd.to_datetime(bet_by_day["date"]) - pd.to_datetime(bet_by_day["registration_dt"])).dt.days
    bet_by_day = bet_by_day.drop_duplicates()
    # selecionando variáveis:
    bet_by_day = bet_by_day[["t1", "Username", "ftd_value", "age", "n_bets", "turnover", "ggr"]]
    bet_by_day = bet_by_day.sort_values(by=["t1", "Username"])    
    # guarantee 7 days per user:
    bet_by_day = bet_by_day.groupby("Username").apply(f,min_days=7).reset_index(drop=True)    
    ## Calculate Recency:
    recency_df = bet_by_day.groupby("Username").apply(calculate_recency,window=7)
    recency_df = recency_df.reset_index()
    recency_df.columns = ["Username", "recency_value"]
    # NA são os casos em que nao houve nenhuma aposta dentro do window.
    recency_df["recency_value"] = recency_df["recency_value"].fillna(7)
    ## Calculate Frequency:
    frequency_df = bet_by_day.groupby("Username")["n_bets"].sum()
    frequency_df = frequency_df.reset_index()
    frequency_df.columns = ["Username", "frequency_value"]
    ## Calculate Monetary value:
    revenue_df = bet_by_day.groupby("Username")["ggr"].sum()
    revenue_df = revenue_df.reset_index()
    revenue_df.columns = ["Username", "revenue_value"]
    # merging:
    rfm_df = recency_df.merge(frequency_df, on="Username")
    rfm_df = rfm_df.merge(revenue_df, on="Username")    
    # adding info about the player:
    rfm_df = rfm_df.merge(
        bet_by_day[["Username", "age", "ftd_value"]].drop_duplicates(),
        on="Username"
    )
    ## predicting:
    vars_ = ["recency_value", "frequency_value", "revenue_value",
             "age", "ftd_value"]
    rfm_df['y_lower'] = np.round(models["q 0.10"].predict(rfm_df[vars_]),2)
    rfm_df['y_upper'] = np.round(models["q 0.90"].predict(rfm_df[vars_]), 2)
    rfm_df['y_pred'] = np.round(models["q 0.50"].predict(rfm_df[vars_]), 2)
    # returning:   
    return rfm_df[["Username", "y_pred", "y_lower", "y_upper"]].to_json(orient="records")


if __name__ == '__main__':
    # If you don't provide any port the port will be set to 500
    try:
        port = int(sys.argv[1])
    except:
        port = 1234    
    # loading model:
    models = load("cltv_model.joblib")
    # running debug mode:
    app.run(port=port, debug=True)

