# Local Beauty Industry Market Analysis & Lead Generation

**Role:** Data Analyst  
**Tech Stack:** Power BI (DAX, Data Modeling), Python (Pandas, Playwright), Outscraper

**[🔗 View the Live Interactive Dashboard](https://app.powerbi.com/view?r=eyJrIjoiYmEzZDMxN2EtOGU3Zi00YTE0LWE5OWItNTllNmE1OWZjN2QzIiwidCI6ImRjYzhiMTE5LTEzZTYtNDc5Mi1iZTMwLTU5NzU5M2RhYmZiZiIsImMiOjEwfQ%3D%3D)**  
**[📄 View Dashboard Presentation (PDF)](./Visual_Report_Beauty_Salons.pdf)**

### The Business Problem
Identifying viable leads for custom web development within the local personal care sector in Parañaque and Marcelo Green. The objective was to map the total market opportunity of salons operating without digital storefronts and quantitatively prove the ROI of a dedicated website versus relying solely on social media platforms.

### Methodology & Execution
* **Data Extraction & Cleaning:** Engineered a data pipeline utilizing Outscraper and Python (Playwright) to extract business directory data for local salons. Leveraged Pandas to clean raw outputs, handle missing values, and remove duplicate directory entries, resulting in a pristine dataset of 119 verified businesses.
* **Data Modeling & BI Development:** Imported the cleaned CSV into Power BI to build an interactive, executive-facing dashboard. 
* **Automated Formatting:** Wrote custom DAX measures (`SWITCH` logic) to automate conditional formatting, ensuring visual consistency across all charts based on precise category conditions without manual color mapping.

### Key Insights & Impact
* **Demonstrated ROI:** Proved that local salons with dedicated websites average 173.11 reviews, heavily outperforming businesses with only social media links (49.05) or no digital footprint (32.29).
* **Actionable Market Opportunity:** Visualized a massive gap in the market, revealing that over 50% of local salons lack any web link, and 85% lack a dedicated website. 
* **Lead Generation Engine:** Built a fully interactive cross-filtering table that allows stakeholders to isolate non-digitized businesses, providing a prioritized, data-backed prospect list for direct outreach.
