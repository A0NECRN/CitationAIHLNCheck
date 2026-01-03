import requests
import time
import re
import xml.etree.ElementTree as ET
from rapidfuzz import fuzz
from urllib.parse import quote

# ==========================================
# Configuration
# ==========================================
CROSSREF_API_URL = "https://api.crossref.org/works"
SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
ARXIV_API_URL = "http://export.arxiv.org/api/query"

# Be polite to the APIs
HEADERS = {
    "User-Agent": "CitationCheck/2.0 (mailto:citation_check_bot@example.com)"
}

# Similarity Thresholds (0-100)
THRESHOLD_VALID = 85      # High confidence match
THRESHOLD_UNCERTAIN = 60  # Needs manual check

def clean_title(title):
    """
    Cleans the title by removing BibTeX specific characters and extra spaces.
    """
    if not title:
        return ""
    # Remove braces {}
    title = title.replace('{', '').replace('}', '')
    # Remove quotes
    title = title.replace('"', '').replace("'", "")
    # Remove multiple spaces
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def calculate_similarity(s1, s2):
    """
    Calculates similarity using RapidFuzz's token_sort_ratio.
    This is robust against word order changes and punctuation.
    """
    if not s1 or not s2:
        return 0.0
    # token_sort_ratio handles "The AI" vs "AI, The" well
    return fuzz.token_sort_ratio(s1.lower(), s2.lower())

def check_author_match(entry_author, result_authors):
    """
    Checks if the entry author matches any of the result authors.
    Simple fuzzy matching on last names.
    """
    if not entry_author or not result_authors:
        return False

    # Extract first author's last name from BibTeX entry
    # BibTeX usually: "Lastname, Firstname" or "Firstname Lastname"
    # Simplified extraction:
    entry_author_clean = entry_author.split(',')[0].split(' and ')[0].strip()
    
    # Check against result authors
    # Crossref: [{'given': '...', 'family': '...'}, ...]
    # S2: [{'name': '...'}, ...]
    
    for author in result_authors:
        if isinstance(author, dict):
            # Crossref
            if 'family' in author:
                 if fuzz.partial_ratio(entry_author_clean.lower(), author['family'].lower()) > 80:
                     return True
            # S2
            if 'name' in author:
                 if fuzz.partial_ratio(entry_author_clean.lower(), author['name'].lower()) > 80:
                     return True
        elif isinstance(author, str):
             if fuzz.partial_ratio(entry_author_clean.lower(), author.lower()) > 80:
                 return True
                 
    return False

def check_year_match(entry_year, result_year):
    """
    Checks if the entry year matches the result year.
    Allows for a small margin of error (e.g. +/- 2 years) for preprints/journal lag.
    """
    if not entry_year or not result_year:
        # If one is missing, we can't be sure, so don't penalize too hard but don't confirm.
        return None
    
    try:
        # Clean years (handle '2020a', '2021-2022')
        y1 = int(re.search(r'\d{4}', str(entry_year)).group())
        y2 = int(re.search(r'\d{4}', str(result_year)).group())
        
        diff = abs(y1 - y2)
        
        if diff <= 2:
            return True
        return False
    except:
        return None

# ==========================================
# Source 1: Crossref
# ==========================================
def verify_by_crossref_doi(doi):
    try:
        url = f"{CROSSREF_API_URL}/{doi}"
        response = requests.get(url, headers=HEADERS, timeout=20)
        
        if response.status_code == 200:
            data = response.json()['message']
            
            # Extract Year
            year = None
            if 'published' in data and 'date-parts' in data['published']:
                year = data['published']['date-parts'][0][0]
            elif 'issued' in data and 'date-parts' in data['issued']:
                 year = data['issued']['date-parts'][0][0]

            return {
                "status": "valid",
                "source": "Crossref (DOI)",
                "title": data.get('title', [''])[0],
                "url": data.get('URL', ''),
                "year": year,
                "score": 100
            }
        return None
    except requests.exceptions.Timeout:
        return None
    except:
        return None

def verify_by_crossref_search(title, author=None, year=None):
    try:
        query = title
        if author:
            # Taking the first author's last name often helps
            first_author = author.split(',')[0].split(' and ')[0].strip()
            query += f" {first_author}"
            
        params = {
            "query.bibliographic": query,
            "rows": 3 # Fetch top 3 to increase hit rate
        }
        
        response = requests.get(CROSSREF_API_URL, headers=HEADERS, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()['message']
            if not data['items']:
                return None
            
            best_match = None
            best_score = 0
            
            for item in data['items']:
                found_title = item.get('title', [''])[0]
                similarity = calculate_similarity(title, found_title)
                
                # Check authors if similarity is in "uncertain" range
                is_author_match = False
                if 'author' in item:
                    is_author_match = check_author_match(author, item['author'])
                
                # Extract Year
                found_year = None
                if 'published' in item and 'date-parts' in item['published']:
                    found_year = item['published']['date-parts'][0][0]
                elif 'issued' in item and 'date-parts' in item['issued']:
                    found_year = item['issued']['date-parts'][0][0]
                
                # Check Year Match
                is_year_match = check_year_match(year, found_year)
                
                # Bonus score logic
                final_score = similarity
                
                if is_author_match:
                     final_score += 15
                
                # Penalize if year mismatch heavily
                if year and found_year:
                    if is_year_match == False:
                        final_score -= 30 # Severe penalty for year mismatch
                
                if final_score > 100: final_score = 100
                if final_score < 0: final_score = 0
                
                if final_score > best_score:
                    best_score = final_score
                    best_match = {
                        "title": found_title,
                        "url": item.get('URL', ''),
                        "doi": item.get('DOI', ''),
                        "score": similarity, # Keep original similarity for display
                        "final_score": final_score, # Use boosted score for decision
                        "source": "Crossref (Search)",
                        "authors": item.get('author', []),
                        "year": found_year
                    }

            return best_match
        return None
    except requests.exceptions.Timeout:
        return None
    except:
        return None

# ==========================================
# Source 2: Semantic Scholar (S2)
# ==========================================
def verify_by_semantic_scholar(title, author=None, year=None):
    """
    Uses Semantic Scholar Graph API to find papers.
    Good for CS, arXiv, and recent papers.
    Includes retry logic for rate limits.
    """
    params = {
        "query": title,
        "limit": 1,
        "fields": "title,url,doi,year,authors"
    }
    
    max_retries = 3
    base_wait = 2
    
    for attempt in range(max_retries):
        try:
            # S2 public API rate limit is low
            time.sleep(1) 
            
            response = requests.get(SEMANTIC_SCHOLAR_API_URL, headers=HEADERS, params=params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                if not data.get('data'):
                    return None
                    
                item = data['data'][0]
                found_title = item.get('title', '')
                similarity = calculate_similarity(title, found_title)
                
                # Check authors
                is_author_match = False
                if 'authors' in item:
                    is_author_match = check_author_match(author, item['authors'])
                
                # Check Year
                found_year = item.get('year')
                is_year_match = check_year_match(year, found_year)
                
                final_score = similarity
                if is_author_match:
                    final_score += 15
                
                if year and found_year:
                    if is_year_match == False:
                        final_score -= 30

                if final_score > 100: final_score = 100
                if final_score < 0: final_score = 0

                return {
                    "title": found_title,
                    "url": item.get('url', ''),
                    "doi": item.get('doi', ''),
                    "score": similarity,
                    "final_score": final_score,
                    "source": "Semantic Scholar",
                    "authors": item.get('authors', []),
                    "year": found_year
                }
            elif response.status_code == 429:
                 # Rate limited
                 wait_time = base_wait * (2 ** attempt)
                 print(f" [!] Semantic Scholar rate limited, waiting {wait_time}s...")
                 time.sleep(wait_time)
                 continue
            else:
                return None
        except requests.exceptions.Timeout:
            return None
        except Exception as e:
            return None
            
    return None

# ==========================================
# Source 3: arXiv API
# ==========================================
def verify_by_arxiv(title, author=None, year=None):
    """
    Uses arXiv API to find papers.
    Great for CS/AI/Physics papers.
    """
    try:
        # Search by title
        # arXiv API expects: search_query=ti:"Title"
        # We need to be careful with special characters in title
        # Replace non-alphanumeric characters with space instead of removing them
        clean_t = re.sub(r'[^\w\s]', ' ', title) 
        clean_t = re.sub(r'\s+', ' ', clean_t).strip()
        
        # Strategy A: Precise Title Match
        query = f'ti:"{clean_t}"'
        
        # Strategy B: If author provided, add author to query for better disambiguation
        # This helps with common titles like "Graph Attention Networks"
        if author:
            # Extract last name of first author
            first_author_last = author.split(',')[0].split(' and ')[0].strip()
            # Clean it
            first_author_last = re.sub(r'[^\w\s]', '', first_author_last)
            if first_author_last:
                query += f' AND au:"{first_author_last}"'
        
        params = {
            "search_query": query,
            "start": 0,
            "max_results": 1
        }
        
        # Retry logic for arXiv
        for _ in range(2):
            try:
                response = requests.get(ARXIV_API_URL, params=params, timeout=30)
                if response.status_code == 200:
                    break
            except:
                time.sleep(1)
        else:
            return None
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            # Namespace map
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            entry = root.find('atom:entry', ns)
            
            # If Strategy A+B failed, try fallback: just Title (loose) or just Author+Title keywords
            if entry is None and author:
                 # Fallback: title AND author (no quotes on title to allow fuzzy match)
                 # Note: arXiv API syntax is tricky. Let's try `all:Title AND au:Author`
                 query_fallback = f'all:{clean_t} AND au:{first_author_last}'
                 params['search_query'] = query_fallback
                 
                 for _ in range(2):
                    try:
                        response = requests.get(ARXIV_API_URL, params=params, timeout=30)
                        if response.status_code == 200:
                            root = ET.fromstring(response.content)
                            entry = root.find('atom:entry', ns)
                            if entry is not None:
                                break
                    except:
                        time.sleep(1)

            if entry is None:
                return None
                
            found_title = entry.find('atom:title', ns).text.strip()
            found_title = re.sub(r'\s+', ' ', found_title) # Normalize whitespace
            
            # Extract authors
            found_authors = []
            for author_elem in entry.findall('atom:author', ns):
                name = author_elem.find('atom:name', ns).text
                found_authors.append(name)
            
            # Extract Year
            found_year = None
            published = entry.find('atom:published', ns)
            if published is not None:
                 # Format: 2017-10-30T16:00:23Z
                 found_year = published.text[:4]

            similarity = calculate_similarity(title, found_title)
            
            # Check authors
            is_author_match = check_author_match(author, found_authors)
            
            # Check Year
            is_year_match = check_year_match(year, found_year)

            final_score = similarity
            if is_author_match:
                final_score += 15
            
            if year and found_year:
                if is_year_match == False:
                    final_score -= 30

            if final_score > 100: final_score = 100
            if final_score < 0: final_score = 0
                
            # Get link
            link = entry.find('atom:id', ns).text
            
            return {
                "title": found_title,
                "url": link,
                "doi": "", # arXiv entries might have DOI link but usually just arXiv ID
                "score": similarity,
                "final_score": final_score,
                "source": "arXiv API",
                "authors": found_authors,
                "year": found_year
            }
            
        return None
    except Exception as e:
        return None

# ==========================================
# Main Verification Logic
# ==========================================
def verify_citation(entry):
    """
    Orchestrates the verification process across multiple sources.
    """
    # 1. Clean Metadata
    raw_title = entry.get('title', '')
    clean_t = clean_title(raw_title)
    author = entry.get('author', '')
    year = entry.get('year', '') # Extract year
    
    if not clean_t:
         return {"status": "error", "reason": "No Title provided"}

    # 2. Strategy: DOI First (The Gold Standard)
    if 'doi' in entry and entry['doi']:
        res = verify_by_crossref_doi(entry['doi'])
        if res:
            return res

    # 3. Strategy: Crossref Search
    res_crossref = verify_by_crossref_search(clean_t, author, year)
    
    # Check if Crossref is good enough
    ACCEPTANCE_THRESHOLD = 80 
    
    if res_crossref and res_crossref.get('final_score', 0) >= ACCEPTANCE_THRESHOLD:
        res_crossref['status'] = 'valid'
        return res_crossref

    # 4. Strategy: Semantic Scholar Search (Fallback)
    res_s2 = verify_by_semantic_scholar(clean_t, author, year)
    
    if res_s2 and res_s2.get('final_score', 0) >= ACCEPTANCE_THRESHOLD:
        res_s2['status'] = 'valid'
        return res_s2

    # 5. Strategy: arXiv Search (Deep Fallback for CS/AI)
    res_arxiv = verify_by_arxiv(clean_t, author, year)
    
    if res_arxiv and res_arxiv.get('final_score', 0) >= ACCEPTANCE_THRESHOLD:
        res_arxiv['status'] = 'valid'
        return res_arxiv

    # 6. Comparison and Decision
    # Pick best from all 3 sources
    candidates = [c for c in [res_crossref, res_s2, res_arxiv] if c]
    
    if not candidates:
        return {
            "status": "not_found",
            "reason": "No results from Crossref, Semantic Scholar, or arXiv"
        }
        
    best_res = max(candidates, key=lambda x: x.get('final_score', 0))
    best_score = best_res.get('final_score', 0)
    
    if best_score >= THRESHOLD_UNCERTAIN:
        best_res['status'] = 'uncertain'
        # Update reason to show why (e.g. "Author matched but title differs")
        reason_str = f"Similarity {best_res['score']:.1f}%"
        if best_score > best_res['score']:
            reason_str += " (Boosted by Author Match)"
        if best_score < best_res['score']:
            reason_str += " (Penalized by Year Mismatch)"
        best_res['reason'] = reason_str + f" (Threshold {ACCEPTANCE_THRESHOLD}%)"
        return best_res
    else:
         return {
            "status": "not_found",
            "reason": f"Best match only {best_res['score']:.1f}% similar (Penalized Score: {best_score:.1f})",
            "best_guess": best_res
        }
