import logging
import PyPDF2
import nltk
nltk.download('stopwords')
from nltk import pos_tag, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
from io import StringIO
from .models import StudentUsers
logger = logging.getLogger(__name__)
import warnings
import os
from .models import RepositoryFiles

# upload enrolled students csv file
def csv_enrolled_students(file):
    df = pd.read_excel(file)
    rows_to_keep = []
    seen_student_ids = set()
    for index, row in df.iterrows():
        student_id = row['Student ID']
        if student_id not in seen_student_ids:
            # This is the first time we're seeing this student ID, so keep this row
            rows_to_keep.append(row)
            seen_student_ids.add(student_id)
    # Now we have a list of rows that we want to keep, so we can create the StudentUsers objects
    for row in rows_to_keep:
        data = StudentUsers(id=row['sn'], Student_Id=row['Student ID'], Student_Name=row['Student Name'], Email=row['Email'], Contact_Number=row['Contact No.'],
                            Course=row['Course'], SUBJECT_CODE=row['SUBJ_CODE'], SUBJECT_DESCRIPTION=row['SUBJ_DESC'], YR_SEC=row['YR_SEC'], SEM=row['SEM'], SY=row['SY'])
        data.save()


def preprocess(data):
    # Convert to lower case
    data = np.char.lower(data)

    # Remove punctuation
    symbols = "!\"#$%&()*+-./:;<=>?@[\]^_`{|}~\n"
    for i in range(len(symbols)):
        data = np.char.replace(data, symbols[i], ' ')
        data = np.char.replace(data, "  ", " ")
        data = np.char.replace(data, ',', '')

    # Remove stop words
    stop_words = stopwords.words('english')
    words = word_tokenize(str(data))
    new_text = ""
    for w in words:
        if w not in stop_words and len(w) > 1:
            new_text = new_text + " " + w
    data = new_text

    # Perform stemming
    stemmer = PorterStemmer()
    words = word_tokenize(str(data))
    new_text = ""
    for w in words:
        new_text = new_text + " " + stemmer.stem(w)
    data = new_text

    # Perform lemmatization
    lemmatizer = WordNetLemmatizer()
    words = word_tokenize(str(data))
    new_text = ""
    for w in words:
        new_text = new_text + " " + lemmatizer.lemmatize(w)
    data = new_text

    return data

def extract_pdf_text(pdf_file, repository_file):
    # open the PDF file
    pdf = PyPDF2.PdfReader(pdf_file)
    
    # extract the text from each page and save it in a list
    text_list = [pdf.pages[page].extract_text() for page in range(len(pdf.pages))]

    # join all the texts from the list and save it as a single string
    text = "\n".join(text_list)
    
    path = 'media/ExtractedFiles'
    if not os.path.exists(path):
        os.makedirs(path)
    text_file_name = pdf_file.name.replace('.pdf', '.txt')
    text_file = os.path.join(path, text_file_name)
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text)
    
    # Save the file path to the database
    repository_file.text_file = text_file
    repository_file.save()


#SUPER WORKING
# def vectorize(query_matrix, vectorizer, k):
#     matrices = []
#     path = 'media/ExtractedFiles'
#     for file in os.listdir(path):
#         with open(os.path.join(path, file), 'r',encoding='utf-8', errors='ignore') as f:
#             text = f.read()
#             text = preprocess(text)
#             doc_matrix = vectorizer.transform([text])
#             similarity = cosine_similarity(query_matrix, doc_matrix)[0][0]
#             similarity = round(similarity, 2)
#             similarity = similarity*100
#             # Get the base name and extension of the file
#             base_name, ext = os.path.splitext(file)
#             matrices.append({'title': base_name, 'matrix': doc_matrix, 'similarity': similarity})
#     # Sort the list of documents by similarity in descending order
#     matrices.sort(key=lambda x: x['similarity'], reverse=True)
#     # Select the first k documents
#     nearest_neighbors = matrices[:k]
#     return nearest_neighbors

def vectorize(query_matrix, vectorizer, k):
    matrices = []
    for file_info in RepositoryFiles.objects.all().values('text_file', 'title','proponents','adviser','school_year'):
        file_path = file_info['text_file']
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            text = preprocess(text)
            doc_matrix = vectorizer.transform([text])
            similarity = cosine_similarity(query_matrix, doc_matrix)[0][0]
            similarity = round(similarity, 2)
            similarity = similarity*100
            matrices.append({'title': file_info['title'], 'proponents': file_info['proponents'], 'adviser': file_info['adviser'], 'school_year': file_info['school_year'], 'matrix': doc_matrix, 'similarity': similarity})
    # Sort the list of documents by similarity in descending order
    matrices.sort(key=lambda x: x['similarity'], reverse=True)
    # Select the first k documents
    nearest_neighbors = matrices[:k]
    return nearest_neighbors

        
def student_pdf_text(pdf_file):
    vectorizer = TfidfVectorizer()
    
    all_docs = []
    path = 'media\ExtractedFiles'
    for file in os.listdir(path):
        with open(os.path.join(path, file), 'r',encoding='utf-8', errors='ignore') as f:
            all_docs.append(f.read())
    all_docs = [preprocess(text) for text in all_docs]
    vectorizer.fit(all_docs)
    
    # open the PDF file
    pdf = PyPDF2.PdfReader(pdf_file)

    # extract the text from each page and save it in a list
    text_list = [pdf.pages[page].extract_text() for page in range(len(pdf.pages))]

    # join all the texts from the list and save it as a single string
    text = "\n".join(text_list)
 
    # preprocess the text using NLTK
    query_text = preprocess(text)
    query_matrix = vectorizer.transform([query_text])
    return query_matrix


def pdf_to_text(pdf_file):
    # open the PDF file
    pdf = PyPDF2.PdfReader(pdf_file)
    
    # extract the text from each page and save it in a list
    text_list = [pdf.pages[page].extract_text() for page in range(len(pdf.pages))]

    # join all the texts from the list and save it as a single string
    text = "\n".join(text_list)
    
    return text

def compare_documents(text1, text2):
    
    
   # Create the TF-IDF representation
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform([text1, text2])
    
    # Compute the cosine similarity
    result = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix)
    
    # return the similarity score in percentage form
    return result[0][1]*100
    
    