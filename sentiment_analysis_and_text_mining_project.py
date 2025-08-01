# -*- coding: utf-8 -*-
"""Sentiment Analysis and Text Mining Project.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1V7aKXlfBuXX9rUyYltMZerLawnpdMSPz
"""

import pandas as pd
import re
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

"""## **Data preparation**"""

# Load both datasets for McCafé and Tim Hortons
Mc = pd.read_csv('reviews_data_Mc.csv')
Tim = pd.read_csv('reviews_data_Tim.csv')

# Add a new column to each dataset
Mc['Type'] = 'Mc Cafe'
Tim['Type'] = 'Tim Hortons'

# Combine both datasets
df = pd.concat([Mc, Tim], ignore_index=True)

# Check data
df.head()

total_reviews=df.to_dict(orient='records')

reviews = [
    {
        **review,
        'Score': int(review['Stars'].split()[0]) if 'Stars' in review and review['Stars'] else None
    }
    for review in total_reviews
    if isinstance(review.get('Details'), str) and review['Details'].strip() != ''
]

# Check data
reviews[0:3]

"""## **Creating a Tokenizer**"""

def tokenize(text):
    if not isinstance(text, str):
        return []
    lowercase_text = text.lower()
    tokens = re.findall(r'\b\w+\b', lowercase_text)
    return [t for t in tokens if t not in ENGLISH_STOP_WORDS]

all_tokens = []

for review in reviews:
    if review.get("Details"):
        tokens = tokenize(review["Details"])
        all_tokens.extend(tokens)

all_tokens

"""## **Sparse Vectors**"""

#def vectorize_binary(tokens):
#    return {token: 1 for token in set(tokens)}

"""## **TF Vectorization**"""

def vectorize_tf(tokens):
    tf = {}
    for token in tokens:
        if token in tf:
            tf[token] += 1
        else:
            tf[token] = 1
    return tf

"""## **Calculating IDF**"""

from math import log

N = len(reviews) # total number of documents

doc_freq = {} # document frequency for each word
for review in reviews:
  if not review['Details']:
    continue # some reviews do not have any content, skip these
  doc = tokenize(review['Details'])
  unique_tokens = set(doc) # only count once per document
  for token in unique_tokens:
      doc_freq[token] = doc_freq.get(token, 0) + 1

idf_dict = {}
for token, df in doc_freq.items():
    idf_dict[token] = log(N / df)

idf_dict

"""## **Results**"""

# Sort tokens by IDF score
sorted_idf = sorted(idf_dict.items(), key=lambda x: x[1])

# Lowest IDF scores (most common words)
print("20 Most Common Words (Lowest IDF):")
for token, score in sorted_idf[:20]:
    print(f"{token}: {score:.4f}")

# Highest IDF scores (most unique words)
print("\n5 Most Unique Words (Highest IDF):")
for token, score in sorted_idf[-5:]:
    print(f"{token}: {score:.4f}")

"""## **TF-IDF Vectorization**"""

def vectorize_tf_idf(tokens):
    tf = {}
    for token in tokens:
        if token in tf:
            tf[token] += 1
        else:
            tf[token] = 1

    tf_idf = {}
    for token, doc_freq in tf.items():
        if token in idf_dict:
            tf_idf[token] = doc_freq * idf_dict[token]

    return tf_idf

tf_idf = vectorize_tf_idf(all_tokens)
tf_idf

"""## **Downloading a Lexicon**"""

!wget https://raw.githubusercontent.com/wd13ca/BAN200-Summer-2025/refs/heads/main/lexicon.txt

lexicon = {}

with open("lexicon.txt", "r") as file:
    for line in file:
        word, score = line.strip().split('\t')
        lexicon[word] = float(score)

lexicon

def sparse_dot_product(vec1, vec2):
     return sum(vec1[token] * vec2[token] for token in vec1 if token in vec2)

"""## **Sentiment score**"""

results = []

for review in reviews:
    details = review.get('Details', '')
    if not isinstance(details, str) or not details.strip():
        continue  # skip if Details is empty or not a string

    tokens = tokenize(details)

    if not tokens:
        continue  # skip reviews that result in no tokens

    tf = vectorize_tf(all_tokens)
    sentiment_score = sparse_dot_product(tf, lexicon)
    star_rating = review['Score']
    results.append((sentiment_score, star_rating))

results

"""## **Evalutation**"""

# Store sentiment scores grouped by star rating (excluding zero scores)
scores_by_rating = {}

for sentiment_score, star_rating in results:
    if sentiment_score == 0:
        continue  # skip neutral (zero) sentiment scores
    if star_rating not in scores_by_rating:
        scores_by_rating[star_rating] = []
    scores_by_rating[star_rating].append(sentiment_score)

# Calculate and print average sentiment and review count per rating
print("⭐ Average Sentiment Score by Star Rating (non-zero only):\n")
for rating in sorted(scores_by_rating):
    scores = scores_by_rating[rating]
    avg_score = sum(scores) / len(scores)
    count = len(scores)
    print(f"{rating} stars: {avg_score:.2f} (n = {count} reviews)")

"""## **K-Means**"""

from math import sqrt

def cosine_similarity(vec1, vec2):
    """
    Computes cosine similarity between two sparse vectors (dicts).
    """
    dot = sparse_dot_product(vec1, vec2)
    mag1 = sqrt(sparse_dot_product(vec1, vec1))
    mag2 = sqrt(sparse_dot_product(vec2, vec2))
    if mag1 == 0 or mag2 == 0:
        return 0.0  # Avoid division by zero
    return dot / (mag1 * mag2)

def mean_vector(vectors):
    """Averages a list of sparse vectors."""
    summed = {}
    for vec in vectors:
        for key, value in vec.items():
            summed[key] = summed.get(key, 0) + value
    count = len(vectors)
    return {k: v / count for k, v in summed.items()}

import random
valid_reviews = [r for r in reviews if r.get('Details')]
sampled_reviews = random.sample(valid_reviews, 1781)

for i, review in enumerate(sampled_reviews):
		tf_idf = vectorize_tf_idf(tokenize(review['Details']))
		sampled_reviews[i]['tf-idf'] = tf_idf

# Step 1: Randomly initialize centroids
k = 4
centroids = random.sample([r['tf-idf'] for r in sampled_reviews], k)

for iteration in range(100):
    print(f"Iteration {iteration+1}")

    # Step 2: Assign documents to closest centroid
    clusters = [[] for _ in range(k)]
    for doc in sampled_reviews:
        similarities = [cosine_similarity(doc['tf-idf'], centroid) for centroid in centroids]
        best_cluster = similarities.index(max(similarities))
        clusters[best_cluster].append(doc)

    # Step 3: Update centroids by averaging each cluster
    new_centroids = [mean_vector([review['tf-idf'] for review in cluster]) if cluster else centroids[i] for i, cluster in enumerate(clusters)]

    # Step 4: Check for convergence (no change in centroids)
    if new_centroids == centroids:
        print("Converged.")
        break
    centroids = new_centroids

for i, cluster in enumerate(clusters):
    print(f"Cluster {i}: {len(cluster)} reviews")

for i, cluster in enumerate(clusters):
    print(f"\n=== Cluster {i} ===")
    for review in cluster[:10]:
        print("-", review['Details'][:200])  # print first 200 characters

for i, cluster in enumerate(clusters):
    scores = [review['Score'] for review in cluster]
    avg_score = sum(scores) / len(scores) if scores else 0
    print(f"Cluster {i} average rating: {avg_score:.2f}")

from wordcloud import WordCloud
import matplotlib.pyplot as plt

for i, centroid in enumerate(centroids):
    wc = WordCloud(width=400, height=200)
    wc.generate_from_frequencies(centroid)
    plt.figure()
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title(f"Centroid {i} Word Cloud")
    plt.show()

def sparse_dot_product(vec1, vec2):
    contributions = {}
    total = 0

    for token in vec1:
        if token in vec2:
            freq = vec1[token]
            weight = vec2[token]
            product = freq * weight
            contributions[token] = {
                'frequency': freq,
                'weight': weight,
                'contribution': product
            }
            total += product

    # ✅ Sort by contribution (descending)
    sorted_contributions = sorted(
        contributions.items(),
        key=lambda x: x[1]['contribution'],
        reverse=True
    )

    # ✅ Pretty print
    if sorted_contributions:
        print(f"{'Token':<15} {'Freq':<5} {'Weight':<8} {'Contribution':<12}")
        print("-" * 45)
        for token, values in sorted_contributions:
            print(f"{token:<15} {values['frequency']:<5} {values['weight']:<8} {values['contribution']:<12.2f}")
    else:
        print("No matching tokens found in both vectors.")

    print(f"\nTotal dot product: {total:.2f}\n")
    return total

sparse_dot_product(tf, lexicon)