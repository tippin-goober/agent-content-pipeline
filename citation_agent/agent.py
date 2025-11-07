#!/usr/bin/env python3
"""
Citation Agent - Automatic Citation and Bibliography Generation
Integrates with research data to add proper citations to content
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class CitationAgent:
    """Agent for adding citations to content based on research data"""
    
    def __init__(self):
        self.citation_styles = {
            "apa": self._format_apa_citation,
            "mla": self._format_mla_citation,
            "chicago": self._format_chicago_citation
        }
        self.default_style = "apa"
    
    def identify_claims_needing_citations(self, content: str) -> List[Dict[str, Any]]:
        """Identify claims, statistics, and statements that need citations"""
        claims = []
        
        # Patterns for content that typically needs citations
        citation_patterns = [
            # Statistics and percentages
            (r'([^.]*\b\d+(?:\.\d+)?%[^.]*)', 'statistic'),
            # Dollar amounts and financial data
            (r'([^.]*\$\d+(?:[\d,]*)?(?:\.\d+)?\s*(?:billion|million|thousand|k)?[^.]*)', 'financial'),
            # Growth and change statistics
            (r'([^.]*(?:grew|increased|decreased|rose|fell|improved|declined)\s+(?:by\s+)?\d+(?:\.\d+)?%[^.]*)', 'growth'),
            # Market size and industry data
            (r'([^.]*(?:market|industry|sector)\s+(?:size|value|worth)[^.]*\$?\d+[^.]*)', 'market_data'),
            # Research findings and studies
            (r'([^.]*(?:study|research|survey|report|analysis)\s+(?:shows|found|indicates|reveals|suggests)[^.]*)', 'research_finding'),
            # Expert opinions and quotes
            (r'([^.]*(?:according to|experts|analysts|researchers)\s+[^.]*)', 'expert_opinion'),
            # Specific dates and timeframes
            (r'([^.]*(?:in\s+20\d{2}|during\s+20\d{2}|by\s+20\d{2})[^.]*)', 'temporal_claim'),
            # Comparative claims
            (r'([^.]*(?:compared to|versus|more than|less than|higher than|lower than)[^.]*)', 'comparison'),
            # Definitive statements about trends
            (r'([^.]*(?:trend|trending|popular|leading|dominant|fastest-growing)[^.]*)', 'trend_claim')
        ]
        
        claim_id = 1
        for pattern, claim_type in citation_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                claim_text = match.group(1).strip()
                if len(claim_text) > 20 and claim_text not in [c['text'] for c in claims]:
                    claims.append({
                        'id': claim_id,
                        'text': claim_text,
                        'type': claim_type,
                        'start_pos': match.start(1),
                        'end_pos': match.end(1),
                        'needs_citation': True
                    })
                    claim_id += 1
        
        # Sort by position in text
        claims.sort(key=lambda x: x['start_pos'])
        
        return claims
    
    def match_claims_to_sources(self, claims: List[Dict], research_data: Dict) -> List[Dict]:
        """Match identified claims to research sources"""
        matched_claims = []
        
        # Extract research content for matching
        research_content = []
        
        # Add statistics
        for stat in research_data.get('statistics', []):
            research_content.append({
                'text': stat,
                'type': 'statistic',
                'source_type': 'research_statistic'
            })
        
        # Add expert quotes
        for quote in research_data.get('expert_quotes', []):
            research_content.append({
                'text': quote,
                'type': 'expert_opinion',
                'source_type': 'expert_quote'
            })
        
        # Add research results content
        for result in research_data.get('results', []):
            if 'answer' in result:
                research_content.append({
                    'text': result['answer'],
                    'type': 'research_finding',
                    'source_type': 'research_result',
                    'query': result.get('query', '')
                })
        
        # Match claims to research content
        for claim in claims:
            best_match = self._find_best_source_match(claim, research_content)
            if best_match:
                claim['matched_source'] = best_match
                claim['confidence'] = best_match.get('confidence', 0.5)
            else:
                claim['matched_source'] = None
                claim['confidence'] = 0.0
            
            matched_claims.append(claim)
        
        return matched_claims
    
    def _find_best_source_match(self, claim: Dict, research_content: List[Dict]) -> Optional[Dict]:
        """Find the best matching research source for a claim"""
        claim_text = claim['text'].lower()
        claim_type = claim['type']
        best_match = None
        best_score = 0.0
        
        for source in research_content:
            source_text = source['text'].lower()
            score = 0.0
            
            # Type matching bonus
            if claim_type == source['type']:
                score += 0.3
            
            # Extract key terms from claim
            claim_keywords = self._extract_keywords(claim_text)
            source_keywords = self._extract_keywords(source_text)
            
            # Keyword overlap scoring
            common_keywords = set(claim_keywords) & set(source_keywords)
            if claim_keywords:
                keyword_score = len(common_keywords) / len(claim_keywords)
                score += keyword_score * 0.4
            
            # Specific pattern matching
            if claim_type == 'statistic':
                # Look for matching numbers
                claim_numbers = re.findall(r'\d+(?:\.\d+)?', claim_text)
                source_numbers = re.findall(r'\d+(?:\.\d+)?', source_text)
                if claim_numbers and source_numbers:
                    if any(num in source_numbers for num in claim_numbers):
                        score += 0.3
            
            # Content similarity (simple overlap)
            claim_words = set(claim_text.split())
            source_words = set(source_text.split())
            if len(claim_words) > 0:
                overlap = len(claim_words & source_words) / len(claim_words)
                score += overlap * 0.2
            
            # Update best match
            if score > best_score and score > 0.3:  # Minimum threshold
                best_score = score
                best_match = {
                    **source,
                    'confidence': score
                }
        
        return best_match
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'this', 'that', 'these', 'those', 'there', 'their', 'they', 'them'
        }
        
        # Extract words (3+ characters, not in stop words)
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        keywords = [w for w in words if w not in stop_words]
        
        return keywords
    
    def _select_best_source(self, sources: List[str]) -> Optional[str]:
        """Select the best source from a list (prefer URLs over text snippets)"""
        urls = []
        organizations = []
        other_sources = []
        
        for source in sources:
            if source.startswith(('http://', 'https://')):
                urls.append(source)
            elif any(org in source.lower() for org in [
                'mckinsey', 'deloitte', 'bcg', 'boston consulting', 'gartner', 
                'forrester', 'pwc', 'harvard', 'mit', 'stanford', 'wsj', 
                'wall street', 'new york times', 'financial times', 'forbes', 
                'bloomberg', 'reuters', 'techcrunch', 'wired', 'economist'
            ]):
                organizations.append(source)
            else:
                other_sources.append(source)
        
        # Prefer URLs, then known organizations, then other sources
        if urls:
            return urls[0]
        elif organizations:
            return organizations[0]
        elif other_sources:
            return other_sources[0]
        
        return None
    
    def _extract_source_from_text(self, text: str) -> Optional[str]:
        """Extract source information from text content"""
        # Look for URLs in text
        url_pattern = r'https?://[^\s\)]+[^\s\.\,\)\]]'
        urls = re.findall(url_pattern, text)
        if urls:
            return urls[0]
        
        # Look for organization mentions
        org_patterns = [
            r'(?:according to |source: |via |from )?([A-Za-z\s]+(?:McKinsey|Deloitte|BCG|Boston Consulting|Gartner|Forrester|PwC|Harvard|MIT|Stanford))[^,\n.]*',
            r'(?:according to |source: |via |from )?([A-Za-z\s]*(?:Wall Street Journal|WSJ|New York Times|Financial Times|Forbes|Bloomberg|Reuters|TechCrunch|Wired|Economist))[^,\n.]*'
        ]
        
        for pattern in org_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return None
    
    def _clean_source_title(self, source: str) -> str:
        """Clean and format source titles for citations"""
        if not source:
            return "Unknown Source"
        
        # Remove common URL artifacts
        source = re.sub(r'^www\.', '', source)
        source = re.sub(r'\.com$|\.org$|\.net$|\.edu$|\.gov$', '', source)
        
        # Handle domain-based sources
        domain_mappings = {
            'mckinsey': 'McKinsey & Company',
            'deloitte': 'Deloitte',
            'bcg': 'Boston Consulting Group',
            'gartner': 'Gartner',
            'forrester': 'Forrester Research',
            'pwc': 'PricewaterhouseCoopers',
            'harvard': 'Harvard Business Review',
            'mit': 'MIT Technology Review',
            'stanford': 'Stanford Research',
            'wsj': 'Wall Street Journal',
            'nytimes': 'New York Times',
            'ft': 'Financial Times',
            'forbes': 'Forbes',
            'bloomberg': 'Bloomberg',
            'reuters': 'Reuters',
            'techcrunch': 'TechCrunch',
            'wired': 'Wired',
            'economist': 'The Economist'
        }
        
        source_lower = source.lower()
        for key, value in domain_mappings.items():
            if key in source_lower:
                return value
        
        # Capitalize first letters and clean up
        words = source.replace('-', ' ').replace('_', ' ').split()
        cleaned_words = []
        
        for word in words:
            if len(word) > 2:  # Skip very short words
                cleaned_words.append(word.capitalize())
        
        result = ' '.join(cleaned_words)
        
        # Fallback for very short or unclear sources
        if len(result) < 3:
            return "Industry Research"
        
        return result[:50]  # Limit length
    
    def format_citations(self, matched_claims: List[Dict], research_data: Dict, style: str = "apa") -> Dict[str, Any]:
        """Format claims with citations and create bibliography"""
        citation_formatter = self.citation_styles.get(style, self.citation_styles[self.default_style])
        
        # Create bibliography entries
        bibliography = []
        citation_map = {}
        citation_counter = 1
        
        # Get unique sources
        unique_sources = set()
        for claim in matched_claims:
            if claim.get('matched_source'):
                source_key = self._create_source_key(claim['matched_source'], research_data)
                if source_key and source_key not in unique_sources:
                    unique_sources.add(source_key)
                    
                    bib_entry = citation_formatter(source_key, citation_counter)
                    bibliography.append(bib_entry)
                    citation_map[source_key] = citation_counter
                    citation_counter += 1
        
        # Add citations to claims
        cited_claims = []
        for claim in matched_claims:
            if claim.get('matched_source') and claim['confidence'] > 0.3:
                source_key = self._create_source_key(claim['matched_source'], research_data)
                if source_key in citation_map:
                    claim['citation_number'] = citation_map[source_key]
                    claim['has_citation'] = True
                else:
                    claim['has_citation'] = False
            else:
                claim['has_citation'] = False
            
            cited_claims.append(claim)
        
        return {
            'cited_claims': cited_claims,
            'bibliography': bibliography,
            'citation_map': citation_map
        }
    
    def _create_source_key(self, matched_source: Dict, research_data: Dict) -> Optional[str]:
        """Create a unique key for a source with improved URL extraction"""
        # Try to find the original source from research data
        for result in research_data.get('results', []):
            if 'answer' in result and matched_source['text'] in result['answer']:
                sources = result.get('sources', [])
                if sources:
                    # Find the best source (prefer URLs)
                    best_source = self._select_best_source(sources)
                    if best_source:
                        return best_source
        
        # Try to extract URLs or sources from the matched source text itself
        extracted_source = self._extract_source_from_text(matched_source.get('text', ''))
        if extracted_source:
            return extracted_source
        
        # Fallback to research sources
        sources = research_data.get('sources', [])
        if sources:
            best_source = self._select_best_source(sources)
            if best_source:
                return best_source
        
        # Last resort - create generic source with some context
        source_type = matched_source.get('source_type', 'research')
        if source_type == 'expert_quote':
            return "Expert Industry Analysis"
        elif source_type == 'research_statistic':
            return "Industry Research Data"
        else:
            return "Market Research Report"
    
    def _format_apa_citation(self, source: str, citation_num: int) -> Dict[str, Any]:
        """Format source in APA style with improved title extraction"""
        if source.startswith('http'):
            # URL source
            parsed = urlparse(source)
            domain = parsed.netloc.replace('www.', '')
            
            # Clean up domain name for better titles
            clean_title = self._clean_source_title(domain)
            
            return {
                'id': citation_num,
                'source': source,
                'formatted': f"{clean_title}. Retrieved {datetime.now().strftime('%B %d, %Y')}, from {source}",
                'url': source,
                'accessed': datetime.now().strftime('%Y-%m-%d'),
                'style': 'apa',
                'title': clean_title
            }
        else:
            # Text source - try to extract meaningful title
            clean_title = self._clean_source_title(source)
            
            return {
                'id': citation_num,
                'source': source,
                'formatted': f"{clean_title}. ({datetime.now().year}). Industry research data.",
                'url': None,
                'accessed': datetime.now().strftime('%Y-%m-%d'),
                'style': 'apa',
                'title': clean_title
            }
    
    def _format_mla_citation(self, source: str, citation_num: int) -> Dict[str, Any]:
        """Format source in MLA style with improved title extraction"""
        if source.startswith('http'):
            parsed = urlparse(source)
            domain = parsed.netloc.replace('www.', '')
            clean_title = self._clean_source_title(domain)
            
            return {
                'id': citation_num,
                'source': source,
                'formatted': f'"{clean_title}." Web. {datetime.now().strftime("%d %b %Y")}.',
                'url': source,
                'accessed': datetime.now().strftime('%Y-%m-%d'),
                'style': 'mla',
                'title': clean_title
            }
        else:
            clean_title = self._clean_source_title(source)
            return {
                'id': citation_num,
                'source': source,
                'formatted': f'"{clean_title}." Industry Research, {datetime.now().year}.',
                'url': None,
                'accessed': datetime.now().strftime('%Y-%m-%d'),
                'style': 'mla',
                'title': clean_title
            }
    
    def _format_chicago_citation(self, source: str, citation_num: int) -> Dict[str, Any]:
        """Format source in Chicago style with improved title extraction"""
        if source.startswith('http'):
            parsed = urlparse(source)
            domain = parsed.netloc.replace('www.', '')
            clean_title = self._clean_source_title(domain)
            
            return {
                'id': citation_num,
                'source': source,
                'formatted': f'{clean_title}, accessed {datetime.now().strftime("%B %d, %Y")}, {source}.',
                'url': source,
                'accessed': datetime.now().strftime('%Y-%m-%d'),
                'style': 'chicago',
                'title': clean_title
            }
        else:
            clean_title = self._clean_source_title(source)
            return {
                'id': citation_num,
                'source': source,
                'formatted': f'{clean_title}, Industry Research ({datetime.now().year}).',
                'url': None,
                'accessed': datetime.now().strftime('%Y-%m-%d'),
                'style': 'chicago',
                'title': clean_title
            }
    
    def apply_citations_to_content(self, content: str, citation_data: Dict) -> str:
        """Apply citations to content text"""
        cited_content = content
        offset = 0
        
        # Sort claims by position (reverse order to maintain positions)
        cited_claims = sorted(citation_data['cited_claims'], key=lambda x: x['start_pos'], reverse=True)
        
        for claim in cited_claims:
            if claim.get('has_citation') and claim.get('citation_number'):
                # Find the end of the sentence containing the claim
                start_pos = claim['start_pos'] + offset
                end_pos = claim['end_pos'] + offset
                
                # Look for sentence end after the claim
                sentence_end = cited_content.find('.', end_pos)
                if sentence_end == -1:
                    sentence_end = end_pos
                
                # Insert citation before the period
                citation_text = f" [{claim['citation_number']}]"
                cited_content = cited_content[:sentence_end] + citation_text + cited_content[sentence_end:]
                offset += len(citation_text)
        
        return cited_content
    
    def create_bibliography_section(self, bibliography: List[Dict], style: str = "apa") -> str:
        """Create formatted bibliography section"""
        if not bibliography:
            return ""
        
        bibliography_section = "\n\n## References\n\n"
        
        # Sort bibliography by citation number
        sorted_bib = sorted(bibliography, key=lambda x: x['id'])
        
        for entry in sorted_bib:
            bibliography_section += f"{entry['id']}. {entry['formatted']}\n"
        
        return bibliography_section
    
    def add_citations(self, content: str, research_data: Dict, style: str = "apa") -> Dict[str, Any]:
        """Main function to add citations to content"""
        start_time = time.time()
        
        logger.info("Starting citation process for content")
        
        # Validate research data
        if not research_data or not any([
            research_data.get('statistics'),
            research_data.get('expert_quotes'),
            research_data.get('results')
        ]):
            logger.warning("No research data available for citations")
            return {
                'cited_content': content,
                'bibliography': [],
                'citation_count': 0,
                'uncited_claims': [],
                'metadata': {
                    'processing_time': time.time() - start_time,
                    'error': 'No research data available'
                }
            }
        
        try:
            # Step 1: Identify claims needing citations
            claims = self.identify_claims_needing_citations(content)
            logger.info(f"Identified {len(claims)} potential claims for citation")
            
            # Step 2: Match claims to research sources
            matched_claims = self.match_claims_to_sources(claims, research_data)
            successful_matches = [c for c in matched_claims if c.get('matched_source')]
            logger.info(f"Successfully matched {len(successful_matches)} claims to sources")
            
            # Step 3: Format citations and bibliography
            citation_data = self.format_citations(matched_claims, research_data, style)
            
            # Step 4: Apply citations to content
            cited_content = self.apply_citations_to_content(content, citation_data)
            
            # Step 5: Add bibliography
            bibliography_section = self.create_bibliography_section(citation_data['bibliography'], style)
            final_content = cited_content + bibliography_section
            
            # Identify uncited claims
            uncited_claims = [
                {
                    'text': c['text'],
                    'type': c['type'],
                    'reason': 'No matching source found' if not c.get('matched_source') else 'Low confidence match'
                }
                for c in matched_claims 
                if not c.get('has_citation')
            ]
            
            processing_time = time.time() - start_time
            
            result = {
                'cited_content': final_content,
                'bibliography': citation_data['bibliography'],
                'citation_count': len(citation_data['bibliography']),
                'uncited_claims': uncited_claims,
                'metadata': {
                    'processing_time': processing_time,
                    'total_claims_identified': len(claims),
                    'claims_with_sources': len(successful_matches),
                    'citation_style': style,
                    'success_rate': len(successful_matches) / len(claims) if claims else 0
                }
            }
            
            logger.info(f"Citation process completed: {result['citation_count']} citations added, {len(uncited_claims)} uncited claims")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in citation process: {e}")
            return {
                'cited_content': content,
                'bibliography': [],
                'citation_count': 0,
                'uncited_claims': [],
                'metadata': {
                    'processing_time': time.time() - start_time,
                    'error': str(e)
                }
            }

# Create default citation agent instance
citation_agent = CitationAgent()

# ADK Agent Integration
from google.adk import Agent
from google.genai import types

# Create ADK-compatible agent
root_agent = Agent(
    model="gemini-2.5-flash",
    name="citation_agent",
    description="Citation specialist that adds proper academic citations to content",
    instruction="""You are a citation specialist that adds proper academic citations to content.

When provided with content and research data:
1. Identify claims, statistics, and statements that need citations
2. Match these claims to available research sources
3. Add inline citations in [1], [2] format
4. Create a properly formatted bibliography
5. Maintain content quality while adding citations

Focus on:
- Statistics and data points
- Expert quotes and opinions
- Research findings
- Market data and trends
- Claims that benefit from source attribution

Use standard academic citation formats (APA, MLA, Chicago) and ensure all citations are properly formatted and linked to reliable sources."""
)

async def add_citations(content: str, research_data: Dict, style: str = "apa") -> Dict[str, Any]:
    """Main entry point for citation functionality"""
    return citation_agent.add_citations(content, research_data, style)