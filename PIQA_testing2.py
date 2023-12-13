import pandas as pd
from transformers import GPT2Tokenizer, GPT2LMHeadModel, GPT2Config
from transformers import TextDataset, DataCollatorForLanguageModeling
from transformers import Trainer, TrainingArguments, pipeline

data = pd.read_excel('C:\\Users\\acer1\\Downloads\\Company Structure Dataset.xlsx')

# Preprocess the data
data = data.dropna()  # Remove missing values
data = data.drop_duplicates()  # Remove duplicates

# Convert numerical columns to strings
df = pd.DataFrame(data)

# Convert numerical columns to strings
numerical_columns = ['Phone Number', 'Info Barrier Level']  # Add other numerical columns as needed
df[numerical_columns] = df[numerical_columns].astype(str)

# Extract features
features = (
    df['Name'] + ' ' + df['Role'] + ' ' + df['Business Area'] +
    ' ' + df['Direct Line Manager'] + ' ' + df['Business Function'] +
    ' ' + df['Team'] + ' ' + df['Phone Number'] + ' ' + df['Email'] +
    ' ' + df['Info Barrier Level'].astype(str) + ' ' + df['BA'] + ' ' + df['Sub BA']
)

# Save the preprocessed data to a text file for fine-tuning
features.to_csv('fine_tuning_data.txt', index=False, header=False)
# Fine-tune the GPT-2 model
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2')

# Load the preprocessed data
train_file_path = 'fine_tuning_data.txt'
train_dataset = TextDataset(
    tokenizer=tokenizer,
    file_path=train_file_path,
    block_size=32  # Adjust the block_size based on your dataset
)

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False  # Set to True if you have a masked language modeling task
)

training_args = TrainingArguments(
    output_dir="./gpt2-fine-tuned",
    overwrite_output_dir=True,
    num_train_epochs=50,  # Adjust as needed
    per_device_train_batch_size=6,
    save_steps=500,
    save_total_limit=20,
    logging_dir="./logs",  # Specify the directory for TensorBoard logs
    logging_steps=500,
   evaluation_strategy="steps",  # Evaluate every eval_steps steps
   eval_steps=500,  # Adjust as needed
   load_best_model_at_end=True,
   #learning_rate=1e-5,  # Adjust learning rate
  #weight_decay=0.01,  # Adjust weight decay
)


trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=train_dataset,
    tokenizer=tokenizer,
    
)

trainer.train()

# Save the fine-tuned model
model.save_pretrained("./gpt2-fine-tuned")
tokenizer.save_pretrained("./gpt2-fine-tuned")

# Save the model after training
trainer.save_model("./gpt2-fine-tuned-final")

# Generate responses based on prompts
text_generator = pipeline('text-generation', model=model, tokenizer=tokenizer)
prompts = [
    "Who is the Head of Risk Management?",
    "Tell me about the Marketing Team.",
    "What is Emily Chen's role?",
    "Give me information about the Compliance Officer.",
    "I need details about Corporate Banking.",
    "Who is the Chief Information Officer?"
]

for prompt in prompts:
    response = text_generator(prompt, max_length=100, num_return_sequences=1)
    print(f"Prompt: {prompt}")
    print(f"Response: {response[0]['generated_text']}\n")