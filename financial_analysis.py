from textblob import TextBlob
import pandas as pd

# 1. Define 10 mock headlines
headlines = [
    "Company A reports amazing, wonderful profit growth.", # Strong Positive
    "Company B suffers terrible, horrific losses this quarter.", # Strong Negative
    "Company C launches an excellent, outstanding new product.", # Strong Positive
    "Regulatory concerns are awful and disgusting for Company D.", # Strong Negative
    "Company E declares bankruptcy, a miserable failure.", # Negative
    "Company F announces a fantastic strategic partnership.", # Positive
    "Supply chain issues are annoying but defined.", # Neutral/Weak
    "Company H raises dividend, making shareholders very happy.", # Positive
    "Analysts downgrade Company I, calling it a dreadful investment.", # Negative
    "Company J beats earnings estimates, simply success." # Positive
]

# 2. Analyze polarity and create data
data = []
for headline in headlines:
    analysis = TextBlob(headline)
    score = analysis.sentiment.polarity
    
    # 3. Determine Trade Signal
    if score > 0.5:
        signal = "Buy"
    elif score < -0.5:
        signal = "Sell"
    else:
        signal = "Neutral"
        
    data.append({
        "Headline": headline,
        "Score": score,
        "Trade Signal": signal
    })

# Create DataFrame
df = pd.DataFrame(data)

# Display the DataFrame
pd.set_option('display.max_colwidth', None)
print(df)

# Save to CSV
df.to_csv('financial_sentiment.csv', index=False)
print("\nDataFrame saved to 'financial_sentiment.csv'")
