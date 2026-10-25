import asyncio
import re
from playwright import async_api
from playwright.async_api import expect

async def run_test():
    pw = None
    browser = None
    context = None

    try:
        # Start a Playwright session in asynchronous mode
        pw = await async_api.async_playwright().start()

        # Launch a Chromium browser in headless mode with custom arguments
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--window-size=1280,720",
                "--disable-dev-shm-usage",
                "--ipc=host",
                "--single-process"
            ],
        )

        # Create a new browser context (like an incognito window)
        context = await browser.new_context()
        # Wider default timeout to match the agent's DOM-stability budget;
        # auto-waiting Playwright APIs (expect, locator.wait_for) inherit this.
        context.set_default_timeout(15000)

        # Open a new page in the browser context
        page = await context.new_page()

        # Interact with the page elements to simulate user flow
        # -> navigate
        await page.goto("http://localhost:8501")
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        
        # -> Scroll to the “Next-Month Habit Commitment” section and inspect the available commitment controls.
        await page.mouse.wheel(0, 300)
        
        # -> Commit to monitoring the selected 15-Minute Post-Loss Buffer rule next month.
        # ✅ Commit to Monitoring This Rule Next Month button
        elem = page.get_by_test_id("stBaseButton-primary")
        await elem.click(timeout=10000)
        
        # --> Assertions to verify final state
        
        # --> The commitment is recorded in the session.
        # Assert-outcome: not verified — the export-time check could not be evaluated
        # Assert: The session URL should indicate that the commitment was recorded.
        await expect(page).to_have_url(re.compile("committed=1"), timeout=15000), "The session URL should indicate that the commitment was recorded."
        
        # --> The selected 15-Minute Post-Loss Buffer rule is shown as committed for next month.
        # Assert-outcome: not verified — the export-time check could not be evaluated
        # Assert: The page should show the selected rule as committed for next month.
        await expect(page.locator("#root").nth(0)).to_contain_text("Committed to: 15-Minute Post-Loss Buffer for next month.", timeout=15000), "The page should show the selected rule as committed for next month."
        await asyncio.sleep(5)

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()

asyncio.run(run_test())
    