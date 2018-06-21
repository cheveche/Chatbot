import re
import sqlite3
import random
from collections import Counter
from string import punctuation
from math import sqrt

#---SQL setup--------------------------------------------------
connection = sqlite3.connect('databt.sqlite')
cursor = connection.cursor()



table_creation_list = [
    'CREATE TABLE tbl_words(word TEXT UNIQUE)',
    'CREATE TABLE tbl_sentences(sentence TEXT UNIQUE, used INT NOT NULL DEFAULT 0)',
    'CREATE TABLE tbl_associations (word_id INT NOT NULL,  sentence_id INT NOT NULL, weight REAL NOT NULL)',    
]

for init_table in table_creation_list:
    try:
        cursor.execute(init_table)
    except:
        pass


#create short term memory table of the conversation
cursor.execute('CREATE TEMPORARY TABLE tbl_shortmem(sentence_id INT, sentence TEXT)')




#---SCRIPTING RESSOURCES -----------------------------------------
GREETING_KEYWORDS = ("hello", "hi", "greetings", "hey")
COMMAND_KEYWORDS = ("analysis","execute")
FILTER = ("ass","fuck","suck","dumb")

AFTER_GREETINGS = ("What can I do for you?","is there anything I can help you with?", "are you another person typing ?")  
ALREADY_ASKED = ("you are repeating yourself", "you said that already", "why do you say that again ?", "again?") 
EXCEPTION = ("... can you say it differently", "... can you elaborate please?", ",elaborate please",",but I am not quite sure I get it...", "...")



#---Module Definition------------------------------------------
def get_id(entityName, text):
    """ Request ID or create it for  """
    tableName = 'tbl_'+ entityName + 's'
    columnName = entityName
    cursor.execute('SELECT rowid FROM ' + tableName + ' WHERE ' + columnName + ' = ?', (text,))
    row = cursor.fetchone()

    if row:
        return row[0]
    else:
        cursor.execute('INSERT INTO ' + tableName + ' (' + columnName + ') VALUES (?)', (text,))
        return cursor.lastrowid


def cut_words(text):
    """cut the words from a the input sentence"""
    wordsRegexpString = '(?:\w+|[' + re.escape(punctuation) + ']+)'
    wordsRegexp = re.compile(wordsRegexpString)
    wordsList = wordsRegexp.findall(text.lower())
    return Counter(wordsList).items()


def check_script(text):
    if text in GREETING_KEYWORDS:
        return 1
    elif text in FILTER:
        return 6
    elif text in COMMAND_KEYWORDS:
       return 8      
    else:
        return 0 


def check_shortmem(text):
    tableName = 'tbl_shortmem'
    columnName = 'sentence'
    cursor.execute('SELECT rowid FROM ' + tableName + ' WHERE ' + columnName + ' = ?', (text,))
    row = cursor.fetchone()

    if row:
        return 1
    else:
        cursor.execute('INSERT INTO ' + tableName + ' (' + columnName + ') VALUES (?)', (text,))
        return 0




#---BOT-------------------------------------------------------
count = 0
B = random.choice(GREETING_KEYWORDS).capitalize() + ", I am Bot, what can I do for you ?"


while True:
#__display___

    #display Bot message | break on empty answer
    print('B:' + B)
    H = input('Y:').strip()
    if H=='':
        break


    #increase interaction count
    count = count+1

    #check script vs improvisation
    words = cut_words(H)

    for word, n in words:
        check = check_script(word)
        if check != 0:
            if check == 1 and count > 3:
                break
            elif check == 1 and count < 3:
                check = 0
            else:
                break

#__scripting process___
    if check == 1:
        B = "we greets already," + random.choice(AFTER_GREETINGS)
    elif check == 6:
        B = "please do not use this kind of word ..."
    elif check == 8:
        B = "not available ... yet"

#__improvisation process__
    else :

    #associate B and H
        words = cut_words(B)
        words_length = sum([n * len(word) for word, n in words])
        sentence_id = get_id('sentence', H)
        
        for word, n in words:
            word_id = get_id('word', word)
            weight = sqrt(n / float(words_length))
            cursor.execute('INSERT INTO tbl_associations VALUES (?, ?, ?)', (word_id, sentence_id, weight))
            connection.commit()

    #set the temp table with answer
        cursor.execute('CREATE TEMPORARY TABLE tbl_results(sentence_id INT, sentence TEXT, weight REAL)')
        words = cut_words(H)
        words_length = sum([n * len(word) for word, n in words])

        for word, n in words:
            weight = sqrt(n / float(words_length))

        cursor.execute('INSERT INTO tbl_results SELECT tbl_associations.sentence_id, tbl_sentences.sentence, ? *tbl_associations.weight/(4+tbl_sentences.used) FROM tbl_words INNER JOIN tbl_associations ON tbl_associations.word_id=tbl_words.rowid INNER JOIN tbl_sentences ON tbl_sentences.rowid=tbl_associations.sentence_id WHERE tbl_words.word=?', (weight, word,))


    #Answer
        shortmem = check_shortmem (H)

        if shortmem == 1:
            B = random.choice(ALREADY_ASKED)

        else:
            cursor.execute('SELECT sentence_id, sentence, SUM(weight) AS sum_weight FROM tbl_results GROUP BY sentence_id ORDER BY sum_weight DESC LIMIT 5')
            row = cursor.fetchone()

            if row is None:
                cursor.execute('SELECT rowid, sentence FROM tbl_sentences WHERE used = (SELECT MIN(used) FROM tbl_sentences) ORDER BY RANDOM() LIMIT 5')
                row = cursor.fetchone()
                
            B = row[1]
            r = 1

            while True:
                try:
                    words = cut_words(B)
                    for word, n in words:
                        check = check_script(words)
                except:
                    B = "hmmm" + random.choice(EXCEPTION)
                    break
                    

                memory = check_shortmem (B)

                if check == 0 and memory == 0:
                    break
                else:
                    r +=1
                    if r<5:
                        try:
                            B = row[r]
                        except:
                            B = "interesting" + random.choice(EXCEPTION)
                            break
                    else:
                        B = "that look like nothing to me"
                        break
                        

            cursor.execute('DROP TABLE tbl_results')
                
    # Increase use indicator 
        cursor.execute('UPDATE tbl_sentences SET used=used+1 WHERE rowid=?', (row[0],))
        








 
                

                
                    
                


