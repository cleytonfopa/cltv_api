import sys
from flask import Flask, request
from joblib import load
from utils import f, clean_DF, calculate_recency, predict_interval
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
    # cleaning:
    df = clean_DF(df)    
    # Calculanto agregados por dia:
    bet_by_day = (
      df
      .groupby(["Username", "registration_dt", "ftd_value","age", "date"])
      .agg(
        n_bets=("turnover", lambda x: np.sum(x>0)), 
        turnover=("turnover", np.sum),  
        ggr=("ggr", np.sum)
        )
      .reset_index()
    )
    bet_by_day
    # selecionando variáveis:
    bet_by_day = bet_by_day[["registration_dt", "date", "Username", "ftd_value", "age", "n_bets", "turnover", "ggr"]]
    bet_by_day = bet_by_day.sort_values(by=["registration_dt", "Username"])
    # numero máximo de dias de atividade na plataforma:
    max_days_sample=(bet_by_day["date"].max() - bet_by_day["registration_dt"].min()).days + 1
    # Criando as datas correntes para todos os usuários
    bet_by_day = (
      bet_by_day
      .groupby("Username")
      .apply(f,min_days=max_days_sample)
      .reset_index(drop=True)
    )
    # Filtrando para a data máxima de apostas da base:
    dt_max_bet = df["date"].max()
    bet_by_day = bet_by_day.query("date <= @dt_max_bet")
    ## Calculate Recency:
    # recency:
    recency_df = (
      bet_by_day
      .groupby("Username")
      .apply(
        calculate_recency, 
        date_max=datetime.datetime.today()
      )
    )
    recency_df = recency_df.reset_index()
    recency_df.columns = ["Username", "recency_value"]
    ## Calculate Frequency:
    frequency_df = bet_by_day.groupby("Username")["n_bets"].sum()
    frequency_df = frequency_df.reset_index()
    frequency_df.columns = ["Username", "frequency_value"]
    ## Calculate Monetary value:
    revenue_df = bet_by_day.groupby("Username")["ggr"].sum()
    revenue_df = revenue_df.reset_index()
    revenue_df.columns = ["Username", "revenue_value"]
    # turnover value:
    turnover_df = bet_by_day.groupby("Username")["turnover"].sum()
    turnover_df = turnover_df.reset_index()
    turnover_df.columns = ["Username", "turnover_value"]
    # merging:
    rfm_df = recency_df.merge(frequency_df, on="Username")
    rfm_df = rfm_df.merge(revenue_df, on="Username")
    rfm_df = rfm_df.merge(turnover_df, on="Username")
    # calculando ticket medio
    rfm_df["ticket_medio"] = rfm_df["turnover_value"] / rfm_df["frequency_value"]
    # fill na with 0:
    rfm_df["ticket_medio"] = rfm_df["ticket_medio"].fillna(0)
    # adding info about the player:
    rfm_df = rfm_df.merge(
        bet_by_day[["Username", "age", "ftd_value"]].drop_duplicates(),
        on="Username"
    )
    
    ## predicting:
    vars_ = [
      'recency_value', 'frequency_value', 'revenue_value', 
      'turnover_value', 'ticket_medio', 'age', 'ftd_value'
    ]
    # 1st model: classifier 
    # predicting if LTV = 0
    y_pred_clf = clf.predict(rfm_df[vars_])
    # if y_pred_clf == 1, then is null; else is not-null
    rfm_df["y_pred_clf"] = np.where(y_pred_clf == 1, 0, 1)
    rfm_df
    
    # se some prediction is not-null
    if any(rfm_df["y_pred_clf"] == 1):
        # predicting lower bound for those not-null (y_pred_clf = 1):
        rfm_df.loc[rfm_df["y_pred_clf"] == 1, "y_lower"] = predict_interval(
            rgr,
            rfm_df.query("y_pred_clf == 1")[vars_]
        )["lower"]
        rfm_df["y_lower"] = rfm_df["y_lower"].fillna(0)
        # predicting the average for those not-null (y_pred_clf = 1):
        rfm_df.loc[rfm_df["y_pred_clf"] == 1, "y_pred_rgr"] = predict_interval(
          rgr, 
          rfm_df.query("y_pred_clf == 1")[vars_]
        )["avg"]
        # predicting the upper bound for those not-null (y_pred_clf = 1):
        rfm_df.loc[rfm_df["y_pred_clf"] == 1, "y_upper"] = predict_interval(
          rgr, 
          rfm_df.query("y_pred_clf == 1")[vars_]
        )["upper"]
        rfm_df["y_upper"] = rfm_df["y_upper"].fillna(0)
        # consolidating predictions
        rfm_df["y_pred"] = rfm_df["y_pred_clf"].astype("float")
        # for those not null (y_pred_clf = 0)
        rfm_df.loc[rfm_df["y_pred_clf"] == 1, "y_pred"] = rfm_df.loc[rfm_df["y_pred_clf"] == 1, "y_pred_rgr"]
    else:
        # consolidating predictions
        rfm_df["y_pred"] = rfm_df["y_pred_clf"].astype("float")
        rfm_df["y_lower"] = 0.0
        rfm_df["y_upper"] = 0.0        
    # rounding:
    rfm_df['y_lower'] = np.round(rfm_df["y_lower"], 2)
    rfm_df['y_upper'] = np.round(rfm_df["y_upper"], 2)
    rfm_df['y_pred'] = np.round(rfm_df["y_pred"], 2)
    
    # returning:
    return rfm_df[["Username", "y_pred", "y_lower", "y_upper"]].to_json(orient="records")


if __name__ == '__main__':
    # If you don't provide any port the port will be set to 500
    try:
        port = int(sys.argv[1])
    except:
        port = 1234    
    # loading models:
    clf = load("clf_cltv_model.joblib")
    rgr = load("rgr_cltv_model.joblib")
    # running debug mode:
    app.run(port=port, debug=True)

