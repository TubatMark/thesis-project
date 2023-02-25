import logging
import PyPDF2
from fuzzywuzzy import fuzz
from nltk import pos_tag, word_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
import numpy as np
import pandas as pd
import io
from .models import StudentUsers
logger = logging.getLogger(__name__)
import warnings
import os
from .models import RepositoryFiles, SimilarityThreshold
import codecs
import dateutil.parser as dparser
import string
from django.conf import settings
import nltk
nltk.download('punkt')


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
        data = StudentUsers(Student_Id=row['Student ID'], Student_Name=row['Student Name'], Email=row['Email'], Contact_Number=row['Contact No.'],
                            Course=row['Course'], SUBJECT_CODE=row['SUBJ_CODE'], SUBJECT_DESCRIPTION=row['SUBJ_DESC'], YR_SEC=row['YR_SEC'], SEM=row['SEM'], SY=row['SY'])
        data.save()


def preprocess(data):
    # open and read stopwords.txt
    with codecs.open('stopwords/stopwords.txt', 'r', encoding='utf-8', errors='ignore') as f:
        stopwords = f.read().splitlines()
        
    # Remove stop words
    words = nltk.tokenize.word_tokenize(data)
    
    # Convert words to lowercase
    lower_words = [word.lower() for word in words]
    
    filtered_words = [word for word in lower_words if word not in stopwords and len(word) > 2 and not word.isdigit() and not all(c in string.punctuation for c in word) and not is_date(word)]
    return " ".join(filtered_words)

def is_date(string):
    try:
        dparser.parse(string, fuzzy=True)
        return True
    except ValueError:
        return False

def extract_pdf_text(pdf_file, repository_file):
    # read the contents of the uploaded file
    pdf_content = pdf_file.read()

    # create a PyPDF2 PdfReader object
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))

    # extract the text from each page and save it in a list
    text_list = [pdf_reader.pages[page].extract_text() for page in range(len(pdf_reader.pages))]

    # join all the texts from the list and save it as a single string
    text = "\n".join(text_list)

    # construct the file path using MEDIA_ROOT and MEDIA_URL
    file_path = os.path.join(settings.MEDIA_ROOT, "ExtractedFiles")
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    text_file_name = pdf_file.name.replace('.pdf', '.txt')
    text_file = os.path.join(file_path, text_file_name)
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text)

    # Save the file path to the database
    repository_file.text_file = text_file
    repository_file.save()


# def extract_pdf_text(pdf_file, repository_file):
#     # open the PDF file
#     pdf = PyPDF2.PdfReader(pdf_file)
    
#     # extract the text from each page and save it in a list
#     text_list = [pdf.pages[page].extract_text() for page in range(len(pdf.pages))]

#     # join all the texts from the list and save it as a single string
#     text = "\n".join(text_list)
    
#     # construct the file path using MEDIA_ROOT and MEDIA_URL
#     file_path = os.path.join(settings.MEDIA_ROOT, "ExtractedFiles")
#     if not os.path.exists(file_path):
#         os.makedirs(file_path)
#     text_file_name = pdf_file.name.replace('.pdf', '.txt')
#     text_file = os.path.join(file_path, text_file_name)
#     with open(text_file, 'w', encoding='utf-8') as f:
#         f.write(text)
    
#     # Save the file path to the database
#     repository_file.text_file = text_file
#     repository_file.save()


def vectorize(query_matrix, vectorizer, k, student_title, user_id):
    threshold = 0
    last_threshold = SimilarityThreshold.objects.all().last() #admin set threshold
    if last_threshold:
        threshold = last_threshold.threshold
    matrices = []
    for file_info in RepositoryFiles.objects.exclude(user=user_id).values('text_file', 'title','proponents','adviser','school_year', 'user'):
        file_path = file_info['text_file']
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            text = preprocess(text)
            doc_matrix = vectorizer.transform([text])
            similarity = cosine_similarity(query_matrix, doc_matrix)[0][0]
            similarity = round(similarity, 2)
            content_similarity = similarity*100
            
            #preprocess title
            preprocess_student_title = preprocess(student_title)
            preprocess_corpus_title = preprocess(file_info['title'])
            
            # calculate the similarity between the titles
            title_similarity = fuzz.token_set_ratio(preprocess_corpus_title, preprocess_student_title)
            
            #working
            #title_similarity = fuzz.token_set_ratio(file_info['title'], student_title)

            matrices.append({
                'title': file_info['title'], 
                'title_similarity': title_similarity, 
                'proponents': file_info['proponents'], 
                'adviser': file_info['adviser'], 
                'school_year': file_info['school_year'], 
                'matrix': doc_matrix, 
                'content_similarity': content_similarity
            })
    # Sort the list of documents by similarity in descending order
    matrices.sort(key=lambda x: x['content_similarity'], reverse=True)
    # Select the first k documents
    nearest_neighbors = matrices[:k]
    
    # Add a flag to indicate if the similarity is below the threshold
    for neighbor in nearest_neighbors:
        if neighbor['content_similarity'] < threshold:
            neighbor['below_threshold'] = True
        else:
            neighbor['below_threshold'] = False
    return nearest_neighbors
    

        
def student_pdf_text(pdf_file, vectorizer):
    # open the PDF file
    pdf = PyPDF2.PdfReader(pdf_file)

    # extract the text from each page and save it in a list
    text_list = [pdf.pages[page].extract_text()
                 for page in range(len(pdf.pages))]

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
    
    