import os
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup

# URL to public XML sitemap.
SITEMAP_URL = "https://msmary.edu/sitemap.xml"

# Headers to prevent request blocking during automated crawling.
HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def get_urls_from_sitemap(sitemap_url):
  """Fetches and parses URLs from an XML sitemap or sitemap index."""
  urls = []
  try:
    response = requests.get(sitemap_url, headers=HEADERS, timeout=15)
    if response.status_code != 200:
      print(f"Failed to fetch sitemap: HTTP {response.status_code}")
      return urls

    root = ET.fromstring(response.content)
    # Handle standard XML sitemap namespace.
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    # Check if this is a sitemap index (list of other sitemaps).
    sitemaps = root.findall('ns:sitemap', namespace)
    if sitemaps:
      for sm in sitemaps:
        loc = sm.find('ns:loc', namespace)
        if loc is not None and loc.text:
          urls.extend(get_urls_from_sitemap(loc.text))
    else:
      # Standard sitemap containing page URLs.
      for url_tag in root.findall('ns:url', namespace):
        loc = url_tag.find('ns:loc', namespace)
        if loc is not None and loc.text:
          urls.append(loc.text)
  except Exception as e:
    print(f"Error parsing sitemap ({sitemap_url}): {e}")

  return list(set(urls))

def audit_pages(page_urls):
  """Crawls published pages to locate story grid containers and filters."""
  audit_results = []
  print(f"Scanning {len(page_urls)} published pages for success story components...")

  for url in page_urls:
    try:
      resp = requests.get(url, headers=HEADERS, timeout=10)
      if resp.status_code != 200:
        continue

      soup = BeautifulSoup(resp.content, 'html.parser')
      containers = soup.find_all(class_='story-grid-container')

      if containers:
        for container in containers:
          filter_attr = container.get('data-story-filter', '').strip()
          limit_attr = container.get('data-story-limit', 'All').strip()

          audit_results.append({
            'page_url': url,
            'filter': filter_attr if filter_attr else '(No Filter / All Stories)',
            'limit': limit_attr
          })
    except Exception as e:
      print(f"Could not scan page {url}: {e}")

  return audit_results

def generate_html_report(results, output_file="usage_report.html"):
  """Generates an HTML report summarizing story usage across the site."""
  html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Success Story Placement Audit Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 2rem; background: #f9f9f9; color: #333333; }}
    h1 {{ color: #003366; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; background: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #dddddd; }}
    tr:hover {{ background-color: #f1f1f1; }}
    .badge {{ background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }}
    .empty {{ font-style: italic; color: #777777; }}
  </style>
</head>
<body>
  <h1>Success Story Placement Audit Report</h1>
  <p>Generated automatically on scan. Total components found: <strong>{len(result)}</strong></p>
  <table>
    <thead>
      <tr>
        <th>Page URL</th>
        <th>Applied Filter (Targeted Story / Major)</th>
        <th>Card Limit</th>
      </tr>
    </thead>
    <tbody>
  """

  if not results:
    html_content += '<tr><td colspan="3" class="empty">No story grid components were found on any scanned sitemap pages.</td></tr>'
  else:
    for item in results:
      html_content += f"""
      <tr>
        <td><a href="{item['page_url']}" target="_blank">{item['page_url']}</a></td>
        <td><span class="badge">{item['filter']}</span></td>
        <td>{item['limit']}</td>
      </tr>
      """

  html_content += """
    </tbody>
  </table>
</body>
</html>
  """

  with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

  print(f"Report successfully saved to {output_file}")

if __name__ == "__main__":
  urls = get_urls_from_sitemap(SITEMAP_URL)
  results = audit_pages(urls)
  generate_html_report(results)
