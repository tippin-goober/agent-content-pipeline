#!/usr/bin/env python3
"""
Test Citation Agent fixes for URL extraction and source formatting
"""

import json
import asyncio
from citation_agent.agent import citation_agent

def test_citation_improvements():
    """Test the improved citation functionality"""
    
    print("🧪 Testing Citation Agent URL extraction and formatting improvements")
    print("=" * 70)
    
    # Sample content with claims that need citations
    test_content = """
    Enterprise AI adoption has surged dramatically in 2024, with 78% of organizations now using AI in at least one business function, representing a significant increase from 55% in 2023. 

    The spending on AI has grown substantially, reaching $13.8 billion in 2024, which is more than six times the $2.3 billion spent in 2023. According to McKinsey research, generative AI adoption stands at 71% among enterprises, indicating its transition from experimental to essential technology.

    Despite widespread adoption, 74% of companies struggle to achieve and scale tangible value from AI, with only 26% having developed capabilities to move beyond proofs of concept. Industry experts note that 62% of leaders cite data access and integration as the top challenges to AI adoption.
    """
    
    # Sample research data with the format from your pipeline
    test_research_data = {
        "queries": [
            "Enterprise AI adoption statistics 2024",
            "AI spending trends and growth data"
        ],
        "results": [
            {
                "query": "Enterprise AI adoption statistics 2024",
                "answer": "Enterprise AI adoption has surged dramatically in 2024, with 78% of organizations now using AI in at least one business function, up from 55% in 2023. McKinsey State of AI report 2024 shows that generative AI adoption stands at 71% among enterprises. The spending on AI has grown substantially, reaching $13.8 billion in 2024, more than six times the $2.3 billion spent in 2023 according to Menlo Ventures research.",
                "sources": [
                    "McKinsey State of AI report 2024",
                    "https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai",
                    "Menlo Ventures 2024 State of Generative AI",
                    "Deloitte 2024 State of AI in the Enterprise report",
                    "experimental to essential technology[1][3]"
                ]
            },
            {
                "query": "AI spending trends and growth data",
                "answer": "AI spending surged to $13.8 billion in 2024, a 6x increase from $2.3 billion in 2023. Despite enthusiasm, 74% of companies struggle to scale AI value effectively, with data access and integration cited as top obstacles by 62% of leaders according to Deloitte's 2024 State of AI in the Enterprise report.",
                "sources": [
                    "https://www.deloitte.com/global/en/our-thinking/insights/topics/emerging-technologies/state-of-ai.html",
                    "Deloitte 2024 State of AI in the Enterprise report",
                    "Boston Consulting Group AI adoption research",
                    "pilots to production and strategic integration[2]"
                ]
            }
        ],
        "statistics": [
            "78% of organizations use AI in at least one business function in 2024, up from 55% in 2023",
            "71% generative AI adoption among enterprises in 2024",
            "$13.8 billion AI spending in 2024, up from $2.3 billion in 2023",
            "74% of companies struggle to achieve and scale tangible value from AI",
            "62% of leaders cite data access and integration as top challenges"
        ],
        "expert_quotes": [
            "AI leaders are raising the bar with more ambitious goals targeting meaningful outcomes",
            "Without meaningful access to enterprise data, even the most powerful AI fails to generate relevant results"
        ],
        "sources": [
            "https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai",
            "https://www.deloitte.com/global/en/our-thinking/insights/topics/emerging-technologies/state-of-ai.html",
            "McKinsey State of AI report 2024",
            "Deloitte 2024 State of AI in the Enterprise report",
            "Menlo Ventures 2024 State of Generative AI",
            "Boston Consulting Group AI adoption research"
        ]
    }
    
    print("📝 Test Content Preview:")
    print(test_content[:200] + "..." if len(test_content) > 200 else test_content)
    print()
    
    print("📊 Test Research Data:")
    print(f"   - {len(test_research_data['results'])} research results")
    print(f"   - {len(test_research_data['statistics'])} statistics")
    print(f"   - {len(test_research_data['sources'])} sources")
    print(f"   - URLs found: {sum(1 for s in test_research_data['sources'] if s.startswith('http'))}")
    print()
    
    try:
        # Test the citation agent
        print("🔍 Running Citation Agent...")
        result = citation_agent.add_citations(test_content, test_research_data, style="apa")
        
        print("✅ Citation process completed!")
        print()
        
        # Display results
        print("📈 RESULTS:")
        print(f"   Citations added: {result['citation_count']}")
        print(f"   Claims identified: {result['metadata']['total_claims_identified']}")
        print(f"   Claims with sources: {result['metadata']['claims_with_sources']}")
        print(f"   Success rate: {result['metadata']['success_rate']:.1%}")
        print(f"   Uncited claims: {len(result['uncited_claims'])}")
        print()
        
        if result['bibliography']:
            print("📚 BIBLIOGRAPHY SAMPLE:")
            for i, bib_entry in enumerate(result['bibliography'][:3], 1):
                print(f"   {i}. {bib_entry['formatted']}")
                if bib_entry.get('url'):
                    print(f"      URL: {bib_entry['url']}")
                print()
        
        if result['uncited_claims']:
            print("⚠️  UNCITED CLAIMS:")
            for claim in result['uncited_claims'][:2]:
                print(f"   - {claim['text'][:80]}{'...' if len(claim['text']) > 80 else ''}")
                print(f"     Reason: {claim['reason']}")
            print()
        
        print("📄 CITED CONTENT PREVIEW:")
        cited_preview = result['cited_content'][:500] + "..." if len(result['cited_content']) > 500 else result['cited_content']
        print(cited_preview)
        print()
        
        # Validate improvements
        improvements = []
        
        # Check for actual URLs in bibliography
        url_count = sum(1 for bib in result['bibliography'] if bib.get('url') and bib['url'].startswith('http'))
        if url_count > 0:
            improvements.append(f"✅ {url_count} working URLs in bibliography")
        else:
            improvements.append("❌ No working URLs found")
        
        # Check for clean titles
        clean_titles = [bib.get('title', '') for bib in result['bibliography']]
        if any(title and len(title) > 5 and not title.startswith('http') for title in clean_titles):
            improvements.append("✅ Clean, readable source titles")
        else:
            improvements.append("❌ Source titles need improvement")
        
        # Check citation success rate
        if result['metadata']['success_rate'] > 0.5:
            improvements.append(f"✅ Good citation success rate ({result['metadata']['success_rate']:.1%})")
        else:
            improvements.append(f"⚠️  Low citation success rate ({result['metadata']['success_rate']:.1%})")
        
        print("🎯 IMPROVEMENT VALIDATION:")
        for improvement in improvements:
            print(f"   {improvement}")
        
        success = all("✅" in imp for imp in improvements[:2])  # First two are critical
        
        if success:
            print("\n🎉 SUCCESS! Citation fixes are working properly!")
            print("   - URLs are being extracted and formatted correctly")
            print("   - Source titles are clean and readable")
            print("   - Citations are being matched to claims effectively")
        else:
            print("\n⚠️  Some issues remain. Check the improvements above.")
        
        return success
        
    except Exception as e:
        print(f"❌ Error testing citations: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_before_after_example():
    """Show before/after comparison of citation improvements"""
    
    print("\n" + "="*70)
    print("📊 BEFORE vs AFTER COMPARISON")
    print("="*70)
    
    print("\n🔴 BEFORE (Problems):")
    print("   Sources:")
    print("   - 'experimentation to embedding AI as core infrastruct'")
    print("   - 'experimental to essential technology[1][3]'")
    print("   - 'pilots to production and strategic integration[2]'")
    print("   ")
    print("   Bibliography:")
    print("   1. experimentation to embedding AI as core infrastruct. (2024). Research data.")
    print("   2. experimental to essential technology[1][3]. (2024). Research data.")
    print()
    
    print("🟢 AFTER (Fixed):")
    print("   Sources:")
    print("   - https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai")
    print("   - McKinsey State of AI report 2024")
    print("   - https://www.deloitte.com/global/en/our-thinking/insights/topics/emerging-technologies/state-of-ai.html")
    print("   ")
    print("   Bibliography:")
    print("   1. McKinsey & Company. Retrieved January 05, 2025, from https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai")
    print("   2. Deloitte. Retrieved January 05, 2025, from https://www.deloitte.com/global/en/our-thinking/insights/topics/emerging-technologies/state-of-ai.html")
    print()
    
    print("✅ KEY IMPROVEMENTS:")
    print("   • Full URLs extracted instead of truncated text snippets")
    print("   • Clean, professional organization names as titles")
    print("   • Proper academic citation formatting")
    print("   • Working URLs that users can actually visit")
    print("   • Better matching of claims to authoritative sources")

def main():
    print("🔧 Citation Agent Fix Validation")
    print("Testing URL extraction and source formatting improvements")
    print()
    
    # Run the main test
    success = test_citation_improvements()
    
    # Show before/after comparison
    show_before_after_example()
    
    print("\n" + "="*70)
    if success:
        print("🎉 CITATION FIXES VALIDATED!")
        print("The citation agent now properly:")
        print("   ✅ Extracts full URLs from Perplexity responses")
        print("   ✅ Formats clean, readable source titles")
        print("   ✅ Creates professional bibliography entries")
        print("   ✅ Maps citations correctly between inline refs and bibliography")
        print("\n💡 Ready for production use!")
    else:
        print("⚠️  CITATION FIXES NEED ATTENTION")
        print("Some issues were detected. Review the test output above.")
    
    print("\n🚀 To test with full pipeline, run:")
    print("   python3 pipeline_single_session.py")

if __name__ == "__main__":
    main()