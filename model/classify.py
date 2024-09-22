from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

EMAIL_PATH = ".\\finetuned_lm\\finetuned_minilm"
QUESTION_PATH = ".\\finetuned_lm\\finetuned_minilm_qc"

#Loading the tokenizer
tokenizer_email = AutoTokenizer.from_pretrained(EMAIL_PATH)
tokenizer_ques = AutoTokenizer.from_pretrained(QUESTION_PATH)

#creating the model
email_model = AutoModelForSequenceClassification.from_pretrained(EMAIL_PATH)
question_model = AutoModelForSequenceClassification.from_pretrained(QUESTION_PATH)

#creating the tokenize function

def classify_text(model, tokenizer, text):
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.argmax(outputs.logits, dim=-1)
    return predictions.item()


#mapping the predictions to categories
label_mapping = {
    0: "Internship/Placement Email,college",
    1: "Internship/Placement Email,external",
    2: "Hackathon Email,college",
    3: "Hackathon Email,external",
    4: "Education Email,college",
    5: "Education Email,external",
    6: "Event Email,college",
    7: "Event Email,external",
    8: "Course Advertisement,college",
    9: "Course Advertisement,external",
    10: "Other Emails,college",
    11: "Other Emails,external"
}

#Email prediction and categorize

email_text = "26-07-2023 14:30 Rajesh Patel rajesh.patel@vit.ac.in Internship Opportunity at Google We are excited to announce that we have partnered with Google to offer a 3-month internship program for students. The program is designed to provide hands-on experience in software development and will include a stipend of $5000. If you are interested, please reply to this email by August 1st."
email_prediction = classify_text(email_model, tokenizer_email, email_text)
print(f"Predicted Category: {label_mapping[email_prediction]}")
#Just printing the output for now, will connect with sql later


#
