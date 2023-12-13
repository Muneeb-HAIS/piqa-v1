import pandas as pd
from transformers import pipeline, GPT2Tokenizer

# Load the pre-trained GPT-Neo model
tokenizer = GPT2Tokenizer.from_pretrained('EleutherAI/gpt-neo-2.7B')
text_generator = pipeline('text-generation', model='EleutherAI/gpt-neo-2.7B', tokenizer=tokenizer)

# # Load the data from an Excel file
# data = pd.read_excel('C:\\Users\\acer1\\Downloads\\Company Structure Dataset.xlsx')

# # Preprocess the data
# data = data.dropna()  # Remove missing values
# data = data.drop_duplicates()  # Remove duplicates

# # Convert numerical columns to strings
# df = pd.DataFrame(data)

# # Convert numerical columns to strings
# numerical_columns = ['Phone Number', 'Info Barrier Level']  # Add other numerical columns as needed
# df[numerical_columns] = df[numerical_columns].astype(str)

# # Extract features
# features = (
#     df['Name'] + ' ' + df['Role'] + ' ' + df['Business Area'] +
#     ' ' + df['Direct Line Manager'] + ' ' + df['Business Function'] +
#     ' ' + df['Team'] + ' ' + df['Phone Number'] + ' ' + df['Email'] +
#     ' ' + df['Info Barrier Level'].astype(str) + ' ' + df['BA'] + ' ' + df['Sub BA']
# )

# # Generate responses based on your custom data and prompts
# response = text_generator(features.tolist(), max_length=100, num_return_sequences=1)

# # Iterate through the list of responses and print 'generated_text'
# for r in response:
#     print(r[0]['generated_text'])



# Ask the user for a prompt
user_prompt = input("Enter your prompt: ")

# Generate a response based on the user's prompt
response = text_generator(user_prompt, max_length=100, num_return_sequences=1)

# Print the generated response
print(response[0]['generated_text'])