import os
import json
import time
import random
import urllib.parse
import subprocess
import re
from typing import List, Dict, Optional, Set, Any
import requests
from bs4 import BeautifulSoup
import html2text
import yaml
from pathlib import Path
from functools import lru_cache
from collections import Counter, defaultdict
from tqdm import tqdm
from process_package import process_package
from common import Tool, clean_text, is_valid_tool, determine_category, extract_tags, sleep_between_requests
from datetime import datetime, timezone

__all__ = ['browser_navigate', 'browser_view', 'run_javascript_browser', 'wait_for_element']

# Constants
CHECKPOINT_FILE = 'tools_checkpoint.json'
CATEGORY_STATS_FILE = 'category_stats.json'
GITHUB_CACHE_FILE = 'github_cache.json'
GITHUB_RATE_LIMIT_SLEEP = random.uniform(1, 3)  # Random sleep between 1-3 seconds
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3  # Maximum number of retries for failed requests
MIN_SLEEP = 1  # Minimum sleep between requests
MAX_SLEEP = 3  # Maximum sleep between requests

def run_github_query(query):
    """Run a GitHub search query using REST API"""
    print(f"Running GitHub query: {query}")
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            # Use gh api search/repositories endpoint
            cmd = ['gh', 'api', '-X', 'GET', '/search/repositories',
                  '-f', f'q={query}',
                  '-f', 'sort=stars',
                  '-f', 'order=desc',
                  '-f', 'per_page=100']

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            if 'items' in data:
                return data['items']
            return []

        except subprocess.CalledProcessError as e:
            print(f"Error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Skipping query.")
                return []

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return []

    return []



# Load GitHub cache
github_cache = {}
if Path(GITHUB_CACHE_FILE).exists():
    try:
        with open(GITHUB_CACHE_FILE, 'r') as f:
            github_cache = json.load(f)
    except Exception as e:
        print(f"Error loading GitHub cache: {e}")

def save_github_cache():
    with open(GITHUB_CACHE_FILE, 'w') as f:
        json.dump(github_cache, f, indent=2)

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    return ' '.join(text.strip().split())

def determine_importance(name: str, description: str, stars: int = 0) -> str:
    """Determine the importance of a tool based on various factors"""
    # Convert name and description to lowercase for comparison
    name = str(name).lower()
    description = str(description).lower() if description else ''

    # Essential tools list
    essential_tools = {'kubernetes', 'docker', 'jenkins', 'terraform', 'prometheus', 'git'}
    if name in essential_tools or stars > 10000:
        return 'Essential'
    elif stars > 5000:
        return 'Recommended'
    return 'Optional'

@lru_cache(maxsize=1000)
def extract_github_info(url: str, retry_count: int = 0) -> Dict:
    """Extract information from GitHub repository using gh CLI with exponential backoff"""
    if not url or 'github.com' not in url:
        return {'stars': 0, 'description': '', 'is_open_source': True}

    # Check cache first
    if url in github_cache:
        return github_cache[url]

    try:
        # Extract owner and repo from URL
        parts = url.strip('/').split('/')
        if len(parts) < 5:
            return {'stars': 0, 'description': '', 'is_open_source': True}

        owner = parts[-2]
        repo = parts[-1]

        # Exponential backoff for retries
        if retry_count > 0:
            sleep_time = min(300, GITHUB_RATE_LIMIT_SLEEP * (2 ** retry_count))
            print(f"\nRate limit hit, waiting {sleep_time:.1f} seconds before retry {retry_count}/{MAX_RETRIES}...")
            time.sleep(sleep_time)

        # Use GitHub CLI to get repo info with timeout
        try:
            result = subprocess.run(
                ['gh', 'repo', 'view', f"{owner}/{repo}", '--json', 'stargazerCount,description,isPrivate,name'],
                capture_output=True,
                text=True,
                timeout=REQUEST_TIMEOUT
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                info = {
                    'stars': int(data.get('stargazerCount', 0)),
                    'description': data.get('description', ''),
                    'is_open_source': not data.get('isPrivate', False),
                    'name': data.get('name', repo)
                }
                # Cache the result
                github_cache[url] = info
                save_github_cache()
                return info
            elif 'rate limit exceeded' in result.stderr.lower() and retry_count < MAX_RETRIES:
                return extract_github_info(url, retry_count + 1)
            else:
                print(f"\nError accessing repo {owner}/{repo}: {result.stderr}")
                return {'stars': 0, 'description': '', 'is_open_source': True}

        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            print(f"\nError processing GitHub repo {owner}/{repo}: {e}")
            if retry_count < MAX_RETRIES:
                return extract_github_info(url, retry_count + 1)
            return {'stars': 0, 'description': '', 'is_open_source': True}

    except Exception as e:
        print(f"\nError processing GitHub URL {url}: {e}")
        return {'stars': 0, 'description': '', 'is_open_source': True}

def scrape_awesome_lists():
    """Scrape tools from curated awesome lists"""
    tools = []
    print("\nScraping awesome lists...")

    awesome_lists = {
        'api-gateway': [
            'https://raw.githubusercontent.com/yosriady/awesome-api-gateway/master/README.md',
            'https://raw.githubusercontent.com/svenwal/awesome-api-gateways/master/README.md'
        ],
        'api-management': [
            'https://raw.githubusercontent.com/mailtoharshit/awesome-api/master/README.md',
            'https://raw.githubusercontent.com/APIs-guru/awesome-openapi3/master/README.md'
        ],
        'version-control': [
            'https://raw.githubusercontent.com/vinta/awesome-python/master/README.md#version-control',
            'https://raw.githubusercontent.com/stevemao/awesome-git-addons/master/README.md'
        ],
        'service-mesh': [
            'https://raw.githubusercontent.com/ramitsurana/awesome-kubernetes/master/docs/service-mesh.md',
            'https://raw.githubusercontent.com/servicemesher/awesome-servicemesh/master/README.md'
        ]
    }

    for category, urls in awesome_lists.items():
        for url in urls:
            try:
                print(f"\nProcessing awesome list: {url}")
                response = requests.get(url)
                if response.status_code != 200:
                    continue

                content = response.text
                # Extract GitHub repository links
                github_links = re.findall(r'https://github.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+', content)

                for github_url in github_links:
                    try:
                        # Use gh api to get repository info
                        repo_path = github_url.replace('https://github.com/', '')
                        result = subprocess.run(
                            ['gh', 'api', f'repos/{repo_path}'],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        repo_data = json.loads(result.stdout)

                        # Skip archived and private repositories
                        if repo_data.get('archived', False) or repo_data.get('private', True):
                            continue

                        # Determine importance based on stars
                        stars = repo_data.get('stargazers_count', 0)
                        if stars >= 5000:
                            importance = 'Essential'
                        elif stars >= 1000:
                            importance = 'Recommended'
                        else:
                            importance = 'Optional'

                        tool = Tool(
                            name=repo_data.get('name', ''),
                            description=clean_text(repo_data.get('description', '')),
                            category=category,
                            importance=importance,
                            isOpenSource=not repo_data.get('private', True),
                            url=repo_data.get('homepage', '') or github_url,
                            githubUrl=github_url,
                            stars=stars,
                            language=repo_data.get('language'),
                            topics=repo_data.get('topics', [])
                        )

                        if is_valid_tool(tool):
                            print(f"Added tool from awesome list: {tool.name} ({tool.category})")
                            tools.append(tool)

                        sleep_between_requests(1, 3)

                    except Exception as e:
                        print(f"Error processing GitHub URL {github_url}: {str(e)}")
                        continue

            except Exception as e:
                print(f"Error processing awesome list {url}: {str(e)}")
                continue

    print(f"Collected {len(tools)} tools from awesome lists")
    return tools



def scrape_cncf_landscape():
    """Scrape tools from CNCF landscape with improved categorization"""
    tools = []
    print("\nScraping CNCF landscape...")

    try:
        # Get CNCF landscape data from GitHub raw content
        response = requests.get('https://raw.githubusercontent.com/cncf/landscape/master/landscape.yml')
        if response.status_code != 200:
            print("Failed to fetch CNCF landscape data")
            return tools

        landscape_yaml = yaml.safe_load(response.text)

        # Focus on underrepresented categories
        target_categories = {
            'API Gateway': ['API Gateway', 'API', 'Gateway'],
            'API Management': ['API Management', 'API'],
            'Version Control': ['Version Control', 'Source Control'],
            'Service Mesh': ['Service Mesh', 'Service Proxy']
        }

        for category in landscape_yaml.get('landscape', []):
            category_name = category.get('name', '')
            for subcategory in category.get('subcategories', []):
                for item in subcategory.get('items', []):
                    try:
                        repo_url = item.get('repo_url', '')
                        if not repo_url or 'github.com' not in repo_url:
                            continue

                        # Get repository info using GitHub API
                        repo_path = repo_url.replace('https://github.com/', '')
                        result = subprocess.run(
                            ['gh', 'api', f'repos/{repo_path}'],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        repo_data = json.loads(result.stdout)

                        # Skip archived and private repositories
                        if repo_data.get('archived', False) or repo_data.get('private', True):
                            continue

                        # Determine importance based on stars
                        stars = repo_data.get('stargazers_count', 0)
                        if stars >= 5000:
                            importance = 'Essential'
                        elif stars >= 1000:
                            importance = 'Recommended'
                        else:
                            importance = 'Optional'

                        # Create tool object
                        tool = Tool(
                            name=repo_data.get('name', ''),
                            description=clean_text(repo_data.get('description', '')),
                            category=determine_category(
                                repo_data.get('name', ''),
                                repo_data.get('description', ''),
                                repo_data.get('topics', [])
                            ),
                            importance=importance,
                            isOpenSource=not repo_data.get('private', True),
                            url=repo_data.get('homepage', '') or repo_url,
                            githubUrl=repo_url,
                            stars=stars,
                            language=repo_data.get('language'),
                            topics=repo_data.get('topics', [])
                        )

                        if is_valid_tool(tool):
                            print(f"Added CNCF tool: {tool.name} ({tool.category})")
                            tools.append(tool)

                        sleep_between_requests(1, 3)

                    except Exception as e:
                        print(f"Error processing CNCF item: {str(e)}")
                        continue

    except Exception as e:
        print(f"Error scraping CNCF landscape: {str(e)}")

    print(f"Collected {len(tools)} tools from CNCF landscape")
    return tools

def scrape_github_topics(categories: List[str]) -> List[Tool]:
    """Scrape GitHub topics with enhanced focus on underrepresented categories"""
    tools = []

    # Priority weights for underrepresented categories
    category_weights = {
        'API Gateway': 3,
        'API Management': 3,
        'Service Mesh': 3,
        'Version Control': 3,
        'Cost Management': 2,
        'Logging': 2,
        'Testing': 2
    }

    for category in categories:
        try:
            # Determine search priority and terms based on category
            weight = category_weights.get(category, 1)
            search_terms = []

            # Category-specific search terms
            if category == 'API Gateway':
                search_terms = ['api-gateway', 'api-proxy', 'api-router', 'api-gateway-server']
            elif category == 'API Management':
                search_terms = ['api-management', 'api-manager', 'api-platform', 'api-lifecycle']
            elif category == 'Service Mesh':
                search_terms = ['service-mesh', 'service-proxy', 'service-discovery', 'service-mesh-control']
            elif category == 'Version Control':
                search_terms = ['version-control-system', 'git-server', 'version-manager']
            else:
                search_terms = [category.lower().replace(' ', '-')]

            # Search with category-specific terms
            for term in search_terms:
                query = f'topic:{term} stars:>50'
                results = run_github_query(query)

                for repo in results:
                    try:
                        tool = extract_github_info(repo, category)
                        if tool and is_valid_tool(tool):
                            # Prioritize tools in underrepresented categories
                            if weight > 1:
                                tool.importance = 'Recommended'
                            tools.append(tool)
                            print(f"Added GitHub {category} tool: {tool.name}")
                    except Exception as e:
                        print(f"Error processing GitHub repository: {str(e)}")
                        continue

                    sleep_between_requests(1, 2)  # Rate limiting

            # Additional focused search for underrepresented categories
            if weight > 1:
                focused_query = f'language:go,java,python,typescript {category.lower().replace(" ", "-")} stars:>100'
                focused_results = run_github_query(focused_query)

                for repo in focused_results:
                    try:
                        tool = extract_github_info(repo, category)
                        if tool and is_valid_tool(tool):
                            tool.importance = 'Recommended'
                            tools.append(tool)
                            print(f"Added focused GitHub {category} tool: {tool.name}")
                    except Exception as e:
                        print(f"Error processing focused GitHub repository: {str(e)}")
                        continue

                    sleep_between_requests(1, 2)  # Rate limiting

        except Exception as e:
            print(f"Error scraping GitHub topics for {category}: {str(e)}")
            continue

    return tools

def scrape_package_registries():
    """Scrape tools from package registries focusing on underrepresented categories"""
    tools = []
    try:
        # Enhanced registry queries for underrepresented categories
        registry_queries = {
            'npm': {
                'API Gateway': [
                    'api-gateway',
                    'api-proxy',
                    'gateway-middleware',
                    'express-gateway',
                    'fastify-gateway'
                ],
                'API Management': [
                    'api-management',
                    'api-documentation',
                    'swagger-ui',
                    'openapi-tools',
                    'graphql-tools'
                ],
                'Service Mesh': [
                    'service-mesh',
                    'istio-client',
                    'linkerd-config',
                    'envoy-proxy',
                    'consul-mesh'
                ],
                'Version Control': [
                    'git-tools',
                    'git-workflow',
                    'version-control',
                    'git-hooks',
                    'git-automation'
                ]
            },
            'pypi': {
                'API Gateway': [
                    'api-gateway',
                    'fastapi-gateway',
                    'django-gateway',
                    'flask-gateway',
                    'aiohttp-gateway'
                ],
                'API Management': [
                    'api-management',
                    'fastapi-tools',
                    'django-rest-tools',
                    'flask-restx',
                    'openapi-core'
                ],
                'Service Mesh': [
                    'service-mesh',
                    'istio-python',
                    'linkerd-python',
                    'consul-python',
                    'envoy-python'
                ],
                'Version Control': [
                    'git-python',
                    'gitpython',
                    'git-tools',
                    'version-control',
                    'git-automation'
                ]
            }
        }

        for registry, categories in registry_queries.items():
            for category, queries in categories.items():
                for query in queries:
                    try:
                        print(f"\nSearching {registry} for {category} tools with query: {query}")
                        if registry == 'npm':
                            url = f"https://registry.npmjs.org/-/v1/search?text={query}&size=100"
                        else:  # pypi
                            url = f"https://pypi.org/pypi/{query}/json"

                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            data = response.json()

                            if registry == 'npm':
                                packages = data.get('objects', [])
                                for pkg in packages:
                                    package = pkg.get('package', {})
                                    if package.get('links', {}).get('repository'):
                                        github_info = extract_github_info(package.get('links', {}).get('repository'))
                                        if github_info:
                                            tool = Tool(
                                                name=package.get('name', ''),
                                                description=clean_text(package.get('description', '')),
                                                category=category,
                                                importance=determine_importance(github_info.get('stargazers_count', 0)),
                                                isOpenSource=True,
                                                url=package.get('links', {}).get('homepage', ''),
                                                githubUrl=package.get('links', {}).get('repository', ''),
                                                stars=github_info.get('stargazers_count', 0),
                                                language='JavaScript',
                                                topics=github_info.get('topics', [])
                                            )
                                            if is_valid_tool(tool):
                                                print(f"Added NPM {category} tool: {tool.name}")
                                                tools.append(tool)

                            else:  # pypi
                                if 'info' in data:
                                    package = data['info']
                                    if package.get('project_urls', {}).get('Source'):
                                        github_info = extract_github_info(package.get('project_urls', {}).get('Source'))
                                        if github_info:
                                            tool = Tool(
                                                name=package.get('name', ''),
                                                description=clean_text(package.get('summary', '')),
                                                category=category,
                                                importance=determine_importance(github_info.get('stargazers_count', 0)),
                                                isOpenSource=True,
                                                url=package.get('home_page', ''),
                                                githubUrl=package.get('project_urls', {}).get('Source', ''),
                                                stars=github_info.get('stargazers_count', 0),
                                                language='Python',
                                                topics=github_info.get('topics', [])
                                            )
                                            if is_valid_tool(tool):
                                                print(f"Added PyPI {category} tool: {tool.name}")
                                                tools.append(tool)

                        sleep_between_requests(1, 2)

                    except Exception as e:
                        print(f"Error processing {registry} query {query}: {str(e)}")
                        continue

                sleep_between_requests(2, 4)

    except Exception as e:
        print(f"Error in scrape_package_registries: {str(e)}")

    return tools

def scrape_additional_registries():
    """Scrape tools from additional package registries focusing on underrepresented categories"""
    tools = []
    try:
        # Enhanced registry sources for underrepresented categories
        registry_sources = {
            'API Gateway': [
                'https://registry.hub.docker.com/search?q=api-gateway&type=image',
                'https://artifacthub.io/packages/search?ts_query_web=api+gateway',
                'https://helm.sh/charts/search?q=api-gateway'
            ],
            'API Management': [
                'https://registry.hub.docker.com/search?q=api-management&type=image',
                'https://artifacthub.io/packages/search?ts_query_web=api+management',
                'https://helm.sh/charts/search?q=api-management'
            ],
            'Service Mesh': [
                'https://registry.hub.docker.com/search?q=service-mesh&type=image',
                'https://artifacthub.io/packages/search?ts_query_web=service+mesh',
                'https://helm.sh/charts/search?q=service-mesh'
            ],
            'Version Control': [
                'https://registry.hub.docker.com/search?q=version-control&type=image',
                'https://artifacthub.io/packages/search?ts_query_web=version+control',
                'https://helm.sh/charts/search?q=git-server'
            ]
        }

        for category, sources in registry_sources.items():
            for source in sources:
                try:
                    print(f"\nScraping {category} tools from: {source}")
                    if browser_navigate(source):
                        content = browser_view()
                        if content:
                            # Extract tool information based on registry type
                            if 'docker.com' in source:
                                docker_tools = extract_docker_tools(content, category)
                                tools.extend(docker_tools)
                            elif 'artifacthub.io' in source:
                                artifact_tools = extract_artifact_tools(content, category)
                                tools.extend(artifact_tools)
                            elif 'helm.sh' in source:
                                helm_tools = extract_helm_tools(content, category)
                                tools.extend(helm_tools)

                    sleep_between_requests(2, 4)

                except Exception as e:
                    print(f"Error processing source {source}: {str(e)}")
                    continue

    except Exception as e:
        print(f"Error in scrape_additional_registries: {str(e)}")

    return tools

def extract_docker_tools(content: str, category: str) -> List[Tool]:
    tools = []
    try:
        # Use Docker Hub API instead of web scraping
        search_term = category.lower().replace(' ', '-')
        api_url = f"https://hub.docker.com/v2/search/repositories/?query={search_term}&page_size=25"

        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])

                for result in results[:10]:  # Process top 10 results
                    name = result.get('name', '')
                    description = result.get('description', '')
                    repo_name = result.get('repo_name', '')
                    stars = result.get('star_count', 0)

                    if name and description:
                        tool = Tool(
                            name=clean_text(name),
                            description=clean_text(description),
                            category=category,
                            importance='Recommended' if stars > 100 else 'Optional',
                            isOpenSource=True,
                            url=f"https://hub.docker.com/r/{repo_name}",
                            githubUrl='',  # Could be extracted from description if needed
                            stars=stars,
                            language='Docker',
                            topics=['docker', category.lower()]
                        )

                        if is_valid_tool(tool):
                            print(f"Added Docker Hub {category} tool: {tool.name}")
                            tools.append(tool)

                    sleep_between_requests(1, 2)  # Rate limiting
            else:
                print(f"Docker Hub API request failed with status code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"Error making Docker Hub API request: {str(e)}")

    except Exception as e:
        print(f"Error in extract_docker_tools: {str(e)}")

    return tools

def extract_artifact_tools(content: str, category: str) -> List[Tool]:
    tools = []
    try:
        # Use ArtifactHub API instead of web scraping
        search_term = category.lower().replace(' ', '-')
        api_url = f"https://artifacthub.io/api/v1/packages/search?kind=0&ts_query_web={search_term}&limit=25"

        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                packages = data.get('packages', [])

                for pkg in packages[:10]:  # Process top 10 results
                    name = pkg.get('name', '')
                    description = pkg.get('description', '')
                    repository = pkg.get('repository', {})
                    stars = pkg.get('stars', 0)
                    github_url = ''

                    # Extract GitHub URL if available
                    links = pkg.get('links', [])
                    for link in links:
                        if 'github.com' in link.get('url', ''):
                            github_url = link['url']
                            break

                    if name and description:
                        tool = Tool(
                            name=clean_text(name),
                            description=clean_text(description),
                            category=category,
                            importance='Recommended' if stars > 50 else 'Optional',
                            isOpenSource=True,
                            url=f"https://artifacthub.io/packages/{repository.get('kind', 'helm')}/{repository.get('name', '')}/{name}",
                            githubUrl=github_url,
                            stars=stars,
                            language=repository.get('kind', '').capitalize(),
                            topics=[repository.get('kind', ''), category.lower()]
                        )

                        if is_valid_tool(tool):
                            print(f"Added ArtifactHub {category} tool: {tool.name}")
                            tools.append(tool)

                    sleep_between_requests(1, 2)  # Rate limiting
            else:
                print(f"ArtifactHub API request failed with status code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"Error making ArtifactHub API request: {str(e)}")

    except Exception as e:
        print(f"Error in extract_artifact_tools: {str(e)}")

    return tools

def extract_helm_tools(content: str, category: str) -> List[Tool]:
    tools = []
    try:
        # Use ArtifactHub API specifically for Helm charts
        search_term = category.lower().replace(' ', '-')
        api_url = f"https://artifacthub.io/api/v1/packages/search?kind=0&ts_query_web={search_term}&facets=true&filters=kind%3D0"

        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                packages = data.get('packages', [])

                for pkg in packages[:10]:  # Process top 10 results
                    name = pkg.get('name', '')
                    description = pkg.get('description', '')
                    repository = pkg.get('repository', {})
                    stars = pkg.get('stars', 0)
                    github_url = ''

                    # Extract GitHub URL if available
                    links = pkg.get('links', [])
                    for link in links:
                        if 'github.com' in link.get('url', ''):
                            github_url = link['url']
                            break

                    if name and description and repository.get('kind') == 'helm':
                        tool = Tool(
                            name=clean_text(name),
                            description=clean_text(description),
                            category=category,
                            importance='Recommended' if stars > 50 else 'Optional',
                            isOpenSource=True,
                            url=f"https://artifacthub.io/packages/helm/{repository.get('name', '')}/{name}",
                            githubUrl=github_url,
                            stars=stars,
                            language='Helm',
                            topics=['helm', 'kubernetes', category.lower()]
                        )

                        if is_valid_tool(tool):
                            print(f"Added Helm {category} tool: {tool.name}")
                            tools.append(tool)

                    sleep_between_requests(1, 2)  # Rate limiting
            else:
                print(f"ArtifactHub API request failed for Helm charts with status code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"Error making ArtifactHub API request for Helm charts: {str(e)}")

    except Exception as e:
        print(f"Error in extract_helm_tools: {str(e)}")

    return tools

def extract_apiwatch_tools():
    """Extract API Gateway and Management tools from APIWatch"""
    tools = []
    try:
        # APIWatch data source
        response = requests.get('https://apiwatch.io/api/tools', timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data:
                try:
                    # Determine category based on tool type
                    category = 'API Gateway' if 'gateway' in item.get('type', '').lower() else 'API Management'

                    tool = Tool(
                        name=item.get('name', ''),
                        description=clean_text(item.get('description', '')),
                        category=category,
                        importance='Optional',  # Will be updated if GitHub info is found
                        isOpenSource=item.get('isOpenSource', True),
                        url=item.get('website', ''),
                        githubUrl=item.get('github', ''),
                        stars=0,  # Will be updated if GitHub info is found
                        language=item.get('primaryLanguage', ''),
                        topics=['api', 'api-gateway', 'api-management']
                    )

                    # Update GitHub information if available
                    if tool.githubUrl and 'github.com' in tool.githubUrl:
                        repo_path = tool.githubUrl.split('github.com/')[-1]
                        try:
                            result = subprocess.run(
                                ['gh', 'api', f'repos/{repo_path}'],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            repo_data = json.loads(result.stdout)
                            tool.stars = repo_data.get('stargazers_count', 0)
                            tool.importance = determine_importance(tool.stars)
                        except Exception as e:
                            print(f"Error fetching GitHub data for {tool.githubUrl}: {str(e)}")

                    if is_valid_tool(tool):
                        print(f"Added APIWatch tool: {tool.name} ({tool.category})")
                        tools.append(tool)

                except Exception as e:
                    print(f"Error processing APIWatch tool: {str(e)}")
                    continue

    except Exception as e:
        print(f"Error fetching APIWatch data: {str(e)}")

    return tools

def extract_layer5_tools():
    """Extract Service Mesh tools from Layer5"""
    tools = []
    try:
        # Layer5 Service Mesh Landscape data
        response = requests.get('https://layer5.io/api/landscape', timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data:
                try:
                    tool = Tool(
                        name=item.get('name', ''),
                        description=clean_text(item.get('description', '')),
                        category='Service Mesh',
                        importance='Optional',  # Will be updated if GitHub info is found
                        isOpenSource=item.get('opensource', True),
                        url=item.get('website', ''),
                        githubUrl=item.get('github', ''),
                        stars=0,  # Will be updated if GitHub info is found
                        language=item.get('language', ''),
                        topics=['service-mesh', 'mesh', 'proxy']
                    )


                    # Update GitHub information if available
                    if tool.githubUrl and 'github.com' in tool.githubUrl:
                        repo_path = tool.githubUrl.split('github.com/')[-1]
                        try:
                            result = subprocess.run(
                                ['gh', 'api', f'repos/{repo_path}'],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            repo_data = json.loads(result.stdout)
                            tool.stars = repo_data.get('stargazers_count', 0)
                            tool.importance = determine_importance(tool.stars)
                        except Exception as e:
                            print(f"Error fetching GitHub data for {tool.githubUrl}: {str(e)}")

                    if is_valid_tool(tool):
                        print(f"Added Layer5 tool: {tool.name} ({tool.category})")
                        tools.append(tool)

                except Exception as e:
                    print(f"Error processing Layer5 tool: {str(e)}")
                    continue

    except Exception as e:
        print(f"Error fetching Layer5 data: {str(e)}")

    return tools

def extract_git_tools():
    """Extract Version Control tools from specialized sources"""
    tools = []
    try:
        # Git-related tools from GitHub API
        search_queries = [
            'git gui client stars:>100',
            'git extension stars:>100',
            'git workflow tool stars:>100',
            'version control system stars:>100',
            'git hosting platform stars:>100'
        ]

        for query in search_queries:
            try:
                print(f"\nSearching for Version Control tools: {query}")
                repos = run_github_query(query)

                for repo in repos:
                    try:
                        # Skip archived and private repositories
                        if repo.get('archived', False) or repo.get('private', True):
                            continue

                        # Determine importance based on stars
                        stars = repo.get('stargazers_count', 0)
                        if stars >= 5000:
                            importance = 'Essential'
                        elif stars >= 1000:
                            importance = 'Recommended'
                        else:
                            importance = 'Optional'

                        tool = Tool(
                            name=repo.get('name', ''),
                            description=clean_text(repo.get('description', '')),
                            category='Version Control',
                            importance=importance,
                            isOpenSource=not repo.get('private', True),
                            url=repo.get('homepage', '') or repo.get('html_url', ''),
                            githubUrl=repo.get('html_url', ''),
                            stars=stars,
                            language=repo.get('language'),
                            topics=['git', 'version-control', 'source-control']
                        )

                        if is_valid_tool(tool):
                            print(f"Added Version Control tool: {tool.name}")
                            tools.append(tool)

                        sleep_between_requests(1, 2)

                    except Exception as e:
                        print(f"Error processing repository: {str(e)}")
                        continue

                sleep_between_requests(2, 4)

            except Exception as e:
                print(f"Error processing query {query}: {str(e)}")
                continue

    except Exception as e:
        print(f"Error in extract_git_tools: {str(e)}")

    return tools

def extract_generic_tools():
    """Extract tools from specialized sources focusing on underrepresented categories"""
    tools = []
    try:
        # Enhanced source queries for underrepresented categories
        sources = {
            'API Gateway': [
                ('https://api.github.com/search/repositories', {
                    'q': 'topic:api-gateway stars:>100 language:go language:java language:python NOT topic:tutorial',
                    'sort': 'stars',
                    'order': 'desc'
                }),
                ('https://raw.githubusercontent.com/api7/awesome-api-gateway/master/README.md', None),
                ('https://raw.githubusercontent.com/yosriady/awesome-api-gateway/master/README.md', None)
            ],
            'API Management': [
                ('https://api.github.com/search/repositories', {
                    'q': 'topic:api-management stars:>100 language:typescript language:javascript language:python NOT topic:tutorial',
                    'sort': 'stars',
                    'order': 'desc'
                }),
                ('https://raw.githubusercontent.com/APIs-guru/awesome-openapi3/master/README.md', None),
                ('https://raw.githubusercontent.com/mermade/awesome-openapi3/master/README.md', None)
            ],
            'Service Mesh': [
                ('https://api.github.com/search/repositories', {
                    'q': 'topic:service-mesh stars:>100 language:go NOT topic:tutorial',
                    'sort': 'stars',
                    'order': 'desc'
                }),
                ('https://raw.githubusercontent.com/servicemesher/awesome-servicemesh/master/README.md', None),
                ('https://raw.githubusercontent.com/layer5io/layer5/master/README.md', None)
            ],
            'Version Control': [
                ('https://api.github.com/search/repositories', {
                    'q': 'topic:version-control stars:>100 NOT topic:learning NOT topic:tutorial',
                    'sort': 'stars',
                    'order': 'desc'
                }),
                ('https://raw.githubusercontent.com/viatsko/awesome-vscode/master/README.md', None),
                ('https://raw.githubusercontent.com/stevemao/awesome-git-addons/master/README.md', None)
            ]
        }

        for category, source_list in sources.items():
            for source, params in source_list:
                try:
                    print(f"\nExtracting {category} tools from: {source}")
                    if 'api.github.com' in source:
                        repos = run_github_query(params['q'])
                        for repo in repos:
                            try:
                                github_info = extract_github_info(repo.get('full_name', ''))
                                if github_info:
                                    tool = Tool(
                                        name=repo.get('name', ''),
                                        description=clean_text(repo.get('description', '')),
                                        category=category,
                                        importance=determine_importance(github_info.get('stargazers_count', 0)),
                                        isOpenSource=not repo.get('private', True),
                                        url=repo.get('homepage', '') or repo.get('html_url', ''),
                                        githubUrl=repo.get('html_url', ''),
                                        stars=github_info.get('stargazers_count', 0),
                                        language=repo.get('language', ''),
                                        topics=github_info.get('topics', [])
                                    )
                                    if is_valid_tool(tool):
                                        print(f"Added {category} tool: {tool.name}")
                                        tools.append(tool)
                            except Exception as e:
                                print(f"Error processing repository: {str(e)}")
                                continue
                    else:
                        response = requests.get(source, timeout=10)
                        if response.status_code == 200:
                            content = response.text
                            github_urls = re.findall(r'https://github.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+', content)
                            for url in github_urls:
                                try:
                                    github_info = extract_github_info(url.replace('https://github.com/', ''))
                                    if github_info:
                                        tool = Tool(
                                            name=github_info.get('name', ''),
                                            description=clean_text(github_info.get('description', '')),
                                            category=category,
                                            importance=determine_importance(github_info.get('stargazers_count', 0)),
                                            isOpenSource=not github_info.get('private', True),
                                            url=github_info.get('homepage', '') or url,
                                            githubUrl=url,
                                            stars=github_info.get('stargazers_count', 0),
                                            language=github_info.get('language', ''),
                                            topics=github_info.get('topics', [])
                                        )
                                        if is_valid_tool(tool):
                                            print(f"Added {category} tool from awesome list: {tool.name}")
                                            tools.append(tool)
                                except Exception as e:
                                    print(f"Error processing GitHub URL {url}: {str(e)}")
                                    continue

                    sleep_between_requests(2, 4)

                except Exception as e:
                    print(f"Error processing source {source}: {str(e)}")
                    continue

    except Exception as e:
        print(f"Error in extract_generic_tools: {str(e)}")

    return tools


def extract_aws_tools(content: str, category: str) -> List[Tool]:
    """Extract tools from AWS Marketplace"""
    tools = []
    try:
        # Extract product links
        product_links = re.findall(r'href="(/marketplace/pp/[^"]+)"', content)
        for link in product_links[:5]:  # Process top 5 results
            try:
                full_url = f"https://aws.amazon.com{link}"
                if browser_navigate(full_url):
                    product_content = browser_view()
                    if product_content:
                        name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', product_content)
                        desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', product_content)
                        if name_match and desc_match:
                            tool = Tool(
                                name=clean_text(name_match.group(1)),
                                description=clean_text(desc_match.group(1)),
                                category=category,
                                importance='Recommended',
                                isOpenSource=False,
                                url=full_url,
                                githubUrl='',
                                stars=0,
                                language='',
                                topics=[category.lower(), 'aws', 'cloud']
                            )
                            if is_valid_tool(tool):
                                print(f"Added AWS {category} tool: {tool.name}")
                                tools.append(tool)
            except Exception as e:
                print(f"Error processing AWS product {link}: {str(e)}")
            sleep_between_requests(1, 2)
    except Exception as e:
        print(f"Error in extract_aws_tools: {str(e)}")
    return tools

def extract_azure_tools(content: str, category: str) -> List[Tool]:
    """Extract tools from Azure Marketplace"""
    tools = []
    try:
        # Extract product links
        product_links = re.findall(r'href="(/marketplace/[^"]+)"', content)
        for link in product_links[:5]:  # Process top 5 results
            try:
                full_url = f"https://azuremarketplace.microsoft.com{link}"
                if browser_navigate(full_url):
                    product_content = browser_view()
                    if product_content:
                        name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', product_content)
                        desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', product_content)
                        if name_match and desc_match:
                            tool = Tool(
                                name=clean_text(name_match.group(1)),
                                description=clean_text(desc_match.group(1)),
                                category=category,
                                importance='Recommended',
                                isOpenSource=False,
                                url=full_url,
                                githubUrl='',
                                stars=0,
                                language='',
                                topics=[category.lower(), 'azure', 'cloud']
                            )
                            if is_valid_tool(tool):
                                print(f"Added Azure {category} tool: {tool.name}")
                                tools.append(tool)
            except Exception as e:
                print(f"Error processing Azure product {link}: {str(e)}")
            sleep_between_requests(1, 2)
    except Exception as e:
        print(f"Error in extract_azure_tools: {str(e)}")
    return tools

def extract_gcp_tools(content: str, category: str) -> List[Tool]:
    """Extract tools from Google Cloud Marketplace"""
    tools = []
    try:
        # Extract product links
        product_links = re.findall(r'href="(/marketplace/product/[^"]+)"', content)
        for link in product_links[:5]:  # Process top 5 results
            try:
                full_url = f"https://console.cloud.google.com{link}"
                if browser_navigate(full_url):
                    product_content = browser_view()
                    if product_content:
                        name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', product_content)
                        desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', product_content)
                        if name_match and desc_match:
                            tool = Tool(
                                name=clean_text(name_match.group(1)),
                                description=clean_text(desc_match.group(1)),
                                category=category,
                                importance='Recommended',
                                isOpenSource=False,
                                url=full_url,
                                githubUrl='',
                                stars=0,
                                language='',
                                topics=[category.lower(), 'gcp', 'cloud']
                            )
                            if is_valid_tool(tool):
                                print(f"Added GCP {category} tool: {tool.name}")
                                tools.append(tool)
            except Exception as e:
                print(f"Error processing GCP product {link}: {str(e)}")
            sleep_between_requests(1, 2)
    except Exception as e:
        print(f"Error in extract_gcp_tools: {str(e)}")
    return tools


def browser_navigate(url: str, max_attempts: int = 3, initial_delay: int = 10) -> bool:
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Navigation attempt {attempt}/{max_attempts} to: {url}")
            print(f'<navigate_browser url="{url}"/>')

            sleep_between_requests(initial_delay, initial_delay + 5)

            print('<screenshot_browser>\nChecking if page loaded correctly\n</screenshot_browser>')

            spa_check = """
                return {
                    ready: document.readyState === 'complete',
                    noLoader: !document.querySelector('[class*="loading"],[class*="spinner"]'),
                    hasContent: document.body.textContent.length > 1000,
                    mainContent: !!document.querySelector('main,article,#content,.content'),
                    networkIdle: !window.fetch || window.performance.getEntriesByType('resource').length > 0
                };
            """

            for validation_attempt in range(1, 4):
                print(f'<view_browser reload_window="True"/>')

                print('<scroll_down_browser/>')
                sleep_between_requests(2, 3)
                print('<scroll_up_browser/>')
                sleep_between_requests(1, 2)
                print('<scroll_down_browser/>')

                print(f'<run_javascript_browser>{spa_check}</run_javascript_browser>')

                content = browser_view()
                if validate_page_content(content, url):
                    print(f"Successfully loaded page on validation attempt {validation_attempt}")
                    return True

                if validation_attempt < 3:
                    print(f"Content validation failed on attempt {validation_attempt}, retrying...")
                    sleep_between_requests(3, 5)
                else:
                    print("Failed to get valid content after all retries")

            print(f"Page load attempt {attempt} failed - retrying...")
            if attempt < max_attempts:
                delay = attempt * 15
                print(f"Retry attempt {attempt + 1}/{max_attempts} after {delay}s delay...")
                sleep_between_requests(delay, delay + 5)

        except Exception as e:
            print(f"Error during navigation attempt {attempt}: {str(e)}")
            if attempt < max_attempts:
                sleep_between_requests(10, 15)

    print(f"Failed to load {url} after {max_attempts} attempts")
    return False

def browser_view() -> str:
    try:
        print('<view_browser reload_window="True"/>')
        return "BROWSER_CONTENT"  # This will be replaced by the actual content
    except Exception as e:
        print(f"Error viewing browser content: {str(e)}")
        return ""

def run_javascript_browser(script: str) -> None:
    """Execute JavaScript in the browser"""
    try:
        print(f'<run_javascript_browser>{script}</run_javascript_browser>')
    except Exception as e:
        print(f"Error executing JavaScript: {str(e)}")
        return None

def validate_page_content(content: str, url: str) -> bool:
    if not content:
        return False

    error_indicators = [
        'page not found',
        '404 error',
        'access denied',
        'forbidden',
        'too many requests',
        'rate limit exceeded',
        'loading...',
        'please wait'
    ]

    content_lower = content.lower()
    for indicator in error_indicators:
        if indicator in content_lower:
            print(f"Found error indicator: {indicator}")
            return False

    if len(content) < 500:
        print("Content too short, likely not fully loaded")
        return False

    readiness_check = """
        return {
            documentReady: document.readyState === 'complete',
            hasContent: document.body.textContent.length > 1000,
            noSpinner: !document.querySelector('[class*="spinner"],[class*="loading"]'),
            hasMainContent: document.querySelector('main,article,#content,.content') !== null
        };
    """
    run_javascript_browser(readiness_check)

    if 'docker.com' in url:
        return 'repository' in content_lower or 'docker image' in content_lower
    elif 'artifacthub.io' in url:
        return 'package' in content_lower or 'artifact' in content_lower
    elif 'helm.sh' in url:
        return 'chart' in content_lower or 'helm' in content_lower
    elif 'rapidapi.com' in url:
        return 'api' in content_lower and ('marketplace' in content_lower or 'hub' in content_lower)
    elif 'postman.com' in url:
        return 'collection' in content_lower or 'api' in content_lower
    elif 'swaggerhub.com' in url:
        return 'swagger' in content_lower or 'api' in content_lower

    content_indicators = [
        ('<div', 10),
        ('<script', 2),
        ('class=', 15),
        ('<a', 5)
    ]

    for indicator, min_count in content_indicators:
        if content.count(indicator) < min_count:
            print(f"Insufficient {indicator} elements")
            return False

    return True
def wait_for_element(content: str, element_id: str, timeout: int = 30, check_interval: int = 2) -> bool:
    """Wait for element to appear in page content with improved validation"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Check for element in current content
            if element_id in content:
                return True

            # Scroll and check again
            print("<scroll_down_browser/>")
            time.sleep(1)
            print("<scroll_up_browser/>")
            time.sleep(1)

            # Get fresh content
            content = browser_view(reload=True)
            if not content:
                print("No content available during element wait")
                time.sleep(check_interval)
                continue

            print(f"Waiting for element '{element_id}', time remaining: {int(timeout - (time.time() - start_time))}s")
            time.sleep(check_interval)

        except Exception as e:
            print(f"Error during element wait: {str(e)}")
            time.sleep(check_interval)

    print(f"Element '{element_id}' not found after {timeout} seconds")
    return False

def scrape_cloud_marketplaces() -> List[Tool]:
    """Scrape cloud marketplaces with enhanced focus on underrepresented categories"""
    tools = []

    # Priority categories and their marketplace-specific search terms
    priority_categories = {
        'API Gateway': {
            'aws': ['api-gateway', 'api-management', 'api-proxy'],
            'azure': ['api-management', 'api-gateway', 'api-service'],
            'gcp': ['apigee', 'cloud-endpoints', 'api-gateway']
        },
        'API Management': {
            'aws': ['api-management', 'api-monitoring', 'api-analytics'],
            'azure': ['api-management', 'api-portal', 'api-analytics'],
            'gcp': ['api-management', 'api-analytics', 'api-security']
        },
        'Service Mesh': {
            'aws': ['service-mesh', 'app-mesh', 'mesh-networking'],
            'azure': ['service-mesh', 'service-fabric-mesh', 'mesh-networking'],
            'gcp': ['service-mesh', 'anthos-mesh', 'istio']
        },
        'Version Control': {
            'aws': ['version-control', 'code-repository', 'git-service'],
            'azure': ['version-control', 'repos', 'git-hosting'],
            'gcp': ['version-control', 'cloud-source', 'git-repository']
        }
    }

    try:
        # AWS Marketplace
        print("\nScraping AWS Marketplace...")
        for category, terms in priority_categories.items():
            for term in terms['aws']:
                try:
                    url = f"https://aws.amazon.com/marketplace/search/results?searchTerms={term}"
                    if browser_navigate(url):
                        content = browser_view()
                        tools.extend(extract_aws_tools(content, category))
                    sleep_between_requests(2, 3)
                except Exception as e:
                    print(f"Error scraping AWS Marketplace for {term}: {str(e)}")

        # Azure Marketplace
        print("\nScraping Azure Marketplace...")
        for category, terms in priority_categories.items():
            for term in terms['azure']:
                try:
                    url = f"https://azuremarketplace.microsoft.com/en-us/marketplace/apps?search={term}"
                    if browser_navigate(url):
                        content = browser_view()
                        tools.extend(extract_azure_tools(content, category))
                    sleep_between_requests(2, 3)
                except Exception as e:
                    print(f"Error scraping Azure Marketplace for {term}: {str(e)}")

        # Google Cloud Marketplace
        print("\nScraping Google Cloud Marketplace...")
        for category, terms in priority_categories.items():
            for term in terms['gcp']:
                try:
                    url = f"https://console.cloud.google.com/marketplace/browse?filter=category:developer-tools&q={term}"
                    if browser_navigate(url):
                        content = browser_view()
                        tools.extend(extract_gcp_tools(content, category))
                    sleep_between_requests(2, 3)
                except Exception as e:
                    print(f"Error scraping Google Cloud Marketplace for {term}: {str(e)}")

    except Exception as e:
        print(f"Error in scrape_cloud_marketplaces: {str(e)}")

    print(f"Collected {len(tools)} tools from cloud marketplaces")
    return tools

def load_checkpoint() -> List[Tool]:
    """Load tools from checkpoint file with error handling"""
    try:
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r') as f:
                data = json.load(f)
                return [Tool(**tool_dict) for tool_dict in data]
    except Exception as e:
        print(f"Error loading checkpoint: {e}")
        # Backup corrupted checkpoint if it exists
        if os.path.exists(CHECKPOINT_FILE):
            backup_file = f"{CHECKPOINT_FILE}.bak.{int(time.time())}"
            os.rename(CHECKPOINT_FILE, backup_file)
            print(f"Backed up corrupted checkpoint to {backup_file}")
    return []

def save_checkpoint(tools: List[Tool]) -> None:
    """Save tools to checkpoint file with error handling"""
    try:
        # Create backup of existing checkpoint if it exists
        if os.path.exists(CHECKPOINT_FILE):
            backup_file = f"{CHECKPOINT_FILE}.bak.{int(time.time())}"
            os.rename(CHECKPOINT_FILE, backup_file)
            print(f"Created backup of existing checkpoint: {backup_file}")

        # Save new checkpoint
        tools_data = [t.to_dict() for t in tools]
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(tools_data, f, indent=2)
        print(f"Saved checkpoint with {len(tools)} tools")

    except Exception as e:
        print(f"Error saving checkpoint: {e}")

def merge_tools(existing: Tool, new: Tool) -> Tool:
    """Merge tool data preserving existing information when available"""
    return Tool(
        name=existing.name,
        description=existing.description or new.description,
        category=existing.category or new.category,
        importance=existing.importance or new.importance,
        isOpenSource=existing.isOpenSource,
        url=existing.url or new.url,
        documentationUrl=existing.documentationUrl or new.documentationUrl,
        githubUrl=existing.githubUrl or new.githubUrl,
        tags=list(set(existing.tags or []) | set(new.tags or []))
    )

def main(verbose: bool = True) -> None:
    """Main function to orchestrate the tool collection process"""
    try:
        print("Starting tool collection process...")

        # Load existing tools from checkpoint into dictionary
        existing_tools = {(t.name.lower(), t.url, t.githubUrl): t for t in load_checkpoint()}
        if existing_tools:
            print(f"Loaded {len(existing_tools)} tools from checkpoint")

        def merge_new_tools(existing_dict, new_tools):
            result = existing_dict.copy()
            for tool in new_tools:
                key = (tool.name.lower(), tool.url, tool.githubUrl)
                if key in result:
                    result[key] = merge_tools(result[key], tool)
                else:
                    result[key] = tool
            return list(result.values())

        # Start with most reliable sources first
        print("\nCollecting tools from CNCF landscape...")
        cncf_tools = scrape_cncf_landscape()
        tools = merge_new_tools(existing_tools, cncf_tools)
        existing_tools = {(t.name.lower(), t.url, t.githubUrl): t for t in tools}
        print(f"Collected {len(cncf_tools)} tools from CNCF landscape")
        save_checkpoint(tools)  # Save progress after each source

        print("\nCollecting tools from GitHub topics...")
        github_tools = scrape_github_topics()
        tools = merge_new_tools(existing_tools, github_tools)
        existing_tools = {(t.name.lower(), t.url, t.githubUrl): t for t in tools}
        print(f"Collected {len(github_tools)} tools from GitHub topics")
        save_checkpoint(tools)

        print("\nCollecting tools from package registries...")
        registry_tools = scrape_package_registries()
        tools = merge_new_tools(existing_tools, registry_tools)
        existing_tools = {(t.name.lower(), t.url, t.githubUrl): t for t in tools}
        print(f"Collected {len(registry_tools)} tools from package registries")
        save_checkpoint(tools)

        print("\nCollecting tools from additional registries...")
        additional_tools = scrape_additional_registries()
        tools = merge_new_tools(existing_tools, additional_tools)
        existing_tools = {(t.name.lower(), t.url, t.githubUrl): t for t in tools}
        print(f"Collected {len(additional_tools)} tools from additional registries")
        save_checkpoint(tools)

        print("\nCollecting tools from awesome lists...")
        awesome_tools = scrape_awesome_lists()
        tools = merge_new_tools(existing_tools, awesome_tools)
        existing_tools = {(t.name.lower(), t.url, t.githubUrl): t for t in tools}
        print(f"Collected {len(awesome_tools)} tools from awesome lists")
        save_checkpoint(tools)

        # Try marketplace scraping last
        print("\nCollecting tools from cloud marketplaces...")
        try:
            marketplace_tools = scrape_cloud_marketplaces()
            tools = merge_new_tools(existing_tools, marketplace_tools)
            existing_tools = {(t.name.lower(), t.url, t.githubUrl): t for t in tools}
            print(f"Collected {len(marketplace_tools)} tools from cloud marketplaces")
            save_checkpoint(tools)
        except Exception as e:
            print(f"Error collecting marketplace tools: {str(e)}")
            print("Continuing with tools from other sources...")

        # Final tools list is already deduplicated through dictionary-based tracking
        tools_data = [t.to_dict() for t in tools]
        print(f"\nTotal unique tools collected: {len(tools)}")

        # Save category statistics
        categories = {}
        for tool in tools:
            categories[tool.category] = categories.get(tool.category, 0) + 1

        print("\nCategory distribution:")
        for category, count in categories.items():
            print(f"{category}: {count} tools")

        with open('category_stats.json', 'w') as f:
            json.dump(categories, f, indent=2)

        with open('tools.json', 'w') as f:
            json.dump(tools_data, f, indent=2)

        print("\nTool collection completed successfully!")
        print(f"Results saved to tools.json and category_stats.json")

    except Exception as e:
        print(f"Error in main process: {str(e)}")
        raise

if __name__ == '__main__':
    main()

