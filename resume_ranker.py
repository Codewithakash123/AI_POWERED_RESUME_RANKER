import io
import spacy
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Use SpaCy for text preprocessing
nlp = spacy.blank("en")


def preprocess_text(text):
    """
    Preprocess text using SpaCy.
    Converts text to lowercase and keeps useful alphabetic tokens.
    """
    doc = nlp(text.lower())

    words = []

    for token in doc:
        if token.is_alpha and not token.is_stop:
            words.append(token.text)

    return " ".join(words)


def extract_pdf_text(file_bytes):
    """
    Extract text from a PDF file.
    """
    reader = PdfReader(io.BytesIO(file_bytes))

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + " "

    return text


def rank_resumes(job_description, uploaded_resumes):
    """
    Rank uploaded resumes according to their similarity
    with the given job description.

    uploaded_resumes:
        List of tuples:
        (filename, file_bytes)
    """

    # Preprocess job description
    processed_job = preprocess_text(job_description)

    resume_names = []
    resume_texts = []

    # Extract and preprocess every uploaded PDF
    for filename, file_bytes in uploaded_resumes:

        try:
            text = extract_pdf_text(file_bytes)

            processed_text = preprocess_text(text)

            resume_names.append(filename)
            resume_texts.append(processed_text)

        except Exception as e:
            print(f"Error reading {filename}: {e}")

    # Make sure there is something to rank
    if not resume_texts:
        return []

    # Combine job description and resumes
    documents = [processed_job] + resume_texts

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer()

    tfidf_matrix = vectorizer.fit_transform(documents)

    # First document is the job description
    job_vector = tfidf_matrix[0:1]

    # Remaining documents are resumes
    resume_vectors = tfidf_matrix[1:]

    # Calculate cosine similarity
    similarities = cosine_similarity(
        job_vector,
        resume_vectors
    )[0]

    results = []

    for filename, similarity in zip(resume_names, similarities):

        score = round(float(similarity) * 100, 2)

        if score >= 90:
            status = "Best"
        elif score >= 75:
            status = "Excellent"
        elif score >= 50:
            status = "Good"
        else:
            status = "Average"

        results.append({
            "name": filename,
            "score": score,
            "status": status
        })

    # Highest score first
    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results