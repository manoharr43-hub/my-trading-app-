def filter_top_trades(df):

    if df.empty:
        return df

    df = df.copy()

    score = []

    for i, row in df.iterrows():
        s = 0

        # Support/Resistance strength
        if row['Highlight'] == "🟢 Near Support" and row['Signal'] == "BUY":
            s += 2
        if row['Highlight'] == "🔴 Near Resistance" and row['Signal'] == "SELL":
            s += 2

        # Big player
        if row['Big Player'] != "":
            s += 2

        # Trend confirmation
        if (row['Signal'] == "BUY" and row['Trend'] == "UP") or \
           (row['Signal'] == "SELL" and row['Trend'] == "DOWN"):
            s += 1

        score.append(s)

    df['Score'] = score

    df = df.sort_values(by='Score', ascending=False)

    return df.head(5)
