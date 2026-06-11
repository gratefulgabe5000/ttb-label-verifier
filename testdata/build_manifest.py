"""Build testdata/manifest.json — WBS 2.1.

`testdata/` is a flat directory of real-world label photographs (front/back/
other views of bottles and cans). The original good/bad/category subfolders
were removed (2026-06-11) because they no longer encode a meaningful
pass/fail outcome -- every image here is just a raw label image awaiting
assessment. There are no application forms (F 5100.31) for any of these
products yet; synthetic forms are generated and paired with these label
groups in WBS 2.2-2.7, which is where expected outcomes (APPROVE / DENY /
RECOMMEND_EXEMPTION_REVIEW) get assigned.

This script groups the flat file list into per-product label sets and writes
`manifest.json`. Re-run it whenever files are added to/removed from
`testdata/` -- it fails loudly if ROWS and the directory listing disagree.

product_type values match web/src/lib/types.ts ProductType:
    "distilled_spirits" | "wine" | "malt_beverages"
label_type values match web/src/lib/types.ts LabelType:
    "brand" | "back" | "neck" | "other"
("front"/"front2"/"(front)" -> "brand"; "back"/"(back)" -> "back")
"""

import json
from collections import OrderedDict
from pathlib import Path

TESTDATA_DIR = Path(__file__).parent
MANIFEST_PATH = TESTDATA_DIR / "manifest.json"

# (filename, product_key, brand_name, product_type, label_type, note)
ROWS = [
    ("Alpine Lafayette whiskey.jpg", "alpine_lafayette", "Alpine Lafayette", "distilled_spirits", "brand", None),

    ("Angels Envy burbon back.jpg", "angels_envy", "Angels Envy", "distilled_spirits", "back", None),
    ("Angels Envy burbon front.jpg", "angels_envy", "Angels Envy", "distilled_spirits", "brand", None),

    ("Barenjager back.jpg", "barenjager", "Barenjager", "distilled_spirits", "back", None),
    ("Barenjager front.jpg", "barenjager", "Barenjager", "distilled_spirits", "brand", None),

    ("Barenjager burbon back.jpg", "barenjager_burbon", "Barenjager Burbon", "distilled_spirits", "back",
     "Filename includes 'burbon' -- treated as a distinct product from 'Barenjager' "
     "(honey liqueur). Kept separate pending visual confirmation during 2.3-2.5 pairing."),
    ("Barenjager burbon front.jpg", "barenjager_burbon", "Barenjager Burbon", "distilled_spirits", "brand", None),

    ("Black Maple Hill whiskey back.jpg", "black_maple_hill", "Black Maple Hill", "distilled_spirits", "back", None),
    ("Black Maple Hill whiskey front.jpg", "black_maple_hill", "Black Maple Hill", "distilled_spirits", "brand", None),
    ("Black Maple Hill whiskey other.jpg", "black_maple_hill", "Black Maple Hill", "distilled_spirits", "other", None),

    ("Boston Harbor maple cream back.jpg", "boston_harbor", "Boston Harbor", "distilled_spirits", "back", None),
    ("Boston Harbor maple cream front.jpg", "boston_harbor", "Boston Harbor", "distilled_spirits", "brand", None),

    ("Casamigos tequila back.jpg", "casamigos", "Casamigos", "distilled_spirits", "back", None),
    ("Casamigos tequila front.jpg", "casamigos", "Casamigos", "distilled_spirits", "brand", None),

    ("Cascade Val wine.jpg", "cascade_val", "Cascade Val", "wine", "brand", None),

    ("Cerveza Barrilito.jpg", "barrilito", "Barrilito", "malt_beverages", "brand", None),

    ("Collabor&tion whiskey.jpg", "collaboration", "Collabor&tion", "distilled_spirits", "brand", None),

    ("Cotton Hollow burbon front.jpg", "cotton_hollow", "Cotton Hollow", "distilled_spirits", "brand", None),
    ("Cotton Hollow burbon other.jpg", "cotton_hollow", "Cotton Hollow", "distilled_spirits", "other", None),

    ("Den of Thieves chocolate whiskey back.jpg", "den_of_thieves", "Den of Thieves", "distilled_spirits", "back", None),
    ("Den of Thieves chocolate whiskey front.jpg", "den_of_thieves", "Den of Thieves", "distilled_spirits", "brand", None),

    ("Dutch Courage gin back.jpg", "dutch_courage", "Dutch Courage", "distilled_spirits", "back", None),
    ("Dutch Courage gin front.jpg", "dutch_courage", "Dutch Courage", "distilled_spirits", "brand", None),

    ("Fete Rose wine back.jpg", "fete_rose", "Fete Rose", "wine", "back", None),
    ("Fete Rose wine.jpg", "fete_rose", "Fete Rose", "wine", "brand", None),

    ("Forte Masso beer back.jpg", "forte_masso", "Forte Masso", "malt_beverages", "back",
     "Filename says 'beer' but the label artwork reads 'Barbera D'Alba -- Denominazione di "
     "Origine Controllata' (an Italian wine appellation/class designation). Likely an "
     "intentional product/class-type mismatch fixture (FR-100 product/class-type, FR-107 "
     "wine appellation) -- confirm intended product_type before pairing with a synthetic "
     "form in WBS 2.4."),
    ("Forte Masso beer front.jpg", "forte_masso", "Forte Masso", "malt_beverages", "brand", None),

    ("Fuel moonshine.jpg", "fuel", "Fuel", "distilled_spirits", "brand", None),

    ("Ginger Sins whiskey back.jpg", "ginger_sins", "Ginger Sins", "distilled_spirits", "back", None),
    ("Ginger Sins whiskey front.jpg", "ginger_sins", "Ginger Sins", "distilled_spirits", "brand", None),
    ("Ginger Sins whiskey other.jpg", "ginger_sins", "Ginger Sins", "distilled_spirits", "other", None),

    ("Gordian Knot rum back.jpg", "gordian_knot", "Gordian Knot", "distilled_spirits", "back", None),
    ("Gordian Knot rum front.jpg", "gordian_knot", "Gordian Knot", "distilled_spirits", "brand", None),

    ("Hanami gin back.jpg", "hanami", "Hanami", "distilled_spirits", "back", None),
    ("Hanami gin front.jpg", "hanami", "Hanami", "distilled_spirits", "brand", None),

    ("Howling Moon moonshine back.jpg", "howling_moon_moonshine", "Howling Moon (Moonshine)", "distilled_spirits", "back", None),
    ("Howling Moon moonshine front.jpg", "howling_moon_moonshine", "Howling Moon (Moonshine)", "distilled_spirits", "brand", None),

    ("Howling Moon whiskey back.jpg", "howling_moon_whiskey", "Howling Moon (Whiskey)", "distilled_spirits", "back", None),
    ("Howling Moon whiskey front.jpg", "howling_moon_whiskey", "Howling Moon (Whiskey)", "distilled_spirits", "brand", None),

    ("Jacques Cardin cognac back.jpg", "jacques_cardin", "Jacques Cardin", "distilled_spirits", "back", None),
    ("Jacques Cardin cognac front.jpg", "jacques_cardin", "Jacques Cardin", "distilled_spirits", "brand", None),

    ("Lenz Moser wine back.jpg", "lenz_moser", "Lenz Moser", "wine", "back", None),
    ("Lenz Moser wine front.jpg", "lenz_moser", "Lenz Moser", "wine", "brand", None),

    ("Market Alley gin (back).jpg", "market_alley", "Market Alley", "distilled_spirits", "back", None),
    ("Market Alley gin (front).jpg", "market_alley", "Market Alley", "distilled_spirits", "brand", None),

    ("McKenzie Brew House vodka.jpg", "mckenzie_brew_house", "McKenzie Brew House", "distilled_spirits", "brand", None),

    ("Misunderstood ginger whiskey front.jpg", "misunderstood", "Misunderstood", "distilled_spirits", "brand", None),
    ("Misunderstood ginger whiskey other.jpg", "misunderstood", "Misunderstood", "distilled_spirits", "other", None),

    ("Mokka whiskey back.jpg", "mokka", "Mokka", "distilled_spirits", "back", None),
    ("Mokka whiskey front.jpg", "mokka", "Mokka", "distilled_spirits", "brand", None),
    ("Mokka whiskey other.jpg", "mokka", "Mokka", "distilled_spirits", "other", None),

    ("Monkey 47 gin back.jpg", "monkey_47", "Monkey 47", "distilled_spirits", "back", None),
    ("Monkey 47 gin front.jpg", "monkey_47", "Monkey 47", "distilled_spirits", "brand", None),

    ("Nicks & Bruce aged rum back.jpg", "nicks_and_bruce", "Nicks & Bruce", "distilled_spirits", "back", None),
    ("Nicks & Bruce aged rum front.jpg", "nicks_and_bruce", "Nicks & Bruce", "distilled_spirits", "brand", None),

    ("Original Spice whiskey back.jpg", "original_spice", "Original Spice", "distilled_spirits", "back", None),
    ("Original Spice whiskey front.jpg", "original_spice", "Original Spice", "distilled_spirits", "brand", None),
    ("Original Spice whiskey other.jpg", "original_spice", "Original Spice", "distilled_spirits", "other", None),

    ("Presidential Dram whiskey back.jpg", "presidential_dram", "Presidential Dram", "distilled_spirits", "back", None),
    ("Presidential Dram whiskey front.jpg", "presidential_dram", "Presidential Dram", "distilled_spirits", "brand", None),

    ("Resilient burbon front.jpg", "resilient", "Resilient", "distilled_spirits", "brand", None),
    ("Resilient burbon other.jpg", "resilient", "Resilient", "distilled_spirits", "other", None),

    ("Rocky Mount whiskey back.jpg", "rocky_mount", "Rocky Mount", "distilled_spirits", "back", None),
    ("Rocky Mount whiskey front.jpg", "rocky_mount", "Rocky Mount", "distilled_spirits", "brand", None),

    ("Rosso Veneto wine back.jpg", "rosso_veneto", "Rosso Veneto", "wine", "back", None),
    ("Rosso Veneto wine front.jpg", "rosso_veneto", "Rosso Veneto", "wine", "brand", None),

    ("Sailor Jerry rum.jpg", "sailor_jerry", "Sailor Jerry", "distilled_spirits", "brand", None),

    ("Salted Caramel whiskey back.jpg", "salted_caramel", "Salted Caramel", "distilled_spirits", "back", None),
    ("Salted Caramel whiskey front.jpg", "salted_caramel", "Salted Caramel", "distilled_spirits", "brand", None),
    ("Salted Caramel whiskey other.jpg", "salted_caramel", "Salted Caramel", "distilled_spirits", "other", None),

    ("Seven Fathoms rum back.jpg", "seven_fathoms", "Seven Fathoms", "distilled_spirits", "back", None),
    ("Seven Fathoms rum front.jpg", "seven_fathoms", "Seven Fathoms", "distilled_spirits", "brand", None),

    ("Sortilege liqueur back.jpg", "sortilege_1", "Sortilege", "distilled_spirits", "back", None),
    ("Sortilege liqueur front.jpg", "sortilege_1", "Sortilege", "distilled_spirits", "brand", None),
    ("Sortilege liqueur other.jpg", "sortilege_1", "Sortilege", "distilled_spirits", "other", None),

    ("Sortilege liqueur2 back.jpg", "sortilege_2", "Sortilege (variant 2)", "distilled_spirits", "back",
     "Second Sortilege label set ('liqueur2') -- kept as a separate product from "
     "'sortilege_1' since it appears to be a different bottle/edition."),
    ("Sortilege liqueur2 front.jpg", "sortilege_2", "Sortilege (variant 2)", "distilled_spirits", "brand", None),

    ("Stoll & Wolfe whiskey back.jpg", "stoll_and_wolfe", "Stoll & Wolfe", "distilled_spirits", "back", None),
    ("Stoll & Wolfe whiskey front.jpg", "stoll_and_wolfe", "Stoll & Wolfe", "distilled_spirits", "brand", None),

    ("Twelv 31 liqeur front.jpg", "twelv_31", "Twelv 31", "distilled_spirits", "brand", None),

    ("Uncle Nearest whiskey back.jpg", "uncle_nearest", "Uncle Nearest", "distilled_spirits", "back", None),
    ("Uncle Nearest whiskey front.jpg", "uncle_nearest", "Uncle Nearest", "distilled_spirits", "brand", None),

    ("Warm whiskey.jpg", "warm", "Warm", "distilled_spirits", "brand", None),

    ("White Label whiskey back.jpg", "white_label", "White Label", "distilled_spirits", "back", None),
    ("White Label whiskey front.jpg", "white_label", "White Label", "distilled_spirits", "brand", None),

    ("Woodford Reserve burbon back.jpg", "woodford_reserve", "Woodford Reserve", "distilled_spirits", "back", None),
    ("Woodford Reserve burbon front.jpg", "woodford_reserve", "Woodford Reserve", "distilled_spirits", "brand", None),
    ("Woodford Reserve burbon front2.jpg", "woodford_reserve", "Woodford Reserve", "distilled_spirits", "brand",
     "Second brand-label photo (alternate angle/printing) -- both 'front' and 'front2' "
     "map to label_type 'brand'."),
]


def build() -> dict:
    on_disk = {p.name for p in TESTDATA_DIR.glob("*.jpg")}
    listed = {row[0] for row in ROWS}

    missing = on_disk - listed
    extra = listed - on_disk
    if missing:
        raise SystemExit(f"ROWS is missing files present in testdata/: {sorted(missing)}")
    if extra:
        raise SystemExit(f"ROWS lists files no longer present in testdata/: {sorted(extra)}")

    products: "OrderedDict[str, dict]" = OrderedDict()
    for filename, product_key, brand_name, product_type, label_type, note in ROWS:
        product = products.setdefault(
            product_key,
            {
                "product_key": product_key,
                "brand_name": brand_name,
                "product_type": product_type,
                "images": [],
                "notes": [],
            },
        )
        if product["brand_name"] != brand_name or product["product_type"] != product_type:
            raise SystemExit(f"Inconsistent brand_name/product_type for product_key={product_key!r}")
        product["images"].append({"filename": filename, "label_type": label_type})
        if note and note not in product["notes"]:
            product["notes"].append(note)

    for product in products.values():
        if not product["notes"]:
            del product["notes"]

    by_product_type: "OrderedDict[str, int]" = OrderedDict(
        [("distilled_spirits", 0), ("wine", 0), ("malt_beverages", 0)]
    )
    for product in products.values():
        by_product_type[product["product_type"]] += len(product["images"])

    return {
        "wbs_ref": "2.1",
        "generated_at": "2026-06-11",
        "source_note": (
            "Flat inventory of testdata/ label images. The original good/bad category "
            "subfolders (good spirits, good wine+beer, bad spirits label/photo/warning, "
            "bad wine+beer) were removed by Gabe on 2026-06-11 -- they no longer encode an "
            "expected pass/fail outcome. Every file below is a raw label image awaiting "
            "assessment, grouped by product (front/brand, back, other views of the same "
            "bottle/can). No application forms (F 5100.31) exist for any of these products "
            "yet; synthetic forms must be generated (WBS 2.2) and paired with these label "
            "groups (WBS 2.3-2.7) to assign expected outcomes (APPROVE / DENY / "
            "RECOMMEND_EXEMPTION_REVIEW) and comparison-rule coverage."
        ),
        "totals": {
            "images": len(ROWS),
            "products": len(products),
            "by_product_type": dict(by_product_type),
        },
        "products": list(products.values()),
    }


if __name__ == "__main__":
    manifest = build()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {MANIFEST_PATH.relative_to(TESTDATA_DIR.parent)}: "
        f"{manifest['totals']['products']} products, "
        f"{manifest['totals']['images']} images, "
        f"by type {manifest['totals']['by_product_type']}"
    )
