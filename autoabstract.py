import sys
import collections
import functools
import pymorphy2

args_len = len(sys.argv)
if (args_len == 1):
    print('autoabstract.py <text file name> <compression (default: 20)> <output file name (default: autoabstract.txt)>')
    exit()
if (args_len >= 2):
    TEXT_FILE_NAME = sys.argv[1]
    COMPRESSION_PERCENT = 20
    OUT_FILE_NAME = 'autoabstract.txt'
if (args_len >= 3):
    COMPRESSION_PERCENT = int(sys.argv[2])
    if not 1 <= COMPRESSION_PERCENT <= 99:
        print('wrong compression percent - must be from 1 to 99')
        exit()
if (args_len == 4):
    OUT_FILE_NAME = sys.argv[3]   
 
NON_INFORMATIVE_WORDS_FILE_NAME = "trash-words.txt"
END_SENTENCE_MARKS = ['...', '.', '?', '!']
PUNCTUATION_MARKS = [',', ';', '"', ':', '—', '\n', '«', '»'] + END_SENTENCE_MARKS
MORPH_ANALYZER = pymorphy2.MorphAnalyzer()

class Word:
    def __init__(self, string):
        s = string.lower()
        for mark in PUNCTUATION_MARKS: s = s.replace(mark, '')
        self.data = MORPH_ANALYZER.parse(s)[0].normal_form

    # получить вес слова в тексте
    def get_weight(self, text) -> float:
        return text.word_counter[self.data] / text.size_w if self.data not in text.get_trash_words() else 0

    def __str__(self): return self.data

class Sentence:
    def __init__(self, string):
        self.data = string
        tokens = self.tokenize()
        chains = list(map(lambda w: Word(w), tokens)) # преобразовать цепочки в слова
        self.words = [w for w in chains if w.data] # удалить пустые слова
        self.size = len(self.words)

    # разбить предложение на цепочки
    def tokenize(self) -> list:
        return self.data.split(' ')

    # получить вес предложения в тексте
    def get_weight(self, text) -> float:
        return functools.reduce(lambda a, word: a + word.get_weight(text), self.words, 0)

    def __str__(self): return self.data

class Text:
    def __init__(self, string):
        self.data = string
        presentences = list(map(lambda s: Sentence(s), self.tokenize()))
        self.sentences = [s for s in presentences if s.data] # удалить пустые предложения
        words_list = list(functools.reduce(lambda a, s: a + [s.words[i].data for i in range(s.size)], self.sentences, []))
        self.word_counter = collections.Counter(words_list)
        self.size_w = len(words_list)
        self.size_s = len(self.sentences)
        
    # разбить текст на предложения
    def tokenize(self) -> list:
        text = ""
        TEMP_MARK = '$$$'
        for mark in END_SENTENCE_MARKS: text = self.data.replace(mark, mark+TEMP_MARK)
        return text.split(TEMP_MARK)

    # получить неинформативные слова языка
    def get_trash_words(self) -> list:
        return open(NON_INFORMATIVE_WORDS_FILE_NAME, 'r').read().split(' ')

    # получить автореферат текста как "ужатый" до некоторого процента текст 
    def summarize(self, COMPRESSION_PERCENT) -> str:
        weighted_sentences = [{'sentence': s, 'weight': s.get_weight(self)} for s in self.sentences]
        weighted_sentences = sorted(weighted_sentences, key=lambda s: s['weight'], reverse=True) # отсортировать предложения по их весу по убыванию
        max_sentences = self.size_s * COMPRESSION_PERCENT // 100 # максимальное количество предложений в реферате
        min_weight = weighted_sentences[max_sentences]['weight'] # минимальный допустимый вес предложения в реферате
        abstract = ""
        for s in self.sentences:
            if s.get_weight(self) >= min_weight:
                abstract += s.data + '.'
        return abstract

    def __str__(self): return self.data

text = Text(open(TEXT_FILE_NAME, 'r').read())
out = open(OUT_FILE_NAME, 'w')
out.write(text.summarize(COMPRESSION_PERCENT))
out.close()