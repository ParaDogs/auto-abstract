import sys
import collections
import functools
import pymorphy2

args_len = len(sys.argv)
if (args_len == 1):
    print('autoabstract <text file name> <output file name>')
    exit()
elif (args_len == 2): OUT_FILE_NAME = 'autoabstract.txt'
else:
    OUT_FILE_NAME = sys.argv[2]
 
NON_INFORMATIVE_WORDS_FILE_NAME = "trash-words.txt"
TEXT_FILE_NAME = sys.argv[1]
PERCENT = 20
END_SENTENCE_MARKS = ['.', '?', '!']
PUNCTUATION_MARKS = [',', ';', '"', ':', '—', '\n', '«', '»'] + END_SENTENCE_MARKS
MORPH = pymorphy2.MorphAnalyzer()

class Word:
    def __init__(self, string):
        s = string.lower()
        for mark in PUNCTUATION_MARKS: s = s.replace(mark, '')
        self.data = MORPH.parse(s)[0].normal_form # TODO слово нужно лемматизировать
    
    # получить список синонимов слова
    def get_synonyms(self):
        return [Word(self.data)] #TODO нужна сторонняя библиотека

    # получить вес слова в тексте
    def get_weight(self, text):
        return text.word_counter[self.data] / text.size_w if self.data not in text.get_trash_words() else 0

    def __str__(self): return self.data

class Sentence:
    def __init__(self, string):
        self.data = string
        chains = list(map(lambda w: Word(w), self.tokenize())) # преобразовать цепочки в слова
        self.words = [w for w in chains if w.data] # удалить пустые слова
        self.size = len(self.words)

    # разбить предложение на цепочки
    def tokenize(self):
        return self.data.split(' ')

    # получить вес предложения в тексте
    def get_weight(self, text):
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
    def tokenize(self):
        return self.data.split('.') #TODO учесть сокращения

    # получить неинформативные слова языка
    def get_trash_words(self):
        return open(NON_INFORMATIVE_WORDS_FILE_NAME, 'r').read().split(' ')

    # получить автореферат текста как "ужатый" до некоторого процента текст 
    def summarize(self, percent):
        sw = [[s, s.get_weight(self)] for s in self.sentences] # sentences with weigth = sw
        sw = sorted(sw, key=lambda s: s[1], reverse=True) # отсортировать предложения по их весу по убыванию
        max_sentences = self.size_s * percent // 100 # максимальное количество предложений в реферате
        min_weight = sw[max_sentences][1] # минимальный допустимый вес предложения в реферате
        abstract = ""
        for s in self.sentences: abstract += s.data + '.' if s.get_weight(self) >= min_weight else ''
        return abstract

    def __str__(self): return self.data

text = Text(open(TEXT_FILE_NAME, 'r').read())
out = open(OUT_FILE_NAME, 'w')
out.write(text.summarize(PERCENT))
out.close()
