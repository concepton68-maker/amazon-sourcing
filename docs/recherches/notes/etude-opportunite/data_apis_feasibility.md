# Amazon marketplace data for a third-party-seller SaaS: technical & legal feasibility (as of 2026-11-11)

Conventions used below:
- **Reliability**: HIGH = primary source read directly (Amazon docs/policy text, court-related primary reporting); MED = reputable secondary / vendor's own page via search snippet; LOW = aggregator/blog, unverified, or conflicting.
- **Data type**: OBSERVED (returned by Amazon as fact, e.g. current offers), CALCULATED (deterministic from observed inputs, e.g. fee estimate, rate-limit arithmetic), ESTIMATED (model output, e.g. units sold from BSR).
- Amazon's SP-API docs moved to the domain `developer-docs.amazon` (old `developer-docs.amazon.com` URLs 301-redirect there). Page `updatedAt` stamps cited below are from the docs' own metadata.

---

## Q1. Amazon Selling Partner API (SP-API): access, fees, policies, endpoints, rate limits, cross-customer use

### Takeaway
SP-API is the only sanctioned source for the seller-specific data a profit/eligibility tool needs (fees, listing restrictions, live offers/Buy Box), and as of Nov 2026 it carries **no developer fee** (the $1,400/yr + usage-tier plan announced Nov 2025 was cancelled in May 2026). But the Acceptable Use Policy forbids (a) aggregating data across authorized sellers to serve other customers (AUP 4.4/4.6) and (b) "using, offering or promoting external (non-Amazon) data services that vend data retrieved from Amazon's websites" (AUP 4.3) — which on its face covers Keepa/scraper data, and an Amazon SP-API team reply reported on the seller forums applied it exactly that way. This is the single biggest legal design constraint for a SellerAmp-style product.

### Cited Findings

**Developer registration (public vs private) — HIGH**
- Public developers build apps serving other sellers, must obtain OAuth authorization from each seller, and "must list their application in the Amazon Selling Partner Appstore, in accordance with the Solution Provider Portal Agreement"; private developers build for internal use only. Page updated 2026-09-09. — [Register as a Public SP-API Developer](https://developer-docs.amazon/sp-api/docs/register-as-a-public-developer.md)
- Public registration requires a publicly accessible website describing the services (no under-construction / login-only sites), selection of roles, and — if requesting restricted (PII) roles — an architecture review with the SP-API Solutions Architecture team (data flows, PII controls, possibly screen-share demo) and a "Phase 2: Data security assessment". Amazon questions must be answered within 5 days or the case is closed. — [Register as a Public SP-API Developer](https://developer-docs.amazon/sp-api/docs/register-as-a-public-developer.md)
- Authorization limits (updated 2026-09-09): Private app = 10 self-authorizations, no OAuth; Public app **not listed** on Appstore = 25 seller OAuth authorizations; Public app **listed** on Appstore = unlimited. — [Authorization Limits](https://developer-docs.amazon/sp-api/docs/application-authorization-limits.md)
- Seller Central roles split into "service provider-eligible" and "seller employee-only" roles; the latter are "not available to service providers through any method", and being added as an employee user is not a workaround (updated 2026-10-28). — [Understanding Seller Central Role Eligibility](https://developer-docs.amazon/sp-api/docs/eligible-seller-central-roles-for-service-providers.md)
- Policies governing SP-API: Data Protection Policy (DPP), Acceptable Use Policy (AUP), Solution Provider Portal Agreement; English version prevails. Page updated 2026-09-16. — [Policies and Agreements](https://developer-docs.amazon/sp-api/docs/policies-and-agreements.md)

**Acceptable Use Policy — key clauses (HIGH; text fetched 2026-11-11, no version date on page)** — [Amazon AUP (en_US)](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US)
- 1.1 "Use the Amazon Services API only to perform acceptable Amazon activities, and only for Authorized Users who have authorized you to perform these activities on their behalf."
- 2.4 "Be explicit about any calculations and the use of models such as artificial intelligence in the service you provide, their accuracy and data freshness." (relevant to sales estimates)
- 3.10 "Do not attempt to circumvent throttling quotas through the creation of multiple Solution Provider accounts or applications."
- 4.3 "Do not use, offer or promote external (non-Amazon) data services that vend information or data retrieved from Amazon's websites."
- 4.4 "Do not aggregate data across Authorized Users' businesses or customers obtained through the Amazon Services API to provide or sell to any parties, including competing Authorized Users."
- 4.5 "Do not promote, publish or share insights about Amazon's business."
- 4.6 "Do not disclose Information, individually labelled or aggregated, to other Application users, affiliated entities or any outside parties, unless required to perform acceptable Authorized User activities for Authorized Users that authorized your Application."
- 4.1 PII about customers may be used only for merchant-fulfilled shipping or legal/tax requirements.
- Breach → suspension/termination of API access.

**Amazon's reported interpretation of AUP 4.3 vis-à-vis Keepa (MED-LOW: second-hand report, undated forum thread, Amazon moderator declined to interpret)**
- A developer reported that, after two support cases, the Amazon Services API team told them "third-party product data cannot be incorporated into an SP-API application," even when technically separated; they asked why SellerAmp (Keepa charts + SP-API) appears to do this. The Amazon forum moderator replied that policy interpretation is outside the forum's scope and pointed to AUP §4.3 as the relevant provision, referring them to Developer Support. — [Seller Forums thread on AUP 4.3](https://sellercentral.amazon.com/seller-forums/discussions/t/a7961c30-b453-4dcc-9a31-e1b6312d36b0)

**Data Protection Policy (HIGH)** — [Amazon DPP (en_US)](https://sellercentral.amazon.com/mws/static/policy?documentType=DPP&locale=en_US)
- 1.7: delete Information within 30 days of Amazon's request; "retain Information only for so long as, and to the extent, such retention is strictly necessary to fulfill the purposes for which the Information was collected"; "must not retain Information beyond the scope of its authorized use".
- 2.1: PII retained no longer than 30 days after order delivery (except tax/legal); if PII is combined with non-PII, the entire data store must meet PII requirements.
- DPP also requires tagging/identifying the origin of all data in any database containing Information.

**SP-API developer fees: announced, postponed, cancelled (MED — secondary sources; Amazon's original announcement page now 404s)**
- Announced 2025-11-03: $1,400/yr annual subscription for third-party developers (start originally 2026-01-31); monthly GET-call tiers: Basic 2.5M GET calls included; Pro $1,000/mo for 25M; Plus $10,000/mo for 250M; Enterprise negotiated; overage $0.40 per 1,000 calls; only GET calls metered; usage fees from 2026-04-30; apps without payment info to be removed from Appstore 2026-02-09 and lose access 2026-02-16. — [PPC Land, 2026-05-14](https://ppc.land/amazon-drops-sp-api-fees-after-developer-pushback)
- Annual fee start later moved to 2026-03-02 (per Amazon notice in search results); postponed indefinitely 2026-03-09; cancelled 2026-05-12/14. Amazon wording: it "will not move forward with the SP-API usage and annual fees at this time." — [PPC Land](https://ppc.land/amazon-drops-sp-api-fees-after-developer-pushback); [Novadata, cancellation](https://novadata.io/resources/news/amazon-cancels-sp-api-fees-may-2026); [Fivetran blog](https://www.fivetran.com/blog/no-walled-gardens-amazon-reversed-its-seller-partner-api-fees)
- Conflict: an agentdeals.dev page dated 2026-04-14 claimed the $1,400 fee remained in effect — predates the May cancellation. — [agentdeals.dev](https://agentdeals.dev/vendor/amazon-sp-api)
- The original Amazon announcement URL now returns 404. — [developer.amazonservices.com/spp-announcement](https://developer.amazonservices.com/spp-announcement)
- Sellers using SP-API for their own business were not targeted by the fee plan. — [summary of search results incl. Shopifreaks](https://www.shopifreaks.com/amazon-selling-partner-api-is-no-longer-free/) (LOW-MED)

**Rate-limit model (HIGH)** — [Usage Plans and Rate Limits](https://developer-docs.amazon/sp-api/docs/usage-plans-and-rate-limits.md) (updated 2026-09-09)
- Token-bucket algorithm; "Most operations' rate limits are per the selling partner and application pair"; a different selling partner, different regional account or different application gets a separate bucket. Grantless operations are exceptions.

**Relevant operations & default limits (HIGH; reference pages updated 2026-09-10)**
| Operation | What it returns | Default rate / burst | Source |
|---|---|---|---|
| getItemOffers (Pricing v0) | "lowest priced offers for a single item based on ASIN" (OBSERVED) | 0.5 rps / 1 | [ref](https://developer-docs.amazon/sp-api/reference/getitemoffers.md) |
| getItemOffersBatch (v0) | lowest priced offers for a batch of ASINs | 0.1 rps / 1 | [ref](https://developer-docs.amazon/sp-api/reference/getitemoffersbatch.md) |
| getCompetitiveSummary (2022-05-01) | "competitive summary... including featured buying options" (Buy Box/featured offer) per ASIN+marketplace, batch endpoint | 0.033 rps / 1 | [ref](https://developer-docs.amazon/sp-api/reference/getcompetitivesummary.md) |
| getFeaturedOfferExpectedPriceBatch | up to 40 requests/batch; "featured offer expected price (FOEP)" at/below which the seller can expect to win the featured offer — "not guaranteed" (CALCULATED by Amazon) | 0.033 rps / 1 | [ref](https://developer-docs.amazon/sp-api/reference/getfeaturedofferexpectedpricebatch.md) |
| getMyFeesEstimateForASIN | estimated fees for an ASIN before pricing; "Actual costs may vary"; uses catalog size, which may differ from actual item size (CALCULATED) | 1 rps / 2 | [ref](https://developer-docs.amazon/sp-api/reference/getmyfeesestimateforasin.md) |
| getMyFeesEstimates | fees for a list of products (docs: batches of up to 20) | 0.5 rps / 1 | [ref](https://developer-docs.amazon/sp-api/reference/getmyfeesestimates.md); [batch guide title](https://developer-docs.amazon/sp-api/docs/get-product-fees-batch.md) |
| getListingsRestrictions (2021-08-01) | listing restrictions/approval requirements for an ASIN for the authorized seller (OBSERVED, seller-specific) | 5 rps / 10 | [ref](https://developer-docs.amazon/sp-api/reference/getlistingsrestrictions.md) |
| searchCatalogItems / getCatalogItem (2022-04-01) | catalog attributes, identifiers, keyword search | 2 rps / 2 | [llms index](https://developer-docs.amazon/sp-api/llms.txt) |
| createReport (Reports) | report generation | 0.0167 rps / 15 | [llms index](https://developer-docs.amazon/sp-api/llms.txt) |
- Docs note that "Selling partners whose business demands require higher throughput may see higher rate and burst values". — [getItemOffers ref](https://developer-docs.amazon/sp-api/reference/getitemoffers.md)

### Inferences
- CALCULATED throughput per seller-app pair at default limits: getItemOffers 0.5 rps ≈ 1,800 ASINs/hour ≈ 43,200/day; getListingsRestrictions 5 rps ≈ 18,000 ASINs/hour; getMyFeesEstimateForASIN 1 rps ≈ 3,600/hour; getMyFeesEstimates 0.5 rps × 20 items ≈ 36,000 items/hour; FOEP batch 0.033 rps × 40 ≈ 4,750 ASINs/hour. Because buckets are per seller-app pair, a wholesale bulk scan of e.g. 10,000 ASINs is feasible for each customer on their own token within a few hours, but you cannot pool customers' quotas to serve one customer (AUP 3.10 forbids circumventing throttling; 4.4/4.6 forbid cross-customer reuse).
- Cross-customer caching: the plain reading of AUP 4.4/4.6 + DPP 1.7 is that data fetched under customer A's token (offers, fees, restrictions) may not be cached and shown to customer B, nor be used to build a shared price-history database. Catalog/public offer data is arguably less sensitive, but the AUP makes no public-data carve-out → treat as NOT permitted (MED confidence; no Amazon ruling found).
- AUP 4.3 is the critical risk for combining SP-API with Keepa/scraped data. Incumbents (SellerAmp, Seller Assistant) visibly do combine them, so enforcement appears inconsistent, but the reported SP-API team position makes this a real app-suspension risk. Mitigation options to evaluate with counsel: separate apps/entities, BYO-Keepa-key (user's own licensed data, not "offered" by you), or written confirmation from Amazon Developer Support.
- Restricted (PII) roles are not needed for any of the listed research features; avoiding them keeps registration on the standard review path.
- Fee risk: although cancelled, Amazon publicly priced SP-API at $1,400/yr + $0.40/1k GET over 2.5M/month; "at this time" wording means it could return — model it as a contingent cost. A research tool doing 50k offer lookups/day/customer × 100 customers ≈ 150M GET/month would have fallen in the $10,000/mo "Plus" tier (CALCULATED).

### Gaps
- Exact current batch sizes for getItemOffersBatch and getCompetitiveSummary, and number of offers returned by getItemOffers (commonly cited as top 20) — not verified in this session.
- Whether getItemOffers/getCompetitiveSummary return sales rank (BSR) — not verified here.
- No official Amazon written interpretation of AUP 4.3 found; the forum report is second-hand.
- Appstore listing process/criteria details and timing not researched.

---

## Q2. Product Advertising API 5 → Creators API

### Takeaway
PA-API 5 is deprecated (calls now return HTTP 403 "Product Advertising API is deprecated"); its replacement, the Creators API, is an affiliate/publisher API tied to Associates eligibility — not a sanctioned data source for a seller-tool SaaS.

### Cited Findings
- Amazon's deprecation page: PA-API 5 is deprecated and replaced by the Creators API, "a REST-based API for publishers, influencers, and affiliate partners"; PA-API calls return 403 `AccessDeniedException` "Product Advertising API is deprecated." (HIGH) — [Amazon Associates: PA-API v5 deprecation](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation)
- PA-API docs gave May 15, 2026 as deprecation date; a developer post gives April 30, 2026 as recommended migration cutoff and May 15, 2026 as endpoint retirement (MED). — [PA-API 5 documentation](https://webservices.amazon.com/paapi5/documentation/); [DEV Community](https://dev.to/th3nate/amazon-pa-api-v5-is-shutting-down-april-30-2026-here-is-what-changes-at-the-auth-layer-22ek)
- Creators API requires new credentials created in Associates Central (old AWS keys don't work) (LOW-MED). — [KeywordRush blog](https://www.keywordrush.com/blog/?p=245)
- Loss of Associates eligibility can cut API access before deadlines (LOW). — [Techbloat](https://www.techbloat.com/amazon-product-api-creators-api-migration-and-scraping-boundaries.html)

### Inferences
- Access is gated by being an Associate driving referral sales and the Associates Operating Agreement; using it to power a seller research SaaS (no affiliate links/traffic to Amazon) would likely breach the program's purpose. Not recommended as a core data source.

### Gaps
- Creators API eligibility thresholds (e.g. qualifying sales), rate limits, caching rules and fields (does it expose sales rank/offers?) — FAQ URL returned 404; unknown.

---

## Q3. Amazon Ads API, Amazon Marketing Stream, Brand Analytics / SQP / Product Opportunity Explorer

### Takeaway
Keyword search-volume-like data from Amazon is available only for the *authorized* seller's own brand context: Brand Analytics reports via SP-API require the Brand Analytics role **and** Brand Registry; Ads API data covers only the advertiser's own campaigns. None of it may be pooled across customers under the AUP. Product Opportunity Explorer has no API found.

### Cited Findings
- SP-API Brand Analytics report types and availability (HIGH) — [Analytics Reports](https://developer-docs.amazon/sp-api/docs/report-type-values-analytics.md):
  - `GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT`: "Sellers and vendors who have the Brand Analytics Selling Partner API role, are registered in Amazon Brand Registry, and are a brand representative."
  - `GET_BRAND_ANALYTICS_SEARCH_QUERY_PERFORMANCE_REPORT`, `..._SEARCH_CATALOG_PERFORMANCE_REPORT`, `..._MARKET_BASKET_REPORT`, `..._REPEAT_PURCHASE_REPORT`: Brand Analytics role + Brand Registry.
  - Freshness: weekly periods available ~48h after close (end of Monday); daily non-Saturday periods 72h after close (OBSERVED, lagged).
- Search Terms report is limited to ~12M items (top ASINs by search term/department); SQP gives impressions, clicks, cart adds, purchases per ASIN; periods WEEK/MONTH/QUARTER (MED). — [Analytics Reports (search snippet)](https://developer-docs.amazon.com/sp-api/docs/report-type-values-analytics); [Changelog: Search Terms report update](https://developer-docs.amazon.com/sp-api/changelog/updates-to-the-brand-analytics-search-terms-report)
- Amazon Marketing Stream is available to agencies, tech providers and direct advertisers already integrated with the Ads API; no separate access needed; self-service requires AWS setup (MED). — [Amazon Ads: Marketing Stream](https://advertising.amazon.com/solutions/products/amazon-marketing-stream)
- Ads API access requires completing onboarding to obtain access token and profile ID. — [Amazon Ads API onboarding guide (PDF)](https://m.media-amazon.com/images/G/01/decassets/Amazon_Ads_API_onboarding_guide.pdf) (MED)
- Amazon's own Ads MCP server entered open beta 2026-02-02 (LOW-MED, single secondary mention). — [search summary referencing RevenueGeeks/H10 MCP](https://revenuegeeks.com/software/helium-10/mcp)

### Inferences
- Brand Analytics gives Amazon "search frequency rank" (a rank, not an absolute volume) — any "search volume" number shown by tools is ESTIMATED by the vendor. A SaaS can show it only to the brand-registered seller who authorized it.
- Ads API search-term reports reflect only the advertiser's own impressions/clicks — useful for that seller, not market-wide.

### Gaps
- Ads API fees (none known), Ads API data-use terms (not read), Product Opportunity Explorer API (none found), Brand Analytics freshness for Search Terms report specifically.

---

## Q4. Keepa API

### Takeaway
Keepa is the de-facto source of Amazon price/BSR/offer-count history (used by SellerAmp, Seller Assistant). Pricing is token-based starting at €49/month for 20 tokens/minute. Its redistribution/resale terms could NOT be retrieved (keepa.com is a JS app; no static terms found) — this is a must-verify item. Using Keepa inside an SP-API app collides with AUP 4.3 (see Q1).

### Cited Findings
- Entry plan €49/month = 20 tokens/minute; presets 60 tokens/min €129 and 250 tokens/min €459, custom slider in between; unused tokens expire after 60 minutes; product request ≈1 token/ASIN, product search ≈10 tokens/page, best sellers ≈50 tokens (MED-LOW, third-party; Keepa page not machine-readable). — [RevenueGeeks: Keepa API](https://revenuegeeks.com/software/keepa/api); [Nexscope Keepa API guide](https://www.nexscope.ai/blog/keepa-api-guide)
- Conflict: one source says no free tier, another claims a 100 tokens/min free tier — unresolved (LOW). — [RevenueGeeks](https://revenuegeeks.com/software/keepa/pricing); [socket.dev keepa-mcp](https://socket.dev/npm/package/keepa-mcp)
- API requires an access key and paid monthly subscription. — [akaszynski/keepa (GitHub)](https://github.com/akaszynski/keepa)
- Keepa data is used as input by SellerAmp SAS and Seller Assistant, which display Keepa-driven charts (MED-LOW). — [ProfitHawk Keepa review](https://www.profithawk.io/software-tools/keepa/)
- Some MCP services avoid "reselling" by proxying the user's own Keepa key (BYO key) (LOW). — [MarketplaceAdPros Keepa MCP](https://marketplaceadpros.com/keepa-mcp-server/)
- Seller Assistant's own API "merges the power of Keepa and Amazon SP API into a single platform" (MED, vendor). — [Seller Assistant API blog](https://www.sellerassistant.app/blog/seller-assistant-api/)

### Inferences
- CALCULATED capacity: €49 plan → 20 × 60 × 24 = 28,800 tokens/day ≈ 864k/month; at ~1 token per basic product request that is ~28.8k ASIN lookups/day shared across ALL users of the SaaS — enough for a small user base or caching strategy, not for per-user bulk scans of 10k+ ASINs. Requests with offers/stock data cost more tokens (not verified), so real capacity is lower.
- Data types: Keepa price/rank history is OBSERVED by Keepa (crawled), with its own sampling gaps; "monthly sold" fields are Amazon's badge passthrough (OBSERVED, coarse buckets) whereas sales estimates from rank drops are ESTIMATED.
- BYO-key architecture (each user enters their own Keepa key) reduces redistribution risk vis-à-vis Keepa, and arguably vis-à-vis AUP 4.3 ("offer or promote"), but does not clearly eliminate the latter.

### Gaps
- Keepa API Terms of Service: redistribution, caching, display to end users, reseller licence — UNKNOWN (pages not retrievable; requires direct check / written confirmation from Keepa).
- Exact token costs for offers/stock/buybox parameters, EU marketplace list (Keepa is believed to cover .de/.fr/.it/.es/.co.uk etc., but not verified in this session).

---

## Q5. Other third-party data providers (pricing as found; verify on vendor pages)

### Takeaway
A full market of scraper-based Amazon data APIs exists at ~$0.3–$12 per 1,000 records; all are ultimately derived from scraping Amazon (→ AUP 4.3 problem if mixed with SP-API, and Amazon CoU risk borne indirectly). Seller-tool incumbents' APIs (Jungle Scout, SmartScout, Helium 10) are custom/enterprise-priced or plan-gated.

### Cited Findings
- **Rainforest API (Traject Data)**: Hobbyist $15/mo (500 req), Starter $59 (10k), Production $375 (250k), BigData $1,000 (1M), ScaleUp $2,200 (2.5M); overage ~$0.0118→$0.00176/req; 100-request free trial (MED; a conflicting "from $18/mo" figure also exists). — [Traject Data Rainforest pricing](https://trajectdata.com/?p=1705); [trajectdata.com/pricing](https://trajectdata.com/pricing). Search results also indicate "ScraperAPI has acquired Traject Data" (LOW, unverified). — [scraperapi.com/pricing](https://scraperapi.com/pricing/)
- **Bright Data** Amazon scraper: ~$1.50/1,000 records PAYG, volume ~$0.98–1.30/1k at $499/mo (figures conflict) (LOW-MED). — [Bright Data blog](https://brightdata.com/blog/web-data/best-amazon-scrapers); [Costbench](https://www.costbench.com/compare/bright-data-vs-oxylabs/)
- **Oxylabs** Web Scraper API: Micro $49/mo ≈ 98k results (~$0.50/1k), down to ~$0.30/1k at $999/mo; billed per result row (LOW-MED). — [Costbench](https://www.costbench.com/compare/bright-data-vs-oxylabs/); [socialcrawl.dev comparison](https://www.socialcrawl.dev/blog/best-amazon-product-data-apis-2026)
- **DataForSEO Amazon**: Labs Amazon endpoints (incl. Amazon keyword search volume) $0.012/task + $0.00012/item (~$132 per 1M keywords/ASINs); pay-as-you-go, $50 minimum top-up; Merchant Amazon task prices raised 50% in a later update (MED). — [DataForSEO Amazon Labs pricing](https://dataforseo.com/pricing/dataforseo-labs/dataforseo-amazon-api); [DataForSEO Amazon Bulk Search Volume docs](https://docs.dataforseo.com/v3/dataforseo_labs/amazon/bulk_search_volume/live); [DataForSEO pricing update](https://dataforseo.com/update/pricing-update-in-dataforseo-apis)
- **Canopy API**: free 100 calls/month; Premium ~$99/mo; PAYG from ~$0.01/unit (LOW). — [Capterra Canopy](https://www.capterra.com/p/10045057/Canopy-API/); [agentdeals Canopy](https://agentdeals.dev/vendor/canopy)
- **Jungle Scout API / Cobalt**: Cobalt (enterprise) custom pricing; a Jungle Scout API exists for "self-serve tools and dynamic data reports"; API requests reportedly included (100) on Growth Accelerator and Brand Owner+CI tiers (MED-LOW). — [Jungle Scout pricing](https://junglescout.com/?p=108222); [RevenueGeeks JS pricing](https://revenuegeeks.com/software/jungle-scout/pricing)
- **SmartScout API**: only via Enterprise options (custom pricing); public plans $29–$187/mo (MED-LOW). — [SmartScout pricing](https://smartscout.com/pricing); [RevenueGeeks SmartScout API](https://revenuegeeks.com/software/smartscout/api)
- **Helium 10 MCP**: launched 2026-07-16; no separate fee but requires Diamond plan or higher (~$359/mo, $279/mo annual); tools include Magnet/Cerebro keywords, Black Box, Brand Analytics/SQP, Keyword Tracker; marketplaces US, UK, DE, JP, CA, AU, FR, ES, IT, NL, PL, SE, MX; KB mentions 10,000 API calls/month (conflicting with "no metered calls") (MED). — [Helium 10 blog: MCP](https://www.helium10.com/blog/helium-10-mcp/); [Helium 10 KB: Getting Started with MCP](https://kb.helium10.com/hc/en-us/articles/51580564409883-Getting-Started-with-Helium-10-MCP); [RevenueGeeks H10 MCP](https://revenuegeeks.com/software/helium-10/mcp)

### Inferences
- Helium 10 MCP and Jungle Scout API are licensed for the subscriber's own use; using them as a backend to resell data to your SaaS users almost certainly requires an enterprise/data licence (not verified — check ToS).
- For keyword search volume, DataForSEO is the cheapest documented independent source (ESTIMATED volumes by the vendor).

### Gaps
- Redistribution/resale clauses of each provider's ToS (not read). Data provenance/methods of Rainforest/Canopy (presumably scraping). EU marketplace coverage per provider.

---

## Q6. Legality of scraping Amazon

### Takeaway
Scraping public Amazon pages is not per se a crime in the US after hiQ (9th Cir.) and the 2026 Ninth Circuit Amazon v. Perplexity ruling, but Amazon's Conditions of Use expressly prohibit robots/data-extraction tools, and contract claims are enforceable (hiQ lost on breach of contract; CJEU Ryanair allows contractual bans on unprotected databases in the EU). Amazon actively litigates against automated access (Perplexity, Nov 2025). For an EU SaaS, the sui generis database right is an additional exposure.

### Cited Findings
- Amazon Conditions of Use (last updated 2025-05-30 per search snippet) license excludes "any use of data mining, robots, or similar data gathering and extraction tools"; licenses terminate on non-compliance (MED — wording confirmed via search; official page not machine-fetched). — [ConductAtlas: CoU provision](https://conductatlas.com/platform/amazon/amazon-conditions-of-use/provision/CA-P-018441/prohibition-on-data-mining-and-scraping-tools/); [Thunderbit summary](https://thunderbit.com/blog/is-scraping-amazon-legal)
- amazon.com robots.txt (fetched 2026-11-11) disallows for `User-agent: *` a list of paths incl. `/gp/cart`, `/gp/sign-in`, `/gp/product/product-availability`, `/exec/obidos/handle-buy-box`, `/gp/customer-reviews/write-a-review.html`, `/gp/history` etc. (HIGH; first 40 lines only checked — product detail pages `/dp/` were not in the excerpt viewed). — [amazon.com/robots.txt](https://www.amazon.com/robots.txt)
- hiQ v. LinkedIn: on 2022-11-04 the N.D. Cal. held hiQ breached LinkedIn's User Agreement (scraping + fake profiles), anti-scraping provisions enforceable as contract; consent judgment Dec 2022: $500,000 against hiQ, permanent injunction, deletion of scraped data/code (HIGH-MED, law-firm summaries). — [Proskauer New Media Law](https://newmedialaw.proskauer.com/2022/12/08/hiq-and-linkedin-reach-proposed-settlement-in-landmark-scraping-case/); [ZwillGen](https://www.zwillgen.com/alternative-data/hiq-v-linkedin-wrapped-up-web-scraping-lessons-learned/); [Morgan Lewis](https://www.morganlewis.com/blogs/sourcingatmorganlewis/2022/12/linkedin-v-hiq-landmark-data-scraPing-suit-provides-guidance-to-data-scrapers-and-web-operators)
- Ryanair v PR Aviation (CJEU C-30/14, 2015-01-15): where a database is protected neither by copyright nor sui generis right, the Database Directive does not prevent its maker from imposing contractual limits on use by third parties (screen-scraping of flight data) (HIGH-MED). — [SCL commentary](https://www.scl.org/3280-the-cjeu-takes-flight-databases-and-air-fares/); [Kluwer Copyright Blog](https://copyrightblog.kluweriplaw.com/2015/01/26/ryanair-ltd-v-pr-aviation-bv-contracts-rights-and-users-in-a-low-cost-database-law/?output=pdf)
- Amazon v. Perplexity (Comet agentic browser): suit filed Nov 2025 under CFAA and California computer-fraud law, alleging Comet disguised automated sessions as Chrome; March 2026 preliminary injunction (Judge Chesney: access "with the Amazon user's permission, but without authorization by Amazon"); Ninth Circuit reversed ~2026-08-04, holding Amazon unlikely to succeed on CFAA because the users, not Perplexity, "accessed" the platform; "We do not establish a new legal regime governing agentic AI." Case continues (MED). — [Decrypt, 2026-08-05](https://decrypt.co/374996/perplexity-amazon-ai-agent-lawsuit?amp=1); [GeekWire, 2026-03-10](https://www.geekwire.com/2026/03/10/judge-blocks-perplexitys-ai-bot-from-shopping-on-amazon-in-early-test-of-agentic-commerce/); [Bloomberg Law](https://news.bloomberglaw.com/ip-law/amazon-wins-court-order-blocking-perplexitys-ai-shopping-bots)

### Inferences
- Risk ranking (for a SaaS): (1) contractual/CoU breach + account termination — HIGH likelihood if detected, and your company may have Amazon seller/developer accounts at stake (SP-API AUP 4.3 cross-contamination); (2) EU sui generis right (Directive 96/9/EC art. 7) — Amazon's catalog/offer database likely involves substantial investment, so systematic extraction of substantial parts could infringe (not verified with case law in this session); (3) CFAA criminal/civil — reduced after hiQ and the Perplexity appeal, especially for user-driven access (extension running in the user's own browser fits the Ninth Circuit's "users accessed" reasoning best).
- A browser extension that reads the page the user is viewing (user-initiated, no bot fleet) is materially lower-risk than server-side crawling, but still arguably "data gathering ... tools" under the CoU.

### Gaps
- Amazon litigation directly against seller-tool scrapers (Keepa, Jungle Scout, etc.): none found. CJEU sui generis cases on aggregators (e.g. CV-Online Latvia C-762/19) not fetched this session. French-law specifics (Code de la propriété intellectuelle L.342-1) not researched.

---

## Q7. How sales estimates are produced & their accuracy

### Takeaway
Units-sold numbers in seller tools are ESTIMATED from BSR→sales curves (calibrated with panel/seller data) and/or rank-drop counting; Amazon's "X+ bought in past month" badge is a coarse OBSERVED bucket. Published accuracy figures are vendor-run and contradictory (Helium 10 claims 89.6% vs JS 60%; Jungle Scout claims 84.1% vs H10 74%); small independent tests show large errors (e.g. ~-51% bias).

### Cited Findings
- Helium 10 study: 89.59% accuracy across 29,906 products in 32 categories vs 60.00% Jungle Scout (vendor-run) (MED as to claim, LOW as to truth). — [Helium 10 blog](https://www.helium10.com/blog/helium-10-jungle-scout-amazon-sales-data-accuracy/)
- Jungle Scout claims 84.1% vs Helium 10 74% (vendor-run). — [Jungle Scout vs Helium 10](https://www.junglescout.com/blog/jungle-scout-vs-helium-10/)
- Independent small test: Helium 10 closer in 18/25 products, but ~-51% systematic underestimate (LOW). — [EcomCrew](https://www.ecomcrew.com/helium10-vs-junglescout/)
- Jungle Scout publishes updates to its estimation algorithm. — [Jungle Scout: Amazon sales estimates update](https://www.junglescout.com/blog/amazon-sales-estimates-update)
- AUP 2.4 requires SP-API apps to "be explicit about any calculations and the use of models ... their accuracy and data freshness." (HIGH) — [AUP](https://sellercentral.amazon.com/mws/static/policy?documentType=AUP&locale=en_US)
- Amazon offers seller-own demand forecasts (P70/P80/P90 weekly) in analytics reports — vendor-scoped, not market-wide (HIGH). — [Analytics Reports](https://developer-docs.amazon/sp-api/docs/report-type-values-analytics.md)

### Inferences
- A new entrant can build a BSR curve from the "bought in past month" buckets (via Keepa or scraping) + rank history; accuracy will be bucket-limited and must be disclosed (AUP 2.4).

### Gaps
- No independent study of Keepa "monthly sold" or Amazon badge accuracy found. Incumbents' panel sizes not documented.

---

## Q8. How incumbents obtain data

### Takeaway
Documented evidence is thin: Seller Assistant openly combines Keepa + SP-API; SellerAmp displays Keepa data alongside SP-API-driven eligibility/fees; Helium 10 markets data "Amazon can't give you" (i.e. non-SP-API sources) and also pulls Brand Analytics/SQP from authorized accounts.

### Cited Findings
- Seller Assistant API "merges the power of Keepa and Amazon SP API into a single platform" (MED, vendor). — [Seller Assistant API](https://www.sellerassistant.app/blog/seller-assistant-api/)
- SellerAmp alerts panel covers eligibility, hazmat, IP-complaint risk, meltable, private label, variations (MED, vendor). — [SellerAmp Alerts Panel tutorial](https://selleramp.com/selleramp-alerts-panel-tutorial/)
- SellerAmp shows estimated sales, profit calc, BSR, competitor offers and Keepa data (LOW, competitor blog). — [Seller Assistant: SellerAmp vs Keepa](https://sellerassistant.app/blog/selleramp-vs-keepa)
- Helium 10 MCP marketed as "the only marketplace intelligence MCP with data that Amazon can't give you"; includes Brand Analytics / SQP tools (MED). — [Helium 10 blog](https://www.helium10.com/blog/helium-10-mcp/); [anythingmcp H10 connector](https://anythingmcp.com/marketplace/helium10)
- A developer cited SellerAmp (>100k users, Keepa charts) as apparently combining Keepa with SP-API, contrary to the SP-API team's reported position (LOW). — [Seller Forums](https://sellercentral.amazon.com/seller-forums/discussions/t/a7961c30-b453-4dcc-9a31-e1b6312d36b0)

### Inferences
- IP-complaint flags are likely crowd-sourced/user-reported or proprietary lists (no Amazon API exposes other sellers' IP complaints); hazmat flags can come from SP-API (e.g. restrictions/FBA eligibility) or catalog attributes — unverified.

### Gaps
- No primary documentation of Helium 10/Jungle Scout scraping or panel methods; SellerAmp's precise SP-API usage not documented publicly.

---

## Q9. Chrome extension constraints (Manifest V3, Chrome Web Store)

### Takeaway
MV3 forbids remotely hosted code (all executable logic must ship in the package; fetched JSON data is fine, but no remote "command interpreters"), and user-data policies (Limited Use, privacy policy) apply. Nothing found that bans reading the Amazon page the user is on.

### Cited Findings
- RHC = "anything that is executed by the browser that is loaded from someplace other than the extension's own files"; data like JSON/CSS is not RHC; violations tagged "Blue Argon"; building an interpreter for remotely fetched commands counts as a violation; isolated/sandboxed code still must comply with Limited Use and privacy policy (HIGH). — [Chrome: Deal with remote hosted code violations](https://developer.chrome.com/docs/extensions/develop/migrate/remote-hosted-code); [Chrome Web Store: MV3 requirements](https://developer.chrome.com/docs/webstore/program-policies/mv3-requirements); [Troubleshooting CWS violations](https://developer.chrome.com/docs/webstore/troubleshooting)

### Inferences
- Amazon frequently changes page DOM; under MV3 parsers can't be hot-patched as code — selectors must be shipped as data (allowed) or via store updates (review delay).

### Gaps
- Chrome Web Store User Data/Limited Use detail and Amazon-specific extension takedowns not researched.

---

## Q10. Feature → data-source mapping (synthesis)

### Takeaway
Seller-specific features (fees, restrictions/ungating, Buy Box eligibility, FOEP) are cleanly served by SP-API per authorized seller. Market-intelligence features (price/BSR history, sales estimates, keyword volume, competitor/brand intel) require non-Amazon sources (Keepa/scrapers/DataForSEO) — which is where AUP 4.3 and redistribution licences bite.

### Cited Findings (each row cites its source; type in brackets)
| Feature | Primary source | Data type | Key constraint |
|---|---|---|---|
| Profit calculator | SP-API getMyFeesEstimate(s) + getItemOffers price — [fees ref](https://developer-docs.amazon/sp-api/reference/getmyfeesestimateforasin.md) | CALCULATED (fees, Amazon-computed; "actual costs may vary") | per-seller token; 1 rps / 0.5 rps×20 |
| Fee estimate | same | CALCULATED | catalog-size based, may differ from real size |
| Restrictions / ungating check | getListingsRestrictions — [ref](https://developer-docs.amazon/sp-api/reference/getlistingsrestrictions.md) | OBSERVED, seller-specific | must use that seller's authorization; 5 rps |
| Price & BSR history | Keepa API — [RevenueGeeks](https://revenuegeeks.com/software/keepa/api); scrapers | OBSERVED by third party (crawled) | Keepa ToS unknown; AUP 4.3 if inside SP-API app; SP-API data can't be pooled into a shared history DB (AUP 4.4/4.6) |
| Sales estimates | Keepa/scraped BSR + badges; incumbents' models — [H10 study](https://www.helium10.com/blog/helium-10-jungle-scout-amazon-sales-data-accuracy/) | ESTIMATED | disclose model & accuracy (AUP 2.4) |
| Keyword search volume | DataForSEO Amazon — [pricing](https://dataforseo.com/pricing/dataforseo-labs/dataforseo-amazon-api); Brand Analytics (own brand only) — [analytics](https://developer-docs.amazon/sp-api/docs/report-type-values-analytics.md) | ESTIMATED (3rd-party); Amazon gives rank not volume | Brand Registry + BA role required |
| Competitor / brand intelligence | Scrapers, Keepa, SmartScout/JS enterprise APIs — [SmartScout](https://revenuegeeks.com/software/smartscout/api) | OBSERVED+ESTIMATED | licences custom; AUP 4.5 bans sharing "insights about Amazon's business" |
| Wholesale bulk scan | SP-API (fees, restrictions, offers) per user + Keepa for history | mixed | per-user rate limits (≈1,800 offer lookups/h); Keepa tokens shared |
| Buy Box ownership | getCompetitiveSummary (featured buying options), getItemOffers — [ref](https://developer-docs.amazon/sp-api/reference/getcompetitivesummary.md) | OBSERVED | 0.033 rps; snapshot only |
| Offer counts | getItemOffers / Keepa history | OBSERVED | snapshot vs history |
| IP complaint / hazmat flags | No Amazon API for others' IP complaints; hazmat partly via restrictions/catalog — [SellerAmp alerts](https://selleramp.com/selleramp-alerts-panel-tutorial/) | ESTIMATED/crowd-sourced (inferred) | data provenance unclear |

### Inferences
- Lowest-risk architecture: (a) SP-API public app listed on the Appstore (unlimited authorizations) for all seller-specific features, strictly per-tenant, no cross-tenant cache; (b) market history via user's own Keepa key (BYO) or a separately licensed provider, isolated, with a written legal opinion / Amazon Developer Support confirmation on AUP 4.3 before launch.
- Unit economics are dominated by third-party data (Keepa €49–459+/mo; scrapers ~$0.3–1.5/1k records), since SP-API is currently free.

### Gaps
- Written confirmation from Amazon on AUP 4.3 scope; Keepa licensing terms; whether hazmat status is directly exposed by an SP-API endpoint (e.g. FBA inbound eligibility) — not verified in this session.
