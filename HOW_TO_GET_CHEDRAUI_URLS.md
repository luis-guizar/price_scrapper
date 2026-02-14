
# Obtaining Chedraui URLs for Scraping

To get valid URLs for the `chedraui_example_api_urls.txt` file:

1.  Open your browser (Chrome/Edge/Firefox) and go to **[https://www.chedraui.com.mx/](https://www.chedraui.com.mx/)**.
2.  Open **Developer Tools**:
    *   Press `F12` or `Ctrl+Shift+I`.
    *   Click on the **Network** tab.
3.  Filter the network requests:
    *   In the "Filter" box (top left of the Network tab), type `graphql` or `productSearchV3`.
4.  Perform a search or navigate to a category on the website:
    *   Example: Search for "Laptops" or click "Tecnología -> Computación".
5.  Look for a network request in the list:
    *   It will likely be named `graphql` or have a long query string.
    *   Click on it and check the **Preview** or **Response** tab to verify it contains product data (`data.productSearch.products`).
6.  Copy the URL:
    *   Right-click the request name in the list.
    *   Select **Copy** -> **Copy Link Address** (or **Copy URL**).
7.  Paste this full URL into `chedraui_example_api_urls.txt`.

**Note:** The scraper now handles the complex pagination encoding automatically, so any valid search URL should work.
