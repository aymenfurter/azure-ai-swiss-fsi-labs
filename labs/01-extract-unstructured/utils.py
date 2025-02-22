import logging
import wikipedia
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from content_understanding import ContentUnderstandingClient

def get_wikipedia_content(person_name: str) -> Optional[bytes]:
    """Fetch Wikipedia content for a person."""
    try:
        page = wikipedia.page(wikipedia.search(person_name)[0], auto_suggest=False)
        return page.content.split('\n\n')[0].encode('utf-8')
    except Exception as e:
        logging.error(f"Error fetching Wikipedia content for {person_name}: {e}")
        return None

def download_audio(url: str, output_path: Path) -> Optional[Path]:
    """Download audio file from URL."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return output_path
    except Exception as e:
        logging.error(f"Error downloading audio: {e}")
        return None

def extract_info_from_result(result):
    """
    Given a result dictionary from the analyzer,
    extract the relevant fields and return as a dict.
    """
    # Safety check
    if not result or not result.get("contents"):
        return {}

    fields = result["contents"][0].get("fields", {})

    # Extract affiliations
    affiliations = []
    if 'valueArray' in fields.get('affiliations', {}):
        for aff in fields['affiliations']['valueArray']:
            if 'valueObject' in aff:
                obj = aff['valueObject']
                affiliation = {
                    'company': obj.get('Company', {}).get('valueString', ''),
                    'position': obj.get('Position', {}).get('valueString', ''),
                    'entry_year': obj.get('EntryYear', {}).get('valueString', 'Unknown')
                }
                affiliations.append(affiliation)

    # Extract legal issues
    legal_issues = []
    if 'valueArray' in fields.get('legal_issues', {}):
        legal_issues = [issue['valueString'] for issue in fields['legal_issues']['valueArray']]

    # Format affiliations as string
    affiliations_str = ', '.join([
        f"- {a['company']}: {a['position']} ({a['entry_year']})"
        for a in affiliations
    ]) or "None"

    # Format legal issues as string
    legal_issues_str = ', '.join([
        f"- {issue}"
        for issue in legal_issues
    ]) or "None reported"

    return {
        "Full Name": fields.get('full_name', {}).get('valueString', ''),
        "DOB": fields.get('birthdate', {}).get('valueString', ''),
        "Nationality": fields.get('nationality', {}).get('valueString', ''),
        "Affiliations": affiliations_str,
        "Legal Issues": legal_issues_str,
        "PEP?": fields.get('political_exposure', {}).get('valueString', ''),
        "Summary": fields.get('summary', {}).get('valueString', '')
    }
