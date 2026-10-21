"""Check hero/model lookup and layout against a local server."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('UI_BASE_URL', 'http://127.0.0.1:8000')
OUTPUT = Path(__file__).resolve().parents[1] / '.taste-skill/attack-speed-qa'


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        options = {'headless': True}
        if executable := os.environ.get('UI_BROWSER_PATH'):
            options['executable_path'] = executable
        browser = p.chromium.launch(**options)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'{BASE}/attack-speed.html#hero=ngokhong&form=0')
        expect(page.locator('.speed-hero-card')).to_have_count(130)
        expect(page.locator('dialog,input[type=number]')).to_have_count(0)
        expect(page.locator('#matrix-body tr')).to_have_count(20)
        page.locator('.speed-hero-card[data-id=ngokhong]').click()
        expect(page.locator('#matrix-hero-model')).to_have_text('Model C')
        expect(page.locator('thead .selected-model')).to_have_text('C')
        page.locator('.speed-hero-card[data-id=liliana]').click()
        page.locator('#board-form-select').select_option('1')
        expect(page.locator('#matrix-hero-model')).to_contain_text('H-1f')
        page.locator('.speed-hero-card[data-id=yena]').click()
        page.locator('#board-form-select').select_option('1')
        expect(page.locator('#matrix-hero-model')).to_have_text('Model F')
        page.locator('.speed-hero-card[data-id=preyta]').click()
        expect(page.locator('#matrix-hero-model')).to_contain_text('chưa đủ mốc')
        expect(page.locator('#hero-note')).to_contain_text('178')
        expect(page.locator('#hero-evidence a[href*="sn=333724"]')).to_have_count(1)
        for hero in ['heino', 'capheny']:
            page.locator(f'.speed-hero-card[data-id={hero}]').click()
            expect(page.locator('thead .selected-model')).to_have_count(0)
            expect(page.locator('#hero-note')).to_be_visible()
        page.locator('#directory-search').fill('dieu thuyen')
        expect(page.locator('.speed-hero-card')).to_have_count(1)
        page.locator('.speed-hero-card').click()
        expect(page.locator('#matrix-hero-name')).to_have_text('Điêu Thuyền')
        page.locator('#directory-search').fill('zzzzzz')
        expect(page.locator('#directory-empty')).to_be_visible()
        page.locator('#directory-search').fill('')
        page.locator('#directory-filter').select_option('E')
        expect(page.locator('.speed-hero-card[data-id=preyta]')).to_have_count(1)
        page.locator('#directory-filter').select_option('unknown')
        assert 0 < page.locator('.speed-hero-card').count() < 130
        page.locator('#directory-filter').select_option('all')
        page.locator('#settings-menu summary').click()
        page.get_by_role('button', name='Sáng', exact=True).click()
        page.locator('#settings-menu summary').click()
        for width in [1440, 768, 390]:
            page.set_viewport_size({'width': width, 'height': 900 if width == 1440 else 844})
            if width <= 760:
                page.locator('button[data-pane=heroes]').click()
            page.locator('.speed-hero-card[data-id=valhein]').click()
            expect(page.locator('#matrix-hero-name')).to_have_text('Valhein')
            expect(page.locator('.model-panel')).to_be_visible()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Overflow at {width}px'
            if width == 390:
                page.screenshot(path=str(OUTPUT / 'frames-390.png'), full_page=True)
                page.locator('button[data-pane=heroes]').click()
            page.locator('.hero-picker-scroll').evaluate('el => { el.scrollTop = 0; }')
            page.screenshot(path=str(OUTPUT / f'picker-{width}.png'), full_page=True)
        page.goto(f'{BASE}/index.html')
        expect(page.locator('.hero-card')).to_have_count(130)
        assert page.locator('html').get_attribute('data-theme') == 'light'
        page.get_by_role('link', name='Tốc đánh', exact=True).click()
        expect(page.locator('.speed-hero-card')).to_have_count(130)
        assert not errors, errors
        browser.close()
    print('PASS: selection, variants, missing data, provenance, filters, shared theme, navigation and 3 widths; no JS errors')


if __name__ == '__main__':
    main()
