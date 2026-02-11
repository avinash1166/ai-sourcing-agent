#!/usr/bin/env python3
"""
Web Scraper Module for Alibaba, Made-in-China, GlobalSources
Lightweight scraping with Playwright (headless) + Fallback to requests
"""

import asyncio
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

# Optional import - only needed if actually scraping
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightTimeout = TimeoutError

from config import SEARCH_KEYWORDS, SEARCH_PLATFORMS, RATE_LIMITS

class VendorScraper:
    """Web scraper for ODM/OEM platforms"""
    
    def __init__(self):
        self.delay = RATE_LIMITS['search_delay_seconds']
        self.max_vendors_per_day = RATE_LIMITS['max_vendors_per_day']
    
    async def scrape_alibaba(self, keyword: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Scrape Alibaba for vendors - with fallback to simple requests"""
        
        # Try Playwright first if available
        if PLAYWRIGHT_AVAILABLE:
            results = await self._scrape_alibaba_playwright(keyword, max_results)
            if len(results) > 0:
                return results
            print("  ⚠️  Playwright got 0 results, trying fallback...")
        
        # Fallback to requests + BeautifulSoup (simpler, less detectable)
        return await self._scrape_alibaba_simple(keyword, max_results)
    
    async def _scrape_alibaba_simple(self, keyword: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Simple scraper using requests (fallback method)"""
        print(f"\n>>> Scraping Alibaba (simple mode) for: '{keyword}'...")
        results = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            search_url = f"https://www.alibaba.com/trade/search?SearchText={keyword.replace(' ', '+')}"
            
            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check for anti-bot
            if 'robot' in response.text.lower() or 'captcha' in response.text.lower():
                print("  ⚠️  Anti-bot detection triggered (simple scraper)")
                return results
            
            # Try multiple product card selectors
            products = []
            for selector in ['div[class*="organic"]', 'div[class*="card"]', 'div[class*="product"]', 'div[class*="search-card"]']:
                products = soup.select(selector)
                if len(products) > 0:
                    print(f"  ✓ Found {len(products)} products using: {selector}")
                    break
            
            if len(products) == 0:
                print("  ⚠️  No products found - Alibaba may have changed HTML structure")
                return results
            
            for i, product in enumerate(products[:max_results]):
                try:
                    # Extract title
                    title = "Unknown"
                    for tag in ['h2', 'h3', 'a']:
                        title_elem = product.find(tag)
                        if title_elem and title_elem.get_text(strip=True):
                            title = title_elem.get_text(strip=True)
                            if len(title) > 10:  # Valid title
                                break
                    
                    # Extract link
                    link = ""
                    link_elem = product.find('a', href=True)
                    if link_elem:
                        link = link_elem['href']
                        if link.startswith('//'):
                            link = 'https:' + link
                        elif not link.startswith('http'):
                            link = 'https://www.alibaba.com' + link
                    
                    # Extract price
                    price = "Contact Supplier"
                    price_elem = product.find(class_=lambda x: x and 'price' in x.lower())
                    if price_elem:
                        price = price_elem.get_text(strip=True)
                    
                    # Get full text for context
                    full_text = product.get_text(strip=True)
                    
                    if title != "Unknown" and len(title) > 10:
                        results.append({
                            'vendor_name': title[:200],
                            'url': link,
                            'platform': 'alibaba',
                            'price_info': price,
                            'moq_info': "Contact Supplier",
                            'raw_text': full_text[:1000]
                        })
                        print(f"  ✓ Found: {title[:60]}...")
                
                except Exception as e:
                    print(f"  ✗ Error extracting product {i}: {str(e)[:80]}")
                    continue
        
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Network error: {str(e)[:100]}")
        except Exception as e:
            print(f"  ✗ Scraping error: {str(e)[:100]}")
        
        print(f"  → Scraped {len(results)} vendors from Alibaba (simple mode)")
        return results
    
    async def _scrape_alibaba_playwright(self, keyword: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Scrape Alibaba using Playwright (original method)"""
        if not PLAYWRIGHT_AVAILABLE:
            print("⚠ Playwright not installed. Skipping web scraping.")
            print("Install with: pip install playwright && playwright install chromium")
            return []
        
        print(f"\n>>> Scraping Alibaba for: '{keyword}'...")
        results = []
        
        try:
            async with async_playwright() as p:
                # Launch browser (headless to save RAM)
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                # Search URL
                search_url = f"https://www.alibaba.com/trade/search?SearchText={keyword.replace(' ', '+')}"
                
                try:
                    await page.goto(search_url, timeout=30000)
                    await page.wait_for_timeout(5000)  # Wait longer for dynamic content
                    
                    # DEBUG: Check if page loaded
                    page_content = await page.content()
                    if "robot" in page_content.lower() or "captcha" in page_content.lower():
                        print("  ⚠️  Anti-bot detection triggered!")
                    
                    # Try multiple possible selectors (Alibaba changes often)
                    possible_selectors = [
                        '.organic-list-offer',  # Old selector
                        '[class*="organic"]',   # Any organic class
                        '[class*="card"]',      # Card-based layout
                        '[class*="product"]',   # Product cards
                        '.search-card',         # New search cards
                        '[class*="item"]'       # Generic items
                    ]
                    
                    products = []
                    for selector in possible_selectors:
                        products = await page.query_selector_all(selector)
                        if len(products) > 0:
                            print(f"  ✓ Found products using selector: {selector}")
                            break
                    
                    if len(products) == 0:
                        print(f"  ⚠️  No products found with any selector")
                        print(f"  💡 Page might be blocked or HTML changed")
                        # DEBUG: Save page screenshot for analysis
                        await page.screenshot(path='/tmp/alibaba_debug.png')
                        print(f"  📸 Screenshot saved to /tmp/alibaba_debug.png")
                    
                    for i, product in enumerate(products[:max_results]):
                        try:
                            # Try multiple selectors for title
                            title = "Unknown"
                            for title_selector in ['h2', '.title', 'h3', '[class*="title"]', 'a']:
                                title_elem = await product.query_selector(title_selector)
                                if title_elem:
                                    title_text = await title_elem.inner_text()
                                    if title_text and len(title_text.strip()) > 5:
                                        title = title_text
                                        break
                            
                            # Extract link
                            link = ""
                            link_elem = await product.query_selector('a[href]')
                            if link_elem:
                                link = await link_elem.get_attribute('href')
                                if link and not link.startswith('http'):
                                    link = f"https:{link}" if link.startswith('//') else f"https://www.alibaba.com{link}"
                            
                            # Extract price (try multiple selectors)
                            price = "Contact Supplier"
                            for price_selector in ['.price', '[class*="price"]', '[class*="Price"]']:
                                price_elem = await product.query_selector(price_selector)
                                if price_elem:
                                    price_text = await price_elem.inner_text()
                                    if price_text and '$' in price_text:
                                        price = price_text
                                        break
                            
                            # Extract MOQ
                            moq = "Contact Supplier"
                            full_text = await product.inner_text()
                            if 'moq' in full_text.lower() or 'min' in full_text.lower():
                                # Try to extract MOQ from text
                                for moq_selector in ['.moq', '[class*="moq"]', '[class*="min"]']:
                                    moq_elem = await product.query_selector(moq_selector)
                                    if moq_elem:
                                        moq = await moq_elem.inner_text()
                                        break
                            
                            # Only add if we got meaningful data
                            if title != "Unknown" and len(title.strip()) > 5:
                                results.append({
                                    'vendor_name': title.strip()[:200],
                                    'url': link,
                                    'platform': 'alibaba',
                                    'price_info': price.strip(),
                                    'moq_info': moq.strip(),
                                    'raw_text': full_text[:1000]  # Limit size
                                })
                                
                                print(f"  ✓ Found: {title[:60]}...")
                        
                        except Exception as e:
                            print(f"  ✗ Error extracting product {i}: {str(e)[:100]}")
                            continue
                
                except PlaywrightTimeout:
                    print("  ✗ Page load timeout - Alibaba may be blocking")
                except Exception as e:
                    print(f"  ✗ Scraping error: {str(e)[:200]}")
                
                finally:
                    await browser.close()
        
        except Exception as e:
            print(f"✗ Browser error: {e}")
        
        print(f"  → Scraped {len(results)} vendors from Alibaba")
        return results
    
    async def scrape_made_in_china(self, keyword: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Scrape Made-in-China for vendors - with simple fallback"""
        
        # Try Playwright first
        if PLAYWRIGHT_AVAILABLE:
            results = await self._scrape_made_in_china_playwright(keyword, max_results)
            if len(results) > 0:
                return results
            print("  ⚠️  Playwright got 0 results, trying simple mode...")
        
        # Fallback to simple requests
        return await self._scrape_made_in_china_simple(keyword, max_results)
    
    async def _scrape_made_in_china_simple(self, keyword: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Simple Made-in-China scraper using requests
        STRATEGY: Skip product page fetching due to truncated URLs
        Instead: Extract as much as possible from search results + use BeautifulSoup to parse listing
        """
        print(f"\n>>> Scraping Made-in-China (simple mode) for: '{keyword}'...")
        results = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.made-in-china.com/',
                'Connection': 'keep-alive',
            }
            
            # Made-in-China search URL - use keyword format that works better
            search_url = f"https://www.made-in-china.com/products-search/hot-china-products/{keyword.replace(' ', '+')}.html"
            
            print(f"    Searching: {search_url[:80]}...")
            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Made-in-China product cards - try multiple selectors
            products = soup.select('.item, .search-item, [class*="product"], [class*="item-main"]')
            
            if len(products) == 0:
                print(f"  ⚠️  No products found with standard selectors")
                # Try alternative scraping of visible text
                page_text = soup.get_text(strip=True)
                if len(page_text) < 500:
                    print(f"  ⚠️  Page seems blocked or empty")
                return results
            
            print(f"  ✓ Found {len(products)} product listings")
            
            for i, product in enumerate(products[:max_results]):
                try:
                    # Extract title
                    title = "Unknown"
                    for selector in ['h2', 'h3', '.title', 'a[title]', '[class*="title"]']:
                        title_elem = product.select_one(selector)
                        if title_elem:
                            title_text = title_elem.get_text(strip=True) or title_elem.get('title', '')
                            if len(title_text) > 10:
                                title = title_text
                                break
                    
                    # Extract ALL text from product card (includes hidden details)
                    product_full_text = product.get_text(separator='\n', strip=True)
                    
                    # Try to find company/supplier name in the product card
                    vendor_company = None
                    for sel in ['[class*="company"]', '[class*="supplier"]', '[class*="manu"]', '[class*="seller"]']:
                        company_elem = product.select_one(sel)
                        if company_elem:
                            vendor_text = company_elem.get_text(strip=True)
                            if len(vendor_text) > 5 and len(vendor_text) < 100:
                                vendor_company = vendor_text
                                break
                    
                    # Extract price from listing
                    price = "Contact Supplier"
                    for price_sel in ['.price', '[class*="price"]', '[class*="Price"]']:
                        price_elem = product.select_one(price_sel)
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            if price_text and ('$' in price_text or 'USD' in price_text.upper()):
                                price = price_text
                                break
                    
                    # Try to extract MOQ from product card
                    moq_info = "Contact Supplier"
                    import re
                    moq_match = re.search(r'MOQ[:\s]*(\d+)', product_full_text, re.IGNORECASE)
                    if moq_match:
                        moq_info = moq_match.group(0)
                    
                    # Extract any links (even if truncated, we'll note them)
                    link = ""
                    link_elem = product.select_one('a[href]')
                    if link_elem:
                        href = link_elem.get('href', '')
                        if href and not '...' in href:
                            if not href.startswith('http'):
                                link = f"https://www.made-in-china.com{href}"
                            else:
                                link = href
                    
                    # Look for email in product card text (unlikely but possible)
                    vendor_email = None
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    emails = re.findall(email_pattern, product_full_text)
                    if emails:
                        # Filter out junk
                        real_emails = [e for e in emails if not any(x in e.lower() for x in ['example', 'test', 'noreply'])]
                        if real_emails:
                            vendor_email = real_emails[0]
                    
                    # Build rich context from product card alone (no product page needed)
                    combined_text = f"""
PRODUCT LISTING from Made-in-China Search Results:
Title: {title}
Vendor/Supplier: {vendor_company or 'Not specified in listing'}
Email: {vendor_email or 'Not found in listing'}
Price: {price}
MOQ: {moq_info}
Product URL: {link if link else 'Not available'}

FULL PRODUCT CARD TEXT:
{product_full_text[:3000]}

INSTRUCTIONS FOR EXTRACTION:
- Extract vendor company name (look for "Shenzhen", "Guangzhou", "Co., Ltd", etc.)
- Extract real specifications (screen size, OS, features)
- Extract pricing if visible
- If information is missing, mark as null (don't guess!)
- Product URL may be placeholder if truncated with "..."
"""
                    
                    if title != "Unknown" and len(title) > 10:
                        results.append({
                            'vendor_name': vendor_company or title[:200],
                            'url': link if link else "https://www.made-in-china.com",
                            'platform': 'made-in-china',
                            'price_info': price,
                            'moq_info': moq_info,
                            'raw_text': combined_text[:6000],  # Rich context from product card
                            'contact_email': vendor_email,
                            'product_url': link if link else None
                        })
                        print(f"  ✓ Found: {vendor_company or title[:60]}...")
                
                except Exception as e:
                    print(f"  ✗ Error extracting product {i}: {str(e)[:80]}")
                    continue
        
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Network error: {str(e)[:100]}")
        except Exception as e:
            print(f"  ✗ Scraping error: {str(e)[:100]}")
        
        print(f"  → Scraped {len(results)} vendors from Made-in-China (simple mode)")
        return results
    
    async def _scrape_made_in_china_playwright(self, keyword: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Scrape Made-in-China using Playwright (original)"""
        if not PLAYWRIGHT_AVAILABLE:
            print("⚠ Playwright not installed. Skipping web scraping.")
            return []
        
        print(f"\n>>> Scraping Made-in-China for: '{keyword}'...")
        results = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                search_url = f"https://www.made-in-china.com/products-search/hot-china-products/{keyword.replace(' ', '_')}.html"
                
                try:
                    await page.goto(search_url, timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    # Extract product listings
                    products = await page.query_selector_all('.item-box, .search-item')
                    
                    for i, product in enumerate(products[:max_results]):
                        try:
                            title_elem = await product.query_selector('.item-title, .title a')
                            title = await title_elem.inner_text() if title_elem else "Unknown"
                            
                            link_elem = await product.query_selector('.item-title a, a')
                            link = await link_elem.get_attribute('href') if link_elem else ""
                            if link and not link.startswith('http'):
                                link = f"https://www.made-in-china.com{link}"
                            
                            price_elem = await product.query_selector('.item-price, .price')
                            price = await price_elem.inner_text() if price_elem else "Unknown"
                            
                            full_text = await product.inner_text()
                            
                            results.append({
                                'vendor_name': title.strip(),
                                'url': link,
                                'platform': 'made-in-china',
                                'price_info': price.strip(),
                                'moq_info': "Unknown",
                                'raw_text': full_text
                            })
                            
                            print(f"  ✓ Found: {title[:50]}...")
                        
                        except Exception as e:
                            print(f"  ✗ Error extracting product {i}: {e}")
                            continue
                
                except PlaywrightTimeout:
                    print("  ✗ Page load timeout")
                except Exception as e:
                    print(f"  ✗ Scraping error: {e}")
                
                finally:
                    await browser.close()
        
        except Exception as e:
            print(f"✗ Browser error: {e}")
        
        print(f"  → Scraped {len(results)} vendors from Made-in-China")
        return results
    
    async def scrape_all_platforms(self, keyword: str) -> List[Dict[str, str]]:
        """Scrape all platforms for a given keyword"""
        all_results = []
        
        # Scrape Alibaba
        alibaba_results = await self.scrape_alibaba(keyword, max_results=5)
        all_results.extend(alibaba_results)
        
        # Delay between platforms
        await asyncio.sleep(self.delay)
        
        # Scrape Made-in-China
        mic_results = await self.scrape_made_in_china(keyword, max_results=5)
        all_results.extend(mic_results)
        
        return all_results
    
    async def daily_vendor_discovery(self) -> List[Dict[str, str]]:
        """
        Run daily vendor discovery across all keywords and platforms
        Respects max_vendors_per_day limit
        """
        print("\n" + "=" * 60)
        print("DAILY VENDOR DISCOVERY")
        print("=" * 60)
        
        all_vendors = []
        
        for keyword in SEARCH_KEYWORDS:
            if len(all_vendors) >= self.max_vendors_per_day:
                print(f"\n✓ Reached daily limit of {self.max_vendors_per_day} vendors")
                break
            
            vendors = await self.scrape_all_platforms(keyword)
            all_vendors.extend(vendors)
            
            # Delay between keywords
            await asyncio.sleep(self.delay)
        
        # Trim to max limit
        all_vendors = all_vendors[:self.max_vendors_per_day]
        
        print(f"\n✓ Total vendors discovered today: {len(all_vendors)}")
        return all_vendors

# ==================== TESTING ====================
async def test_scraper():
    """Test the scraper with one keyword"""
    scraper = VendorScraper()
    results = await scraper.scrape_alibaba("15.6 inch Android tablet", max_results=3)
    
    print("\n" + "=" * 60)
    print("SCRAPER TEST RESULTS")
    print("=" * 60)
    
    for i, vendor in enumerate(results, 1):
        print(f"\n{i}. {vendor['vendor_name']}")
        print(f"   URL: {vendor['url']}")
        print(f"   Price: {vendor['price_info']}")
        print(f"   MOQ: {vendor['moq_info']}")

if __name__ == "__main__":
    print("Testing web scraper...")
    asyncio.run(test_scraper())
