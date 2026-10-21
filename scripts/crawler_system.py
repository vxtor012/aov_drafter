# -*- coding: utf-8 -*-
"""
AoV / Liên Quân Mobile - roster, ranked meta, lane, and counter data crawler.
1. Queries AOV Builds for the Vietnamese hero roster, names, and avatars.
2. Reads Thailand ranked stats and lane profiles from RoVGuide, and refuses to save incomplete snapshots.
3. Reads RovMeta as a counter fallback/reference, never as a lane classifier.
4. Crawls AOV Builds counter guides and embeds the synchronized data in app.js.
"""

import os
import json
import requests
import re
import time
import unicodedata
import concurrent.futures
import sys
from pathlib import Path
from datetime import datetime, timezone
from bs4 import BeautifulSoup
if __package__:
    from .validate_data import validate_database
else:
    from validate_data import validate_database

ROOT = Path(__file__).resolve().parents[1]

# --- CONFIGURATION & ENDPOINTS ---
AOV_BUILDS_URL = "https://aov-builds.com/tuong/"
ROVMETA_URL = "https://rovmeta.com"
ROVGUIDE_META_URL = "https://rovguide.com/meta"
ROVGUIDE_HEROES_URL = "https://rovguide.com/heroes"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://aov-builds.com/"
}

# Translate aov-builds Vietnamese slug IDs to RovMeta English IDs
AOV_TO_ROVMETA = {
    "dieu-thuyen": "diaochan",
    "lu-bo": "lubu",
    "ngo-khong": "wukong",
    "trieu-van": "zanis",
    "richter": "riktor",
    "celica": "celica", # Brunhilda/Celica
    "stuart": "stuart",
    "kaine": "kaine",
    "helen": "helen",
    "payna": "payna",
    "the-joker": "thejoker",
    "azzenka": "azzenka",
    "jinna": "jinnar"
}

# Map legacy/different English names found in counters to modern local IDs
UNMATCHED_REPLACEMENTS = {
    "payna": "helen",
    "mortos": "arthur",
    "batman": "kaine",
    "brunhilda": "celica",
    "thejoker": "stuart"
}

# RoVGuide uses Global/Thai English hero slugs; local Vietnamese IDs do not always match.
ROVGUIDE_SLUG_OVERRIDES = {
    "boltbaron": "bolt-baron",
    "celica": "brunhilda",
    "dieuthuyen": "diao-chan",
    "flowborn": "flowborn-archer",
    "flowbornphep": "flowborn-mage",
    "jinna": "jinna",
    "lubo": "lu-bu",
    "ngokhong": "wukong",
    "richter": "richter",
    "theflash": "the-flash",
    "trieuvan": "zanis",
    "wonderwoman": "wonder-woman",
}

LANE_TO_APP_ROLE = {
    "slayer lane": "Top",
    "middle lane": "Mid",
    "mid": "Mid",
    "jungle": "Jungle",
    "dragon lane": "AD",
    "support lane": "SP",
    "support": "SP",
}

TIER_TO_APP_TIER = {"T0": "S+", "T1": "S", "T2": "A", "T3": "B", "T4": "C"}

# Official Vietnamese patch references are recorded for cross-checks only. The
# active lane data remains sourced from the Thai profiles, as requested.
OFFICIAL_VN_ROLE_CROSSCHECKS = {
    "astrid": "https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-le-hoi-5v5-08-04-2026/"
}

def remove_accents(input_str):
    """Normalize unicode characters and filter out combining diacritics (accents)."""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def clean_id(name):
    """Converts a display name into a clean, unique lowercase alphanumeric ID."""
    cleaned = remove_accents(name.lower())
    cleaned = cleaned.replace('đ', 'd').replace('’', '').replace("'", "")
    cleaned = "".join([c for c in cleaned if c.isalnum()])
    return cleaned


def fetch_rovguide_reference_data(hero_ids):
    """Fetch current Thailand ranked metrics and lane profiles as separate signals."""
    response = requests.get(ROVGUIDE_META_URL, headers=HEADERS, timeout=20)
    response.raise_for_status()
    meta_soup = BeautifulSoup(response.content, "html.parser")
    ranked_table = meta_soup.find("table", attrs={"aria-labelledby": "ranked-heading"})
    if not ranked_table:
        raise RuntimeError("RoVGuide ranked table was not found; refusing to reuse stale meta data.")

    ranked = {}
    for row in ranked_table.select("tbody tr"):
        link = row.select_one("a[href^='/heroes/']")
        cells = row.find_all("td", recursive=False)
        if not link or len(cells) < 4:
            continue
        slug = link.get("href", "").rstrip("/").split("/")[-1]
        values = [re.search(r"\d+(?:\.\d+)?", cell.get_text(" ", strip=True)) for cell in cells[-3:]]
        tier_label = row.select_one(".meta-table-hero-copy small")
        tier_match = re.search(r"\bT[0-4]\b", tier_label.get_text(" ", strip=True) if tier_label else "")
        if slug and all(values) and tier_match:
            ranked[slug] = {
                "win_rate": float(values[0].group()),
                "pick_rate": float(values[1].group()),
                "ban_rate": float(values[2].group()),
                "tier": TIER_TO_APP_TIER[tier_match.group()],
            }

    if len(ranked) < max(20, int(len(hero_ids) * 0.9)):
        raise RuntimeError(f"RoVGuide ranked data incomplete ({len(ranked)}/{len(hero_ids)}).")

    page_text = meta_soup.get_text(" ", strip=True)
    date_match = re.search(r"Ranked data\s+(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})", page_text)
    if not date_match:
        raise RuntimeError("RoVGuide ranked snapshot date was not found.")
    date_value = " ".join(date_match.groups())
    try:
        snapshot = datetime.strptime(date_value, "%d %b %Y").date().isoformat()
    except ValueError:
        snapshot = datetime.strptime(date_value, "%d %B %Y").date().isoformat()

    def read_roles(hero_id):
        slug = ROVGUIDE_SLUG_OVERRIDES.get(hero_id, hero_id)
        page = requests.get(f"{ROVGUIDE_HEROES_URL}/{slug}", headers=HEADERS, timeout=15)
        page.raise_for_status()
        soup = BeautifulSoup(page.content, "html.parser")
        for block in soup.select("dl.hero-detail-profile div"):
            label = block.find("dt")
            value = block.find("dd")
            if label and label.get_text(" ", strip=True).casefold() == "lane" and value:
                lanes = [part.strip().casefold() for part in value.get_text(" ", strip=True).split("/")]
                roles = list(dict.fromkeys(LANE_TO_APP_ROLE[lane] for lane in lanes if lane in LANE_TO_APP_ROLE))
                return roles
        return []

    roles_by_hero = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_hero = {executor.submit(read_roles, hero_id): hero_id for hero_id in hero_ids}
        for future in concurrent.futures.as_completed(future_to_hero):
            hero_id = future_to_hero[future]
            try:
                roles_by_hero[hero_id] = future.result()
            except Exception as exc:
                raise RuntimeError(f"Could not read RoVGuide lane profile for {hero_id}.") from exc

    if len(roles_by_hero) != len(hero_ids) or any(not roles for roles in roles_by_hero.values()):
        missing = sorted(hero_id for hero_id in hero_ids if not roles_by_hero.get(hero_id))
        raise RuntimeError(f"RoVGuide lane data incomplete: {', '.join(missing)}")

    return ranked, roles_by_hero, snapshot

def resolve_nextjs_pointer(ptr, data_root):
    """Resolves Next.js stream pointers like $6:props:data:tiers:S+:5:counters:0:hero"""
    if not isinstance(ptr, str) or "tiers" not in ptr:
        return None
        
    parts = ptr.split(":")
    try:
        start_idx = parts.index("tiers")
        path_parts = parts[start_idx + 1:] # Skip 'tiers' itself, since data_root is the 'tiers' dict
    except ValueError:
        return None
        
    current = data_root
    for part in path_parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                idx = int(part)
                current = current[idx]
            except (ValueError, IndexError):
                return None
        else:
            return None
            
    if isinstance(current, str) and current != ptr and "tiers" in current:
        return resolve_nextjs_pointer(current, data_root)
    return current

def estimate_attributes(role):
    """Generates lane-accurate default ratings."""
    if role == "Top":
        return { "damage": 3, "tankiness": 4, "mobility": 2, "teamfight": 4, "split_push": 4 }
    elif role == "Jungle":
        return { "damage": 5, "tankiness": 2, "mobility": 5, "teamfight": 3, "split_push": 4 }
    elif role == "Mid":
        return { "damage": 4, "tankiness": 1, "mobility": 3, "teamfight": 5, "split_push": 2 }
    elif role == "AD":
        return { "damage": 5, "tankiness": 1, "mobility": 3, "teamfight": 4, "split_push": 3 }
    elif role == "SP":
        return { "damage": 1, "tankiness": 5, "mobility": 2, "teamfight": 5, "split_push": 1 }
    return { "damage": 3, "tankiness": 3, "mobility": 3, "teamfight": 3, "split_push": 3 }

def crawl_hero_counters_from_aovbuilds(slug, meta_id_to_local_id):
    """Crawls and parses the detailed counter page from aov-builds.com/khac-che/<slug>/"""
    url = f"https://aov-builds.com/khac-che/{slug}/"
    try:
        response = requests.get(url, headers=HEADERS, timeout=8)
        if response.status_code != 200:
            return slug, None
            
        soup = BeautifulSoup(response.content, "html.parser")
        accordions = soup.find_all("div", class_="counter-box")
        
        parsed_counters = []
        seen_counter_ids = set()
        
        for box in accordions:
            content_div = box.find("div", class_="accordion__content")
            if not content_div:
                continue
                
            items = content_div.find_all("div", class_="nav__tab__content__item")
            for item in items:
                text_lines = [l.strip() for l in item.text.split("\n") if l.strip()]
                if not text_lines:
                    continue
                    
                hero_name = text_lines[0]
                reason = " ".join(text_lines[1:]) if len(text_lines) > 1 else ""
                reason = re.sub(r'\s+', ' ', reason).strip()
                
                # Resolve local ID
                c_meta_id = clean_id(hero_name)
                c_meta_id = UNMATCHED_REPLACEMENTS.get(c_meta_id, c_meta_id)
                
                c_local_id = meta_id_to_local_id.get(c_meta_id)
                            
                if c_local_id and c_local_id not in seen_counter_ids:
                    seen_counter_ids.add(c_local_id)
                    parsed_counters.append({
                        "id": c_local_id,
                        "reason": reason
                    })
        return slug, parsed_counters
    except Exception:
        return slug, None

def main():
    previous = json.loads((ROOT / "data" / "crawled_heroes.json").read_text(encoding="utf-8"))
    previous_by_id = {hero["id"]: hero for hero in previous}
    print("[+] Bắt đầu cập nhật dữ liệu Liên Quân / AoV từ AOV Builds, RoVGuide và RovMeta...")
    
    # ====================================================
    # --- PHASE 1: CRAWL AOV-BUILDS.COM FOR HERO LIST ---
    # ====================================================
    aov_heroes = []
    print(f"[+] 1. Gửi yêu cầu tải danh sách tướng từ: {AOV_BUILDS_URL}...")
    try:
        response = requests.get(AOV_BUILDS_URL, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            links = soup.find_all("a")
            seen = set()
            
            for l in links:
                href = l.get("href", "")
                if href and href.startswith("https://aov-builds.com/tuong/") and len(href.split("/")) >= 5:
                    slug = href.split("/")[-2]
                    if slug == "tuong":
                        continue
                    img = l.find("img")
                    img_src = img.get("src", "") if img else ""
                    name = l.text.strip()
                    if slug not in seen and name:
                        seen.add(slug)
                        aov_heroes.append({
                            "name": name,
                            "slug": slug,
                            "avatar": img_src
                        })
            print(f"[+] Trích xuất thành công {len(aov_heroes)} tướng từ aov-builds.com.")
        else:
            print(f"[-] AOV-Builds trả về mã lỗi: {response.status_code}.")
            raise RuntimeError("Không tải được danh sách tướng; giữ nguyên dữ liệu.")
    except Exception as e:
        print(f"[-] Lỗi kết nối AOV-Builds: {e}")
        raise RuntimeError("Không tải được danh sách tướng; giữ nguyên dữ liệu.") from e

    if len(aov_heroes) < max(20, len(previous) * 0.9):
        raise RuntimeError("Danh sách tướng rỗng hoặc giảm bất thường; giữ nguyên dữ liệu.")

    # ====================================================
    # --- PHASE 2: CRAWL ROVMETA.COM FOR META STATS ---
    # ====================================================
    meta_heroes = {}
    tiers_data = {}
    print(f"[+] 2. Gửi yêu cầu tải trang chủ RovMeta: {ROVMETA_URL}...")
    try:
        meta_response = requests.get(ROVMETA_URL, headers=HEADERS, timeout=15)
        if meta_response.status_code == 200:
            html = meta_response.text
            chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*("(?:\\.|[^"\\])*")\]\)', html)
            
            # Reconstruct stream
            full_stream = ""
            for c in chunks:
                decoded_chunk = json.loads(c)
                full_stream += decoded_chunk
                
            # Locate tiers JSON
            match = re.search(r'"tiers":\s*(\{[\s\S]*?\})', full_stream)
            if match:
                tiers_data, _ = json.JSONDecoder().raw_decode(full_stream[match.start(1):])
                
                # Flatten tiers
                for tier, heroes_list in tiers_data.items():
                    if not isinstance(heroes_list, list):
                        continue
                    for item in heroes_list:
                        if not isinstance(item, dict):
                            continue
                        
                        hero_info = item.get("hero", {})
                        if isinstance(hero_info, str):
                            resolved = resolve_nextjs_pointer(hero_info, tiers_data)
                            if resolved:
                                hero_info = resolved
                                
                        if not isinstance(hero_info, dict):
                            continue
                            
                        name_en = hero_info.get("name_en", "")
                        role = hero_info.get("role", "")
                        stats = item.get("stats", {})
                        if not isinstance(stats, dict):
                            stats = {}
                            
                        if name_en:
                            cid = clean_id(name_en)
                            meta_heroes[cid] = {
                                "name_en": name_en,
                                "role": role,
                                "tier": tier,
                                "win_rate": stats.get("win_rate"),
                                "pick_rate": stats.get("pick_rate"),
                                "ban_rate": stats.get("ban_rate"),
                                "stats_source": stats.get("source", "unspecified"),
                                "raw_item": item
                            }
                print(f"[+] Trích xuất thành công {len(meta_heroes)} tướng từ RovMeta.")
            else:
                print("[-] Không tìm thấy khối dữ liệu 'tiers' trong stream của RovMeta.")
        else:
            print(f"[-] RovMeta trả về mã lỗi: {meta_response.status_code}.")
    except Exception as e:
        print(f"[-] Lỗi kết nối tới RovMeta: {e}")

    if len(meta_heroes) < max(20, len(previous) * 0.8):
        raise RuntimeError("Dữ liệu meta thiếu hoặc không đọc được; giữ nguyên dữ liệu.")

    # ====================================================
    # --- PHASE 3: CONCURRENT COUNTERS CRAWL (AOVBUILDS) -
    # ====================================================
    # Build mapping from English clean IDs to local clean IDs
    meta_id_to_local_id = {}
    for h in aov_heroes:
        slug = h["slug"]
        local_id = clean_id(slug)
        mapped_meta_id = clean_id(AOV_TO_ROVMETA.get(slug, slug))
        if mapped_meta_id not in meta_heroes and clean_id(slug) in meta_heroes:
            mapped_meta_id = clean_id(slug)
        
        meta_match_id = None
        if mapped_meta_id in meta_heroes:
            meta_match_id = mapped_meta_id
        meta_id_to_local_id[local_id] = local_id
        if meta_match_id:
            meta_id_to_local_id[meta_match_id] = local_id

    print(f"[+] 3. Khởi chạy bộ cào khắc chế đồng thời từ AOV-Builds (10 luồng)...")
    aov_counters_db = {}
    start_time = time.time()
    
    # Spawn 10 threads to fetch all counter pages concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_slug = {
            executor.submit(crawl_hero_counters_from_aovbuilds, h["slug"], meta_id_to_local_id): h["slug"] 
            for h in aov_heroes
        }
        for future in concurrent.futures.as_completed(future_to_slug):
            slug = future_to_slug[future]
            try:
                slug, counters = future.result()
                if counters:
                    aov_counters_db[slug] = counters
            except Exception:
                pass
                
    end_time = time.time()
    print(f"[🎉] Hoàn tất thu thập khắc chế từ AOV-Builds trong {end_time - start_time:.2f} giây. Tìm thấy {len(aov_counters_db)}/{len(aov_heroes)} trang chi tiết.")

    # ====================================================
    # --- PHASE 4: REFRESH RANKED DATA AND LANE PROFILES ---
    # ====================================================
    print(f"[+] 4. Cập nhật lane đa vị trí và meta ranked từ RoVGuide...")
    local_ids = [clean_id(hero["slug"]) for hero in aov_heroes]
    ranked_by_slug, roles_by_hero, ranked_snapshot = fetch_rovguide_reference_data(local_ids)
    ranked_by_hero = {}
    for hero_id in local_ids:
        guide_slug = ROVGUIDE_SLUG_OVERRIDES.get(hero_id, hero_id)
        if guide_slug not in ranked_by_slug:
            raise RuntimeError(f"RoVGuide ranked row missing for {hero_id} ({guide_slug}).")
        ranked_by_hero[hero_id] = ranked_by_slug[guide_slug]
    print(f"[+] Đã xác minh ranked cho {len(ranked_by_hero)} tướng; snapshot {ranked_snapshot}; lane hồ sơ {len(roles_by_hero)}/{len(local_ids)}.")

    # ====================================================
    # --- PHASE 4: MERGE DATA & UPDATE TARGET FILES ---
    # ====================================================
    print("[+] 4. Trộn và đồng bộ hóa cơ sở dữ liệu...")
    crawled_database = []
    rovmeta_matches = 0
    ad_count = 0
    total_counters_linked = 0
    unmatched = []
    provenance = {}
    
    for h in aov_heroes:
        slug = h["slug"]
        name_vn = h["name"]
        avatar = h["avatar"]
        
        # Determine unique alphanumeric ID for local storage
        hero_id = clean_id(slug)
        
        # Translate local slug to RovMeta English ID
        mapped_meta_id = clean_id(AOV_TO_ROVMETA.get(slug, slug))
        if mapped_meta_id not in meta_heroes and clean_id(slug) in meta_heroes:
            mapped_meta_id = clean_id(slug)
        meta_match = meta_heroes.get(mapped_meta_id)
        old = previous_by_id.get(hero_id, {})
        guide_data = ranked_by_hero[hero_id]
        roles = roles_by_hero[hero_id]
        official_reference = OFFICIAL_VN_ROLE_CROSSCHECKS.get(hero_id)
        role_source = f"{ROVGUIDE_HEROES_URL}/{ROVGUIDE_SLUG_OVERRIDES.get(hero_id, hero_id)}"
        role_source_region = "TH"
        role_cross_check = official_reference
        provenance[hero_id] = {
            "rovmeta_reference": "matched" if meta_match else "not_matched",
            "stats_source": "rovguide_ranked_thailand",
            "stats_snapshot": ranked_snapshot,
            "roles_source": role_source,
            "roles_source_region": role_source_region,
            "roles_cross_check": role_cross_check,
            "counters": "aov-builds" if aov_counters_db.get(slug) else "rovmeta" if meta_match else "previous",
            "fallback_rate_fields": [],
        }
        if not meta_match:
            unmatched.append(hero_id)
        win_rate = guide_data["win_rate"]
        pick_rate = guide_data["pick_rate"]
        ban_rate = guide_data["ban_rate"]
        tier = guide_data["tier"]
        if meta_match:
            rovmeta_matches += 1

        # Mapped counters container
        merged_counters = []
        
        # Priority 1: AOV-Builds detailed counters (if exists)
        if slug in aov_counters_db and aov_counters_db[slug]:
            merged_counters = aov_counters_db[slug]
        else:
            # Priority 2: Fallback to RovMeta generic counters
            raw_item = meta_match.get("raw_item", {}) if meta_match else {}
            raw_counters = raw_item.get("counters", []) if isinstance(raw_item, dict) else []
            for c in raw_counters:
                if isinstance(c, str):
                    resolved_c = resolve_nextjs_pointer(c, tiers_data)
                    if resolved_c:
                        c = resolved_c
                if isinstance(c, dict):
                    chero = c.get("hero", {})
                    if isinstance(chero, str):
                        resolved_chero = resolve_nextjs_pointer(chero, tiers_data)
                        if resolved_chero:
                            chero = resolved_chero
                    if isinstance(chero, dict):
                        cname = chero.get("name_en", "")
                        if cname:
                            c_meta_id = clean_id(cname)
                            c_meta_id = UNMATCHED_REPLACEMENTS.get(c_meta_id, c_meta_id)
                            c_local_id = meta_id_to_local_id.get(c_meta_id)
                            if c_local_id:
                                # Generate a generic explanation
                                c_vn_name = next((h_vn["name"] for h_vn in aov_heroes if clean_id(h_vn["slug"]) == c_local_id), cname)
                                merged_counters.append({
                                    "id": c_local_id,
                                    "reason": f"RovMeta liệt kê {c_vn_name} trong nhóm khắc chế {name_vn}; nguồn không cung cấp giải thích chi tiết."
                                })

        if not merged_counters and old.get("counters"):
            merged_counters = old["counters"]
            provenance[hero_id]["counters"] = "previous"
        if not merged_counters:
            provenance[hero_id]["counters"] = "none"
        merged_counters = [c for c in merged_counters if c["id"] != hero_id and c["id"] in meta_id_to_local_id]
        merged_counters = list({c["id"]: c for c in merged_counters}.values())
        total_counters_linked += len(merged_counters)
            
        main_role = roles[0]
            
        if main_role == "AD":
            ad_count += 1
            
        attributes = estimate_attributes(main_role)
        
        crawled_database.append({
            "id": hero_id,
            "name": name_vn,
            "main_role": main_role,
            "roles": roles,
            "tier": tier,
            "avatar": avatar,
            "win_rate": win_rate,
            "pick_rate": pick_rate,
            "ban_rate": ban_rate,
            "meta_source": "RoVGuide ranked Thailand",
            "meta_snapshot": ranked_snapshot,
            "roles_source": role_source,
            "roles_region": role_source_region,
            "roles_cross_check": role_cross_check,
            "attributes": attributes,
            "counters": merged_counters,
            "tags": list(dict.fromkeys([role.lower() for role in roles] + ["crawled"]))
        })
        
    print(f"[+] Trộn xong! Tổng cộng: {len(crawled_database)} tướng. Đối chiếu được RovMeta: {rovmeta_matches}/{len(aov_heroes)}.")
    print(f"[+] Tổng số mối liên kết khắc chế chi tiết đã nhập: {total_counters_linked}")
    print(f"[+] Số lượng tướng AD (Xạ Thủ): {ad_count}")
    
    validate_database(crawled_database)
        
    # Update app.js HERO_DATABASE
    app_js_path = ROOT / "public" / "assets" / "js" / "app.js"
    if os.path.exists(app_js_path):
        print("[+] Tìm thấy file app.js. Đang tự động cập nhật cơ sở dữ liệu...")
        try:
            with open(app_js_path, "r", encoding="utf-8") as f:
                js_content = f.read()
            
            pattern = r"const HERO_DATABASE = \[\s*[\s\S]*?\];"
            replacement = f"const HERO_DATABASE = {json.dumps(crawled_database, ensure_ascii=False, indent=4)};"
            
            new_js_content, count = re.subn(pattern, lambda _: replacement, js_content)
            if count == 1:
                output_file = ROOT / "data" / "crawled_heroes.json"
                output_file.write_text(json.dumps(crawled_database, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
                with open(app_js_path, "w", encoding="utf-8") as f:
                    f.write(new_js_content)
                print(f"[🎉] Đã tự động cập nhật {len(crawled_database)} tướng vào file app.js!")
            else:
                raise RuntimeError("Cần đúng một khối HERO_DATABASE trong app.js.")
        except Exception as e:
            raise RuntimeError("Không thể đồng bộ app.js.") from e
    else:
        raise RuntimeError("Không tìm thấy app.js.")

    patch_match = re.search(r'"patch_number":"([^"]+)"', full_stream)
    report = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sources": {"roster": AOV_BUILDS_URL, "roles": ROVGUIDE_HEROES_URL, "official_vietnam_cross_check": "https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-le-hoi-5v5-08-04-2026/", "meta": ROVGUIDE_META_URL, "counters": "https://aov-builds.com/khac-che/", "counter_fallback": ROVMETA_URL},
        "rovmeta_reference_patch": patch_match.group(1) if patch_match else None,
        "ranked_snapshot": ranked_snapshot,
        "ranked_region": "Thailand",
        "hero_count": len(crawled_database),
        "rovmeta_reference_matches": rovmeta_matches,
        "detailed_counter_pages": len(aov_counters_db),
        "counter_links": total_counters_linked,
        "unmatched_rovmeta_reference_ids": unmatched,
        "removed_ids": sorted(set(previous_by_id) - {h["id"] for h in crawled_database}),
        "attributes_source": "estimated_by_lane_not_measured",
        "heroes": provenance,
    }
    (ROOT / "data" / "data_update_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            
    print("\n" + "="*60)
    print(f"[🎉] HỆ THỐNG CẬP NHẬT CƠ SỞ DỮ LIỆU ĐỒNG BỘ ĐÃ HOÀN TẤT THÀNH CÔNG!")
    print(f"[+] Tổng số tướng đã lưu trữ: {len(crawled_database)}")
    print(f"[+] File lưu: {os.path.abspath(output_file)}")
    print("="*60)

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
