from collections import Counter
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

character_n_grams_dict = dict()
word_n_grams_dict = dict()


def character_n_grams(n, document, corpus):
    hashed_corpus = hash(str(corpus))
    if (n, hashed_corpus) in character_n_grams_dict:
        vectorizer = character_n_grams_dict[(n, hashed_corpus)]
    else:
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(n, n))
        vectorizer = vectorizer.fit(corpus)
        character_n_grams_dict[(n, hashed_corpus)] = vectorizer
    matrix = vectorizer.transform([document])
    assert matrix.max() != 0
    return matrix


def word_n_grams(n, document, corpus, max_df=1.0, stop_words=None):
    hashed_corpus = hash(str(corpus))
    if (n, max_df, stop_words, hashed_corpus) in character_n_grams_dict:
        vectorizer = word_n_grams_dict[(n, max_df, stop_words, hashed_corpus)]
    else:
        vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(n, n), stop_words=stop_words, max_df=max_df).fit(
            corpus)
        word_n_grams_dict[(n, max_df, stop_words, hashed_corpus)] = vectorizer
    return vectorizer.transform([document])


def avg_stdev_words_per_sentence(document):
    document_splitted = re.split('. |! |\? ', document)
    # TODO: Maybe remove newlines
    words_per_sentence = []
    for sentence in document_splitted:
        words_per_sentence.append(len(sentence.split()))
    return [[np.average(words_per_sentence)], [np.std(words_per_sentence)]]


def vocabulary_diversity(document):
    document = "".join(c for c in document if c not in ':;?!.,()')
    document_splitted = document.split()
    counter = Counter(document_splitted)
    return [[len(list(counter)) / len(document_splitted)]]


def avg_marks(document):
    document_splitted = document.split('.')
    number_of_sentences = len(document_splitted)
    marks = "".join(c for c in document if c in ',;:()!?')
    counter = Counter(marks)
    representation = []
    for element in ',;:()!?':
        try:
            representation.append([counter[element]/number_of_sentences])
        except KeyError:
            representation.append([0])

    return representation


def concatenation(document):
    features = avg_stdev_words_per_sentence(document)
    features.append(vocabulary_diversity(document)[0])
    features.extend(avg_marks(document))
    return np.reshape(features, (np.shape(features)[0], 1)).tolist()
