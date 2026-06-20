from google import genai
from google.genai import types
import os, json, time
from PIL import Image
import dotenv

dotenv.load_dotenv()
key = os.getenv("API_KEY")

exam_dir = os.listdir("./output")

cnt = 0
all_image_paths = {}
for dir in exam_dir:
    with open(f"./output/{dir}/{dir}.json", "r+") as f:
        py_dict = json.load(f)
        
    for question in py_dict["questions"]:
        all_image_paths[f"q_{cnt}"] = question["image_path"]
        cnt += 1




# Get output path from img path
# split = all_image_paths[1].split('/')
# print(f"{split[0]}/{split[1]}/{split[2]}/{split[2]}.json")

# Edit a file to append new fields to question
# py_dict["questions"][0]["difficulty"] = "easy"
# f.seek(0)
# f.truncate(0)

# json_string = json.dumps(py_dict)
# f.write(json_string)




client = genai.Client(api_key=key)

# System instructions and formatting rules
instructions = [
    "You are classifying edexcel math A-level exam questions.",
    """Return only a json that is in this format. 
        {"q_1": {
                "topic": "the main topic name",
                "subtopic": "subtopics of the main topic",
                "difficulty": "easy" or "medium" or "hard"
            }
        }
    """,
    """
    # Classify difficulty based on marks and complexity:
    # - easy: 1-3 marks, straightforward application
    # - medium: 4-6 marks, requires multiple steps
    # - hard: 7+ marks, requires deep understanding
    """
]

batch_size = 30
cnt = 0
content_batch = []
current_batch = list(instructions) # Start each batch with instructions

# --- Batch Preparation ---
for img_id, path in all_image_paths.items():
    # Open image using PIL
    img = Image.open(path)
    
    # Append image and ID directly to the list
    # The new SDK automatically converts PIL.Image objects
    current_batch.append(img) 
    current_batch.append(f"Question ID: {img_id}")
    
    cnt += 1

    if cnt % batch_size == 0:
        content_batch.append(current_batch)
        current_batch = list(instructions) # Reset for next batch

# Append any remaining items
if len(current_batch) > len(instructions):
    content_batch.append(current_batch)

# --- Processing Batches ---
batch_number = 0
for batch in content_batch:
    # Rate limiting: sleep every 5 batches (except the first)
    if batch_number % 5 == 0 and batch_number != 0:
        time.sleep(120)

    # Generate content
    # No need to manually wrap images in types.Part
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=batch, 
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        )
    )
    
    batch_number += 1

    try:
        py_dict = json.loads(response.text)
    except json.JSONDecodeError:
        print(f"Error decoding JSON in batch {batch_number}")
        continue

    # --- Update Local JSON Files ---
    for id, data in py_dict.items():
        if id not in all_image_paths:
            continue
            
        split = all_image_paths[id].split('/')
        if len(split) < 5: 
            continue
            
        # Extract question number from path
        try:
            question_number = int(split[4].split("_")[3].split(".")[0].replace("q", ""))
        except (IndexError, ValueError):
            print(f"Could not parse question number for {id}")
            continue

        output_path = f"{split[0]}/{split[1]}/{split[2]}/{split[2]}.json"
        
        if os.path.exists(output_path):
            with open(output_path, "r+") as f:
                try:
                    file_data = json.load(f)
                    # Ensure index is valid
                    if 0 <= question_number - 1 < len(file_data.get("questions", [])):
                        file_data["questions"][question_number-1]["difficulty"] = data.get("difficulty")
                        file_data["questions"][question_number-1]["topic"] = data.get("topic")
                        file_data["questions"][question_number-1]["subtopic"] = data.get("subtopic")

                        f.seek(0)
                        f.truncate()
                        json.dump(file_data, f, indent=2)
                except json.JSONDecodeError:
                    print(f"Error reading/writing file: {output_path}")
        else:
            print(f"Warning: Output file not found: {output_path}")