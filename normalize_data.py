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

def parse_list(text, delimiter=";"):
  """Splits delimited text into a clean list of strings."""
  if not text or not isinstance(text, str):
    return []
  return [clean_text(item) for item in text.split(delimiter) if item.strip()]

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

  # Filter by status column or approved boolean.
  status_val = str(raw_story.get("Status") or raw_story.get("Approved")).strip().lower()

  if status_val in ["approved", "true"]:
    raw_photo = raw_story.get("Photo URL") or raw_story.get("Photo") or raw_story.get("Headshot URL") or ""

    if isinstance(raw_photo, str) and raw_photo.startswith("http"):
      photo_url = raw_photo.strip()
    elif isinstance(raw_photo, str) and raw_photo.startswith("/"):
      photo_url = f"https://msmary.edu{raw_photo.strip()}"
    else:
      photo_url = "https://directory.msmary.edu/people/people-photos/placeholder-photo.jpg"

    full_name = raw_story.get("Full Name / Headline") or raw_story.get("Full Name")

    if full_name:
      full_name = clean_text(full_name)
      parts = full_name.split(" ")
      first_name = parts[0] if parts else ""
      last_name = parts[-1] if len(parts) > 1 else ""
    else:
      first_name = clean_text(raw_story.get("First") or "")
      last_name = clean_text(raw_story.get("Last") or "")
      full_name = f"{first_name} {last_name}".strip()

    override_last = clean_text(raw_story.get("Sort Last Name"))

    if override_last:
      last_name = override_last

    raw_roles = raw_story.get("Roles / Tags") or raw_story.get("Role") or ""
    roles_list = parse_list(raw_roles, delimiter=",")

    normalized_roles = [r.lower() for r in roles_list]
      
    cleaned_item = {
      "id": clean_text(raw_story.get("Story ID")),
      "first_name": first_name,
      "last_name": last_name,
      "full_name": full_name,
      "story_type": clean_text(raw_story.get("Story Type") or "person").lower(),
      "roles": normalized_roles,
      "class_year": clean_text(raw_story.get("Class Year")),
      "photo_url": photo_url,
      "location": clean_text(raw_story.get("Hometown / Location") or raw_story.get("City, State")),
      "majors": parse_list(raw_story.get("Majors / Programs") or raw_story.get("Major(s)"), delimiter=";"),
      "current_role": clean_text(raw_story.get("Role / Next Steps / Excerpt") or raw_story.get("Job Title / Graduate Program")),
      "testimonials": parse_list(raw_story.get("Testimonials"), delimiter="|"),
      "related_news": parse_list(raw_story.get("Related News URLs"), delimiter="|")
    }
    normalized_stories.append(cleaned_item)

with open("stories.json", "w", encoding="utf-8") as f:
  json.dump(normalized_stories, f, indent=2, ensure_ascii=False)
  
print(f"Successfully exported {len(normalized_stories)} approved stories to stories.json.")
