import streamlit as st
import pandas as pd

from typing import List, Tuple
from datetime import datetime, timedelta


@st.cache_data
def load_data():
    return pd.read_pickle("rn.pickle")


@st.cache_data
def load_payer_data():
    return pd.read_pickle("payer.pickle")


@st.cache_data
def load_payee_data():
    return pd.read_pickle("payee.pickle")


@st.cache_data
def load_pair_data():
    return pd.read_pickle("pair.pickle")


def simple_filter_box(
    df: pd.DataFrame,
    payer_merged: pd.DataFrame = load_payer_data(),
    payee_merged: pd.DataFrame = load_payee_data(),
    pair_df: pd.DataFrame = load_pair_data(),
    tokens: List[str] = ["USDT", "DAI", "USDC"],
    min_amount_usd: int = 100,
    min_payer_txns: int = 10,
    max_payer_txn_days: int = 90,
    min_payer_txns_28d: int = 2,
    min_payer_unique_payee: int = 3,
    min_payee_txns: int = 2,
    min_payee_income: int = 5000,
    min_payee_income_28d: int = 1000,
    min_pair_txns: int = 2,
) -> pd.DataFrame:
    copy_df = df.copy()
    # copy_df = copy_df[copy_df.token_name.isin(tokens)].query(f"amount_usd > {min_amount_usd}")
    merged_df = pd.merge(copy_df, payer_merged, on="from", how="left")
    merged_df = pd.merge(merged_df, payee_merged, on="to", how="left")
    merged_df = pd.merge(merged_df, pair_df, on=["from", "to"], how="left")

    filtered = (
        merged_df.assign(f_request_amount=lambda df: df.amount_usd < min_amount_usd)
        .assign(f_payer_txns=lambda df: df.payer_txns < min_payer_txns)
        .assign(f_payer_tenure=lambda df: df.payer_earliest_txn > datetime.today() - timedelta(days=max_payer_txn_days))
        .assign(f_payer_txns_28d=lambda df: df.payer_txns_28d < min_payer_txns_28d)
        .assign(f_payer_unique_payee=lambda df: df.payer_unique_payee < min_payer_unique_payee)
        .assign(f_payee_txns=lambda df: df.payee_txns < min_payee_txns)
        .assign(f_payee_income=lambda df: df.payee_total_amount < min_payee_income)
        .assign(f_payee_income_28d=lambda df: df.payee_total_amount_28d < min_payee_income_28d)
        .assign(f_pair_txns=lambda df: df.pair_txns < min_pair_txns)
    )

    li = []
    mask = [False] * len(filtered)
    for col in filtered.columns:
        if col.startswith("f_"):
            li.append(
                {
                    "filter_name": col.replace("f_", ""),
                    "txns_left": (~filtered[col]).sum(),
                    "payers_left": filtered[~filtered[col]]["from"].nunique(),
                    "payees_left": filtered[~filtered[col]]["to"].nunique(),
                }
            )
            mask |= filtered[col]

    li.append(
        {
            "filter_name": "combined",
            "txns_left": (~mask).sum(),
            "payers_left": filtered[~mask]["from"].nunique(),
            "payees_left": filtered[~mask]["to"].nunique(),
        }
    )

    result = pd.DataFrame.from_records(li).assign(
        txn_filtered=lambda df: 1 - (df.txns_left / len(filtered)),
        payer_filtered=lambda df: 1 - df.payers_left / filtered["from"].nunique(),
        payee_filtered=lambda df: 1 - df.payees_left / filtered["to"].nunique(),
    )

    return result


data = load_data()


# st.subheader("Experiment with other settings")

# min_payer_txns = payer_col.slider('Number of transactions required for Payers', min_value=2, max_value=20, value=10, step=2)
# min_payee_txns = payee_col.slider('Number of transactions required for payees', min_value=0, max_value=10, value=2, step=1)
# st.write(simple_filter_box(data, min_payer_txns=min_payer_txns, min_payee_txns=min_payee_txns))

result_container = st.container()
result_container.subheader("Example Heuristic Rules")

st.subheader("Try tweak the rule settings")
payer_tab, payee_tab, others_tab = st.tabs(["Payer Quality", "Payee Quality", "Other Filters"])
payer_tab.subheader("Payer Quality")
min_payer_txns = payer_tab.slider("Min #transactions required ", min_value=2, max_value=20, value=10, step=2)
max_payer_txn_days = payer_tab.slider("Min wallet tenure (days)", min_value=30, max_value=180, value=90, step=10)
min_payer_txns_28d = payer_tab.slider(
    "Min #transactions required (last 28 days)", min_value=0, max_value=5, value=2, step=1
)
min_payer_unique_payee = payer_tab.slider(
    "Minimum number of unique payees for Payers", min_value=0, max_value=10, value=3, step=1
)

payee_tab.subheader("Payee Quality")
min_payee_txns = payee_tab.slider("Minimum #transactions required", min_value=0, max_value=10, value=2, step=1)
min_payee_income = payee_tab.slider(
    "Minimum total income (USD)", min_value=1000, max_value=10000, value=5000, step=1000
)
min_payee_income_28d = payee_tab.slider(
    "Minimum total income (last 28 days)", min_value=0, max_value=2000, value=1000, step=100
)

# other_col = st
others_tab.subheader("Other filters")
# tokens = other_col.multiselect('Token Allowed', ['USDT', 'DAI', 'USDC'], default=['USDT', 'DAI', 'USDC'])
min_amount_usd = others_tab.select_slider(
    "Min request amount allowed (USD)", options=[10, 100, 500, 1000, 5000, 10000, 100000]
)
min_pair_txns = others_tab.slider(
    "Min #transactions between the Payer and Payee required", min_value=0, max_value=10, value=2, step=1
)

result_container.dataframe(
    simple_filter_box(
        data,
        #   tokens=tokens,
        min_amount_usd=min_amount_usd,
        min_payer_txns=min_payer_txns,
        max_payer_txn_days=max_payer_txn_days,
        min_payer_txns_28d=min_payer_txns_28d,
        min_payer_unique_payee=min_payer_unique_payee,
        min_payee_txns=min_payee_txns,
        min_payee_income=min_payee_income,
        min_payee_income_28d=min_payee_income_28d,
        min_pair_txns=min_pair_txns,
    ).style.format({"txn_filtered": "{:.2%}", "payer_filtered": "{:.2%}", "payee_filtered": "{:.2%}"})
)
