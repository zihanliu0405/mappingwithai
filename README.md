# mappingwithai
# California PCOS care-access research page

Open `index.html` with **Live Server** in VS Code (right-click → Open with Live Server). No build step or package installation is needed. Serve the project root so relative data paths resolve. Do not open via `file://`.

The single page includes a MapLibre GL JS county choropleth over a grayscale CARTO Positron vector-tile basemap, a county selector, and linked D3 uncertainty and uninsured-count charts. Libraries, web fonts, and basemap tiles require internet access. No API key is configured or required for the basemap. Attribution is retained on the map.

The map measures uninsured percentages among women ages 19–44 (ACS 2020–2024), as context for potential PCOS care access. It does not map PCOS prevalence. See `data/pcos_access/README.md` for source and calculation details. Map bands are fixed at 5, 8, 11 and 15 percent; derived 90% margins of error appear in the county panel and comparison chart.

Files: `index.html`, `styles.css`, `app.js`; existing CSV and joined GeoJSON in `data/pcos_access/`. There is no separate map page because the map and charts share county selection on the main page.
