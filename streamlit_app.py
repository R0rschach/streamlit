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
st.image("banner.png", use_column_width=True)
st.write("# Risk Management through Huma Protocol’s Evaluation Agent")
st.write(
    "*Discover the power of Huma Protocol's Evaluation Agent and the security it brings to the DeFi lending ecosystem. Evaluation Agents can leverage sophisticated analysis techniques to ensure accurate underwriting decisions in a community-driven system.*"
)
st.write("## The Challenge of Robust Underwriting in DeFi Lending")
st.write("""
In the Huma Protocol, establishing a reliable underwriting process is crucial, especially since we do not utilize an over-collateralized strategy where borrowers' assets secure their loans. A strong underwriting mechanism is vital to protect lending pools from losing money due to fraudulent activities or borrowers defaulting on loans. To tackle this challenge, Huma Protocol incorporates machine learning-powered Evaluation Agents (EAs) that analyze complex signals to deliver precise underwriting decisions for these loans.

The Evaluation Agent (EA) functions as the risk management layer within the Huma Protocol, accountable for making informed underwriting decisions for the lending pools it supports. The objective of the EA platform is to develop a secure, community-driven system that facilitates accurate underwriting on a large scale while preserving transparency and decentralization.
""")
         
st.write("## Lending Pools, Evaluation Agents and Signals")
st.write("EAs are designed to be decentralized, with each agent operating as a microservice that implements a standard interface for interacting with the Huma SDK and Huma contracts. Although Huma Protocol does not mandate EAs to open-source their models for anti-fraud purposes, the core development team behind Huma Protocol, along with the Pool Owner, audits and validates the EA before approving it for underwriting.")
st.image("system.png", use_column_width=True)
st.write("By enabling EAs to either specialize in catering to specific pools or adopting a more generic approach, the protocol ensures the necessary flexibility and adaptability for the rapidly evolving DeFi lending ecosystem.")

st.write("""
### EA Rewards and Responsibilities

EAs are playing a very critical role in the Huma Protocol. To prevent rogue EA, they are required to provide meaningful contributions to the liquidity pool so they have enough skin in the game. 

At the same time, they should be properly rewarded for the hard work of underwriting those requests and taking the risk. So they are taking a percentage of the pool income too. The share can be configured for each pool.
""")

st.write("""
## Example: Request Finance Invoice Factoring
In order to showcase the Evaluation Agent's (EA) capabilities, let’s build a simple EA for factoring Request Finance invoices.

Request Finance is one of the largest web3 finance platforms built on top of the Request Network protocol, with over $300 million in crypto payments sent using their invoicing features. By partnering with Huma, Request Finance tokenizes their invoices into ERC721 receivables that can be factored by lending pools on the Huma Protocol, giving users immediate access to their future income.

At its core, a receivable is a future payment contract with immutable metadata that can be verified by other trusted or trustless sources. Any source of income can be turned into a receivable and underwritten by an EA. EAs extract a number of metadata fields from Request Finance’s receivables including estimated payer address, expected payment amount, and due date and verify them against on-chain historical transactions and Request Network Protocol’s data. Once it has extracted all the data, an EA can apply whatever models and rules it has configured to approve the invoices for factoring.
""")
st.image("rn.png", use_column_width=True)

st.write("""
### A simple rule based EA

Most EAs are driven by AI models, but to make it simple let’s use a set of heuristic rules to demonstrate how EA works:

A significant portion of invoices on Request Network are settled on the Ethereum Mainnet. These payment records are on-chain and accessible for analysis. Leveraging this information, we can craft a set of heuristic rules concentrating on three key aspects of factoring risk: payer quality, payee quality, and the quality of the relationship between payer and payee.

* Payer Quality:
  * Payer has a history of making multiple on-chain payments
  * Payer's earliest transaction dates back a considerable time period
  * Payer has been active in recent weeks, with multiple transactions
  * Payer has a diverse payment history, involving several unique * payees
* Payee Quality:
  * Payee has a history of receiving multiple on-chain payments from different payers
  * Payee has received a substantial amount in total on-chain payments
  * Payee has a recent history of receiving a significant amount on-chain
* Payer and Payee Relationship Quality:
  * The payer and payee pair share a history of previous on-chain interactions

Based on these assumptions, we can create a set of rules to filter out those requests that don't meet the quality bar. And let the ones qualified to do invoice factoring. 

Let’s look at this table that demonstrates the impact of different filter rules. Each rule was evaluated individually, measuring the number of requests, payers, and payees that were filtered out. The combined impact of these rules showcases EA’s ability to analyze data and create sophisticated evaluation strategies.

You can tweak the settings in the sidebar on the left to changes the results. 
""")


result_container = st.container()

st.sidebar.subheader("Try tweak the rule settings")
payer_tab, payee_tab, others_tab = st.sidebar.tabs(["Payer Quality", "Payee Quality", "Other Filters"])

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

st.write("""
This is just a preview into the full Huma Protocol EA. The actual EA can access any on-chain or off-chain data source, through adapters built on the open-source Decentralized Signal Portfolio. While this simple example used a single signal adapter to access on-chain payment history, many signal adapters can be used in combination to bring a richer set of risk signals into decision-making.


Huma Protocol's Evaluation Agent and Decentralized Signal Portfolio are designed to enhance the capabilities and accuracy of underwriting in the DeFi lending space. By fostering a community-driven underwriting platform, the protocol aims to revolutionize the way such decisions are made in the DeFi ecosystem. 
""")
st.markdown("""---""")
st.write("""
**About Huma Finance**: Huma Finance is an income-backed DeFi protocol for the 99%. It enables businesses and people around the world to use their income and receivables as collateral to borrow against. Learn more https://huma.finance/.
""")
