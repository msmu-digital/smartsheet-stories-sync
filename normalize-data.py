import os
import json
import requests
import unicodedata

def clean_text(text):
  if not isinstance(text, str):
    return text
  text = unicodedata.normalize("NFKC", text)
  text = text.replace("\u2019", "'").replace("\u2018", "'")
  text = text.replace("\u201c", '"').replace("\u201d", '"')
  return text.strip()

token = os.getenv("SMARTSHEET_ACCESS_TOKEN")
sheet_id = os.getenv("SMARTSHEET_SHEET_ID")

headers = {"Authorization": f"Bearer {token}"}

columns_url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}/columns"
col_response = requests.get(columns_url, headers=headers)
col_data = col_response.json()

col_map = {col["id"]: col["title"].strip() for col in col_data.get("data", [])}

sheet_url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}"
sheet_response = requests.get(sheet_url, headers=headers)
sheet_data = sheet_response.json()

normalized_stories = []

for row in sheet_data.get("rows", []):
  raw_story = {}
  for cell in row.get("cells", []):
    col_name = col_map.get(cell.get("columnId"))
    if col_name:
      raw_story[col_name] = cell.get("value")

  approved_val = raw_story.get("Approved")
  if approved_val is True or str(approved_val).lower() == "true":
      raw_photo = raw_story.get("Photo") or raw_story.get("Photo URL") or raw_story.get("Headshot URL") or ""

      if isinstance(raw_photo, str) and raw_photo.startswith("http"):
        photo_url = raw_photo.strip()
      elif isinstance(raw_photo, str) and raw_photo.startswith("/"):
        photo_url = f"https://msmary.edu{raw_photo.strip()}"
      else:
        photo_url = "https://directory.msmary.edu/people/people-photos/placeholder-photo.jpg"

      first_name = clean_text(raw_story.get("First"))
      last_name = clean_text(raw_story.get("Last"))
      
      cleaned_item = {
        "first_name": first_name,
        "last_name": last_name,
        "full_name": f"{first_name} {last_name}".strip(),
        "photo_url": photo_url,
        "location": clean_text(raw_story.get("City, State")),
        "majors": clean_text(raw_story.get("Major(s)")),
        "current_role": clean_text(raw_story.get("Job title / Graduate program")),
        "quote_why_mount": clean_text(raw_story.get("Why did you choose the Mount?")),
        "quote_why_major": clean_text(raw_story.get("Why did you choose your major?")),
        "activities": clean_text(raw_story.get("What activities were you involved in and why?")),
        "meaningful_experience": clean_text(raw_story.get("Most meaningful experience? Social, academic, etc.")),
        "quote_equipped": clean_text(raw_story.get("How has the Mount equipped your for post-college?")),
        "quote_live_significantly": clean_text(raw_story.get("How will you live significantly?"))
      }
      normalized_stories.append(cleaned_item)

with open("stories.json", "w", encoding="utf-8") as f:
  json.dump(normalized_stories, f, indent=2, ensure_ascii=False)
  
print(f"Successfully exported {len(normalized_stories)} approved stories to stories.json.")
