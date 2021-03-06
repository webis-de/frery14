import os
import urllib
import zipfile
from sklearn.feature_extraction.text import TfidfVectorizer
import json
import yaml
import copy
import sys

train_corpora_url = 'http://www.uni-weimar.de/medien/webis/corpora/corpus-pan-labs-09-today/pan-14/pan14-data/pan14-authorship-verification-training-corpus-2014-04-22.zip'
train_corpora_dir = 'pan14-authorship-verification-training-corpus-2014-04-22'
data_dir = 'data'


class TfidfRepresentationSpace(object):
    def __init__(self, analyzer=None, ngram_range=0, stopwords=None, max_df=1.0, similarity=cosine_similarity):
        self.analyzer = analyzer
        self.ngram_range = ngram_range
        self.stopwords = stopwords
        self.max_df = max_df
        self.vectorizer = None
        self.document_matrix = None
        self.label = None
        self.name = None
        self.corpus = None
        self.unknown_text = None
        self.language = None
        self.genre = None
        self.similarity = similarity
        self.mean = None
        self.count = None

    def set_corpus(self, corpus):
        self.corpus = corpus

    def set_unknown_text(self, text):
        self.unknown_text = text

    def set_language(self, language):
        self.language = language

    def set_genre(self, genre):
        self.genre = genre

    def set_label(self, label):
        self.label = label

    def set_name(self, name):
        self.name = name

    def get_vectorizer(self):
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(analyzer=self.analyzer,
                                              ngram_range=self.ngram_range, stop_words=self.stopwords)
        return self.vectorizer

    def get_document_matrix(self):
        assert self.corpus is not None

        if self.document_matrix is None:
            self.document_matrix = self.get_vectorizer().fit_transform(self.corpus)
        return self.document_matrix

    def similarity(self, document1, document2):
        if self.vectorizer is not None:
            return self.similarity(self.get_vectorizer().transform(document1, True),
                                   self.get_vectorizer().transform(document2, True))
        else:
            raise Exception('No vectorizer with documents is set up')

    def get_count(self):
        if self.count is None:
            count = 0

            # find minimal similarity in corpus (between all documents in corpus)

            # Check for each document if the similarity with the unknown document is lower than the similarity to all other documents
            for document in self.corpus:
                min_incorpus_similarity = sys.maxsize
                for similarity_document in self.corpus:
                    if document == similarity_document:
                        continue
                    min_incorpus_similarity = min(min_incorpus_similarity,
                                                  self.similarity(document, similarity_document))
                if self.similarity(document, self.unknown_text) < min_incorpus_similarity:
                    count += 1
            self.count = count
        else:
            return self.count

    def get_mean(self):
        if self.mean is None:
            added_similarities = 0
            number_of_documents = 0
            for document in self.corpus:
                added_similarities += self.similarity(document, self.unknown_text)
                number_of_documents += 1
            self.mean = added_similarities / number_of_documents
        else:
            return self.mean

            # TODO: Implement TOT_count (added count over all representation spaces)


def cosine_similarity(vector1, vector2):
    # TODO: Search method for cosine similarity
    return 0


def correlation_coefficient(vector1, vector2):
    # TODO: Search method for correlation coefficient
    return 0


def may_download_training(url, prefix_dir, dir):
    if not os.path.exists(prefix_dir):
        os.makedirs(prefix_dir)
    if not os.path.exists(prefix_dir + '/' + dir):
        zip_file = prefix_dir + '/' + dir + '.zip'
        filename, headers = urllib.urlretrieve(url, zip_file)

        assert os.path.exists(zip_file)
        with zipfile.ZipFile(zip_file, "r") as z:
            z.extractall(prefix_dir)

        assert os.path.exists(prefix_dir + '/' + dir)
        os.remove(zip_file)


def may_unzip_corpus(dir_zips, data_dir, train_corpora_dir):
    for _, _, files in os.walk(dir_zips):
        for file in files:
            if file.endswith(".zip") and not os.path.exists(data_dir + '/' + train_corpora_dir + '/' + file[:-4]):
                with zipfile.ZipFile(data_dir + '/' + train_corpora_dir + '/' + file, "r") as z:
                    z.extractall(data_dir + '/' + train_corpora_dir + '/')

                # Unzipped file has an other name than zip file
                # assert os.path.exists(data_dir+'/'+train_corpora_dir+'/'+file[:-4])
                os.remove(data_dir + '/' + train_corpora_dir + '/' + file)


# TODO: Phrases: word per sentence mean and standard deviation
# TODO: Vocabulary diversity: total number of different terms divided by the total number of occurrences of words
# TODO: Punctuation: average of punctuation marks per sentence characters: "," ";" ":" "(" ")" "!" "?"

def set_labels(representationSpaces):
    for dirname in os.listdir(data_dir + '/' + train_corpora_dir):
        if dirname == '.DS_Store':
            continue
        with open(data_dir + '/' + train_corpora_dir + '/' + dirname + '/' + 'truth.json') as truth_data:

            truth = yaml.load(truth_data)
            for problem in truth['problems']:
                for representationSpace in representationSpaces:
                    if representationSpace.name == problem['name'] \
                            and representationSpace.genre == problem['genre'] \
                            and representationSpace.language == problem['language']:
                        if problem['answer'] == 'Y':
                            representationSpace.set_label(True)
                        elif problem['answer'] == 'N':
                            representationSpace.set_label(False)
                        else:
                            raise Exception('Answer isn\'t Y or N')


def load_text_corpus(representationSpaces):
    representationSpacesWithCorpus = []
    for representationSpace in representationSpaces:
        for dirname in os.listdir(data_dir + '/' + train_corpora_dir):
            if not os.path.isdir(data_dir + '/' + train_corpora_dir + '/' + dirname):
                continue
            if dirname == train_corpora_dir or dirname == '.DS_Store':
                continue
            with open(data_dir + '/' + train_corpora_dir + '/' + dirname + '/' + 'contents.json') as json_data:
                contents = yaml.load(json_data)
                print(contents)
                for problem in contents['problems']:
                    unknown = open(
                        data_dir + '/' + train_corpora_dir + '/' + dirname + '/' + problem + '/' + 'unknown.txt',
                        'r').read()
                    corpus = []
                    # TODO: should also be replaced with os.listdir
                    for _, _, files in os.walk(
                                                                                    data_dir + '/' + train_corpora_dir + '/' + dirname + '/' + problem + '/'):
                        for file in files:
                            if file.endswith(".txt") and not file == 'unknown.txt':
                                corpus.append(open(
                                    data_dir + '/' + train_corpora_dir + '/' + dirname + '/' + problem + '/' + file,
                                    'r').read())
                    representationSpaceCopy = copy.deepcopy(representationSpace)
                    representationSpaceCopy.set_language(contents['language'])
                    representationSpaceCopy.set_genre(contents['genre'])
                    representationSpaceCopy.set_name(problem)
                    representationSpaceCopy.set_unknown_text(unknown)
                    representationSpaceCopy.set_corpus(corpus)

                    representationSpacesWithCorpus.append(representationSpaceCopy)
                    corpus = []
    return representationSpacesWithCorpus


def build_representation_space():
    representationSpaces = []
    # create TfidfRepresentationSpace objects for each combination from the paper
    for analyzer in ['char', 'char_wb']:
        for ngram_range in [(3, 3), (8, 8)]:
            representationSpaces.append(TfidfRepresentationSpace(analyzer=analyzer, ngram_range=ngram_range))
    for analyzer in 'word':
        for ngram_range in [(2, 2)]:
            representationSpaces.append(TfidfRepresentationSpace(analyzer=analyzer, ngram_range=ngram_range))
        representationSpaces.append(
            TfidfRepresentationSpace(analyzer=analyzer, ngram_range=(1, 1), stopwords='english'))
        representationSpaces.append(TfidfRepresentationSpace(analyzer=analyzer, ngram_range=(1, 1), max_df=0.7))
    # TODO: Set correct similarity method
    return representationSpaces


def build_features(representationSpaces):
    return None


def main():
    may_download_training(train_corpora_url, data_dir, train_corpora_dir)
    may_unzip_corpus(data_dir + '/' + train_corpora_dir, data_dir, train_corpora_dir)

    representationSpaces = build_representation_space()
    representationSpaces = load_text_corpus(representationSpaces)
    set_labels(representationSpaces)
    build_features(representationSpaces)


if __name__ == '__main__':
    main()
