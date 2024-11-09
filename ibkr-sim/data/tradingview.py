import os
import pandas as pd
from datetime import datetime as dt
from pathlib import Path


from tvDatafeed import TvDatafeed, Interval


import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.FileHandler(f"tvdata.log", mode="w"),
        logging.StreamHandler(),
    ],
)

dataPath = r"ibkr/broker/data"
# If no such folder exists, create an empty folder
if not os.path.exists(dataPath):
    os.mkdir(dataPath)
    os.mkdir(dataPath+"/tmp")
    logging.info(f"creating Directory {dataPath}")

# get credentials for tradingview
username = "traderjoe1968@gmail.com"
password = "t$C(X4A]%p}F](z"
# initialize tradingview
tv = TvDatafeed(username=username, password=password, pro=True)


def ContractMonths(sym: str) -> set:
    mnth_codes = {
        "ZB": ("H", "M", "U", "Z"),
        "ZN": ("H", "M", "U", "Z"),
        "ZT": ("H", "M", "U", "Z"),
        "ZF": ("H", "M", "U", "Z"),
        "ZS": ("F", "H", "K", "N", "Q", "U", "X"),
        "ZM": ("F", "H", "K", "N", "Q", "U", "V", "Z"),
        "ZL": ("F", "H", "K", "N", "Q", "U", "V", "Z"),
        "ZC": ("F", "H", "K", "N", "U", "X", "Z"),
        "ZW": ("H", "K", "N", "U", "Z"),
        "ZO": ("H", "K", "N", "U", "Z"),
        "HE": ("G", "J", "K", "M", "N", "Q", "V", "Z"),
        "LE": ("G", "J", "M", "Q", "U", "V", "Z"),
        "GF": ("F", "H", "J", "K", "Q", "U", "V", "X"),
        "GC": ("G", "J", "M", "Q", "V", "Z"),
        "SI": ("H", "K", "N", "U", "Z"),
        "HG": ("H", "K", "N", "U", "Z"),
        "PA": ("H", "M", "U", "Z"),
        "PL": ("F", "J", "N", "V"),
        "6A": ("H", "M", "U", "Z"),
        "DX": ("H", "M", "U", "Z"),
        "6B": ("H", "M", "U", "Z"),
        "6C": ("H", "M", "U", "Z"),
        "6E": ("H", "M", "U", "Z"),
        "6J": ("H", "M", "U", "Z"),
        "6S": ("H", "M", "U", "Z"),
        "6N": ("H", "M", "U", "Z"),
        "6L": ("H", "M", "U", "Z"),
        "6M": ("H", "M", "U", "Z"),
        "6R": ("H", "M", "U", "Z"),
        "6Z": ("H", "M", "U", "Z"),
        "CL": ("F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"),
        "BZ": ("F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"),
        "WTI": ("F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"),
        "HO": ("F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"),
        "RB": ("F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"),
        "NG": ("F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"),
        "SB": ("H", "K", "N", "V"),
        "KC": ("H", "K", "N", "U", "Z"),
        "CC": ("H", "K", "N", "U", "Z"),
        "CT": ("H", "K", "N", "U", "Z"),
        "ZR": ("F", "H", "K", "N", "U", "X"),
        "OJ": ("F", "H", "K", "N", "U", "X"),
        "LBS": ("F", "H", "K", "N", "U", "X"),
        "LBR": ("F", "H", "K", "N", "U", "X"),
        "VIX": ("F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"),
        "VX": ("F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"),
        "ES": ("H", "M", "U", "Z"),
        "RTY": ("H", "M", "U", "Z"),
        "YM": ("H", "M", "U", "Z"),
        "NQ": ("H", "M", "U", "Z"),
        "SP": ("H", "M", "U", "Z"),
        "DJIA": ("H", "M", "U", "Z"),
    }
    return mnth_codes.get(sym, None)


def downloadData(Sym, Exchange):
    # futures data
    try:
        df = tv.get_hist(
            Sym, Exchange, Interval.in_5_minute, n_bars=30000, extended_session=True
        )
    except Exception:
        logging.exception("TvDataFeed Error")
        raise
    df.insert(0, "date", df.index.date)
    df.insert(1, "time", df.index.time)
    df.reset_index(inplace=True)
    del df["datetime"]
    del df["symbol"]

    return df


def read_data(filename: str) -> pd.DataFrame:
    cols = ["date", "time", "open", "high", "low", "close", "volume"]
    df = pd.read_csv(
        filename,
        header=0,
        names=cols,
        usecols=[0, 1, 2, 3, 4, 5, 6],
        parse_dates=True,
    )
    df.index = pd.to_datetime(df["date"] + " " + df["time"], format="mixed")
    df.sort_index(inplace=True)
    return df


def ContinuousContract(sym: str):
    raw_files = Path(dataPath+"/tmp").glob(f"{sym}*.csv")
    cc = pd.DataFrame()
    filelist = []
    for filename in raw_files:
        # Get Instrument
        sym = Path(filename).stem
        # Get Data
        data = read_data(filename)
        filelist.append((sym, data))

    filelist.sort(key=lambda x: x[1].index[-1])

    # Process Roll Date
    l = len(filelist)
    logging.info(f"CC: Last File {filelist[l-1][0]}")
    for index, data in enumerate(filelist):
        if index > 0:
            s1, d1 = filelist[index - 1]
            s2, d2 = filelist[index]
            logging.info(f"CC: Processing {s1}\t->\t{s2}")
            combined = pd.merge(
                d1["volume"],
                d2["volume"],
                suffixes=("_d1", "_d2"),
                how="outer",
                left_index=True,
                right_index=True,
            )
            combined = combined.resample("1D").sum()
            v_highest = (
                combined["volume_d2"].rolling(10).mean()
                > combined["volume_d1"].rolling(10).mean()
            )
            roll_date = v_highest[v_highest].index[0]
            d1.drop(d1[(d1.index >= roll_date)].index, inplace=True)
            d2.drop(d2[(d2.index < roll_date)].index, inplace=True)
            cc = pd.concat([cc, d1], ignore_index=False)
            if index == (l - 1):
                cc = pd.concat([cc, d2], ignore_index=False)

    # cc.sort_values(by=["date", "time"], ascending=[True, True])
    cc.sort_index(ascending=True)
    return cc


if __name__ == "__main__":
    startyear = 2017
    endyear = 2022
    # https://tvdb.brianthe.dev/
    symList = [
        ("ES", "CME_MINI", 0.25, 50, 14444),
        # ("CL", "NYMEX", 0.01, 1000, 17500),
        # ("6A", "CME", 0.00005, 100000, 4650),
        # ("ZB", "CBOT", 0.03125, 1000, 4562),
        # ("ZC", "CBOT", 0.25, 50, 4930),
        # ("ZS", "CBOT", 0.25, 50, 5988),
        # ("ZW", "CBOT", 0.25, 50, 4125),
        # ("KC", "ICEUS", 0.05, 375, 7811),
        # ("HG", "COMEX", 0.05, 250, 9933),
    ]

    logging.info("Starting import...")
    details = pd.DataFrame()
    try:
        for i, sym in enumerate(symList):
            CMonths = ContractMonths(sym[0])
            for yr in range(startyear, endyear):
                for mnth in CMonths:
                    contract = f"{sym[0]}{mnth}{yr}"
                    logging.info(f"Processing {contract}")
                    info = tv.search_symbol(sym[0], sym[1])
                    details = pd.concat(
                        [
                            details,
                            pd.DataFrame(
                                [
                                    {
                                        "Ticker": contract,
                                        "Fullname": info[0]["description"],
                                        "Currency": info[0]["currency_code"],
                                        "Country": info[0]["country"],
                                        "Ticksize": sym[2],
                                        "Pointvalue": sym[3],
                                        "Margin": sym[4],
                                    }
                                ]
                            ),
                        ],
                        ignore_index=True,
                    )
                    try:
                        data = downloadData(contract, sym[1])
                    except Exception:
                        continue
                    data.to_csv(
                        os.path.join(dataPath+"/tmp", contract + ".csv"),
                        columns=[
                            "date",
                            "time",
                            "open",
                            "high",
                            "low",
                            "close",
                            "volume",
                        ],
                        index=False,
                    )
            cc = ContinuousContract(sym[0])
            logging.info(f"Writing {dataPath}/{sym[0]}_cc.csv")
            cc.to_csv(f"{dataPath}/{sym[0]}_cc.csv", index=False)
        # Write details
        # details.to_csv(
        #     os.path.join(dataPath, "info.csv"),
        #     columns=[
        #         "Ticker",
        #         "Fullname",
        #         "Currency",
        #         "Country",
        #         "Ticksize",
        #         "Pointvalue",
        #         "Margin",
        #     ],
        #     index=False,
        # )

        # ab.updateDetails(stockdetails)
        logging.info("Finished Import")

    except Exception:
        logging.exception()
