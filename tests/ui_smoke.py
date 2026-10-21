"""Browser regression checks. Start the static server before running this script."""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("UI_BASE_URL", "http://127.0.0.1:8000")
OUTPUT = ROOT / ".taste-skill" / "qa"
HEROES = {hero["id"]: hero for hero in json.loads((ROOT / "data/crawled_heroes.json").read_text(encoding="utf-8"))}


def no_overflow(page):
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Horizontal page overflow"


def choose_first(page):
    page.locator(".hero-card:not(:disabled)").first.click()


def open_settings(page):
    menu = page.locator("#settings-menu")
    if menu.get_attribute("open") is None:
        menu.locator("summary").click()


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as playwright:
        options = {"headless": True}
        if executable := os.environ.get("UI_BROWSER_PATH"):
            options["executable_path"] = executable
        browser = playwright.chromium.launch(**options)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(URL)
        page.wait_for_load_state("networkidle")
        expect(page.locator(".hero-card")).to_have_count(len(HEROES))
        expect(page.locator("#pick-slots-blue .pick-slot")).to_have_count(5)
        expect(page.locator("#pick-slots-red .pick-slot")).to_have_count(5)
        expect(page.locator(".rec-card")).to_have_count(6)
        expect(page.locator("#status-text")).to_have_text("Đội Xanh chọn tướng")
        expect(page.locator("#turn-count")).to_have_text("Lượt 1 / 10")
        no_overflow(page)
        page.screenshot(path=str(OUTPUT / "desktop-empty.png"), full_page=True)

        search = page.get_by_label("Tìm tướng", exact=True)
        page.keyboard.press("/")
        expect(search).to_be_focused()
        search.fill("dieu thuyen")
        expect(page.locator(".hero-card")).to_have_count(1)
        expect(page.locator(".hero-card")).to_have_attribute("data-id", "dieuthuyen")
        search.fill("khong-co-tuong-nay")
        expect(page.locator(".grid-empty")).to_be_visible()
        expect(page.locator("#hero-count")).to_have_text("0 tướng")
        page.get_by_role("button", name="Xóa tìm kiếm", exact=True).click()
        page.locator("#role-filters [data-role=Mid]").click()
        ids = page.locator(".hero-card").evaluate_all("cards => cards.map(card => card.dataset.id)")
        assert ids and all(HEROES[hid]["main_role"] == "Mid" for hid in ids)
        page.locator("#role-filters [data-role=all]").click()
        page.locator("#sort-select").select_option("tier")
        first_id = page.locator(".hero-card").first.get_attribute("data-id")
        assert HEROES[first_id]["tier"] == "S+"
        page.locator("#rec-role-select").select_option("SP")
        assert all("SP" in item for item in page.locator(".rec-hero-details p").all_text_contents())
        page.locator("#rec-modes [data-mode=meta]").click()
        expect(page.locator("#rec-modes [data-mode=meta]")).to_have_attribute("aria-pressed", "true")
        page.locator("#rec-role-select").select_option("all")
        page.locator(".rec-reason-details summary").first.click()
        expect(page.locator(".rec-reason-details").first).to_have_attribute("open", "")
        page.locator(".btn-rec-select").first.click()
        expect(page.locator("#pick-slots-blue .filled")).to_have_count(1)
        expect(page.locator("#status-text")).to_have_text("Đội Đỏ chọn tướng")
        page.locator("#btn-undo").click()
        expect(page.locator("#pick-slots-blue .filled")).to_have_count(0)
        expect(page.locator("#turn-count")).to_have_text("Lượt 1 / 10")

        open_settings(page)
        page.locator("[data-theme-val=light]").click()
        expect(page.locator("html")).to_have_attribute("data-theme", "light")
        page.reload()
        page.wait_for_load_state("networkidle")
        expect(page.locator("html")).to_have_attribute("data-theme", "light")
        page.screenshot(path=str(OUTPUT / "desktop-light.png"), full_page=True)
        open_settings(page)
        page.locator("[data-theme-val=dark]").click()
        page.locator("#skip-ban-checkbox").uncheck()
        page.keyboard.press("Escape")
        expect(page.locator("#status-text")).to_have_text("Đội Xanh cấm tướng")
        expect(page.locator(".rec-empty-state")).to_be_visible()
        for _ in range(10):
            choose_first(page)
        expect(page.locator(".ban-slot.filled")).to_have_count(10)
        expect(page.locator("#turn-count")).to_have_text("Lượt 1 / 10")
        for _ in range(6):
            choose_first(page)
        no_overflow(page)
        page.screenshot(path=str(OUTPUT / "desktop-populated.png"), full_page=True)
        for _ in range(4):
            choose_first(page)
        expect(page.locator("#pick-slots-blue .filled")).to_have_count(5)
        expect(page.locator("#pick-slots-red .filled")).to_have_count(5)
        expect(page.get_by_role("dialog")).to_be_visible()
        expect(page.locator("#btn-overlay-close")).to_be_focused()
        page.keyboard.press("Shift+Tab")
        expect(page.locator("#btn-overlay-reset")).to_be_focused()
        page.screenshot(path=str(OUTPUT / "analysis.png"), full_page=True)
        page.keyboard.press("Escape")
        expect(page.get_by_role("dialog")).not_to_be_visible()
        page.locator("#btn-analysis").click()
        expect(page.get_by_role("dialog")).to_be_visible()
        page.locator("#btn-overlay-reset").click()
        expect(page.locator(".pick-slot.filled")).to_have_count(0)
        expect(page.locator(".ban-slot.filled")).to_have_count(0)

        # Independent mobile session: verify tabs, picks and a narrow viewport.
        mobile = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        phone = mobile.new_page()
        phone.on("pageerror", lambda error: errors.append(str(error)))
        phone.goto(URL)
        phone.wait_for_load_state("networkidle")
        no_overflow(phone)
        expect(phone.locator(".selection-panel")).to_be_visible()
        expect(phone.locator(".recommendation-panel")).not_to_be_visible()
        phone.locator("[data-view=recommendations].workspace-tab").click()
        expect(phone.locator(".recommendation-panel")).to_be_visible()
        expect(phone.locator(".selection-panel")).not_to_be_visible()
        phone.locator(".btn-rec-select").first.click()
        expect(phone.locator("#pick-slots-blue .filled")).to_have_count(1)
        phone.screenshot(path=str(OUTPUT / "mobile-recommendations.png"), full_page=True)
        phone.locator("[data-view=heroes].workspace-tab").click()
        phone.screenshot(path=str(OUTPUT / "mobile-heroes.png"), full_page=True)
        for width in (360, 600, 768, 1024):
            phone.set_viewport_size({"width": width, "height": 900})
            no_overflow(phone)
        phone.set_viewport_size({"width": 768, "height": 1024})
        phone.screenshot(path=str(OUTPUT / "tablet.png"), full_page=True)
        assert not errors, errors
        mobile.close()
        context.close()
        browser.close()
    print("OK: desktop/mobile draft, bans, recommendations, search, filters, themes, undo/reset, dialog focus and overflow")


if __name__ == "__main__":
    main()
