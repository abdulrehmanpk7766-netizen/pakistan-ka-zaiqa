"""
Pakistan Ka Zaiqa - Streamlit app (Pakistan City Food Guide)
Mohsin Mustafa (BSEDS24025), Abdul Rehman (BSEDS24052)

Three screens, one query behind each (same queries as Part E of the report):
  1. Search    : pick city + meal type + spice level -> up to 3 local dishes
  2. Dish      : ingredients and facts of the chosen dish
  3. Outlets   : outlets in that city that serve the dish (table + map)

Optional photos: create a folder called "images" next to this file and put
  images/bg.jpg    -> page wallpaper (darkened automatically so text stays readable)
  images/hero.jpg  -> picture shown under the title banner
Both are optional. Without them the app uses a built-in truck-art pattern.

Run:  streamlit run app.py
"""
import base64
import os
from html import escape

import pandas as pd
import psycopg2
from dotenv import load_dotenv
load_dotenv(".env.local")
import streamlit as st

st.set_page_config(page_title="Pakistan Ka Zaiqa", page_icon="🍛", layout="centered")

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- pictures
def image_data_uri(filename):
    """Return a data URI for images/<filename>, or None if the file does not exist."""
    path = os.path.join(HERE, "images", filename)
    if not os.path.isfile(path):
        return None
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    with open(path, "rb") as f:
        return f"data:image/{mime};base64," + base64.b64encode(f.read()).decode()


# Built-in truck-art style pattern (small flowers and diamonds), drawn as SVG.
PATTERN = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='90' height='90'>"
    "<g opacity='0.40'>"
    "<circle cx='45' cy='45' r='15' fill='none' stroke='%23FFB300' stroke-width='3'/>"
    "<circle cx='45' cy='45' r='6' fill='%23D6286E'/>"
    "<circle cx='45' cy='24' r='4' fill='%23FFB300'/><circle cx='45' cy='66' r='4' fill='%23FFB300'/>"
    "<circle cx='24' cy='45' r='4' fill='%23FFB300'/><circle cx='66' cy='45' r='4' fill='%23FFB300'/>"
    "<path d='M0 0 L8 4 L0 8 Z M90 0 L82 4 L90 8 Z M0 90 L8 86 L0 82 Z M90 90 L82 86 L90 82 Z' fill='%23FF6B00'/>"
    "</g></svg>"
)

BG_PHOTO = image_data_uri("bg.jpg")
HERO_PHOTO = image_data_uri("hero.jpg")

# Dark wallpaper: deep green with the pattern, or the user's photo under a dark wash.
if BG_PHOTO:
    PAGE_BACKGROUND = (
        f"linear-gradient(rgba(8,24,18,0.78), rgba(8,24,18,0.78)), url('{BG_PHOTO}') center / cover fixed"
    )
else:
    PAGE_BACKGROUND = f"url(\"{PATTERN}\"), #0A2E24"

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&family=Rakkas&display=swap');

html, body, [class*="css"], .stApp { font-family: 'Poppins', sans-serif; }

.stApp { background: __BACKGROUND__; }

/* hide default streamlit chrome */
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }

/* content sits on a light panel so every text stays easy to read on the dark wallpaper */
div.block-container, div[data-testid="stMainBlockContainer"] {
    background: rgba(255, 248, 231, 0.97);
    color: #2B1B0E;
    border-radius: 26px;
    border: 4px solid #FFB300;
    box-shadow: 0 0 0 4px #D6286E, 0 16px 40px rgba(0, 0, 0, 0.45);
    padding: 1.6rem 1.6rem 1.4rem 1.6rem;
    margin-top: 1.2rem;
    margin-bottom: 1.2rem;
}

/* truck-art banner */
.hero {
    background: linear-gradient(135deg, #0B6E4F 0%, #0E8A63 100%);
    border-radius: 22px;
    padding: 26px 22px 22px 22px;
    text-align: center;
    color: #FFF8E7;
    border: 4px solid #FFB300;
    box-shadow: 0 0 0 4px #D6286E, 0 10px 24px rgba(0, 0, 0, 0.18);
    margin-bottom: 8px;
}
.hero-title { font-family: 'Rakkas', cursive; font-size: 2.5rem; line-height: 1.15; color: #FFD54A; text-shadow: 2px 2px 0 #D6286E; }
.hero-sub { font-size: 1rem; margin-top: 6px; opacity: 0.95; }
.hero-photo { width: 100%; max-height: 230px; object-fit: cover; border-radius: 16px; border: 3px solid #FFB300; margin: 12px 0 0 0; }
.bunting { text-align: center; font-size: 1.4rem; letter-spacing: 6px; margin: 4px 0 14px 0; }
.stripe { height: 10px; border-radius: 6px; margin: 18px 0 6px 0;
    background: repeating-linear-gradient(90deg, #0B6E4F 0 24px, #FFB300 24px 48px, #D6286E 48px 72px, #FF6B00 72px 96px); }
.foodstrip { text-align: center; font-size: 1.6rem; letter-spacing: 8px; }

.how { background: #FFF1C2; border-left: 6px solid #D6286E; border-radius: 12px; padding: 10px 14px; margin: 6px 0 10px 0; color: #4a3500; font-size: 0.95rem; }

.section-title { font-family: 'Rakkas', cursive; font-size: 1.7rem; color: #0B6E4F; margin: 10px 0 4px 0; }
.section-title span { color: #D6286E; }

/* cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 2px dashed #FFB300 !important;
    border-radius: 18px !important;
    box-shadow: 4px 4px 0 #D6286E;
}

/* buttons */
.stButton > button {
    border-radius: 999px;
    border: 2px solid #0B6E4F;
    font-weight: 600;
    transition: transform .12s ease;
}
.stButton > button:hover { transform: scale(1.03); border-color: #D6286E; color: #D6286E; }
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #D6286E, #FF6B00);
    color: white;
    border: none;
    font-size: 1.05rem;
    padding: 0.55rem 1rem;
}
.stButton > button[kind="primary"]:hover { color: white; box-shadow: 0 6px 16px rgba(214, 40, 110, 0.35); }

/* badges and chips */
.dish-name { font-family: 'Rakkas', cursive; font-size: 1.5rem; color: #0B6E4F; }
.rank { display: inline-block; background: #FFB300; color: #3a2a00; border-radius: 999px; padding: 2px 10px; font-weight: 700; font-size: 0.8rem; margin-right: 6px; }
.badge { display: inline-block; border-radius: 999px; padding: 3px 12px; margin: 3px 4px 3px 0; font-size: 0.82rem; font-weight: 600; }
.b-veg { background: #DFF5E3; color: #0B6E4F; }
.b-nonveg { background: #FFE0E0; color: #B3261E; }
.b-info { background: #FFF1C2; color: #6b4e00; }
.b-spice { background: #FFE3D1; color: #B34700; }
.chip { display: inline-block; background: #FFF1C2; border: 1.5px solid #FFB300; color: #4a3500; border-radius: 12px; padding: 5px 12px; margin: 4px 5px 4px 0; font-weight: 600; font-size: 0.9rem; }

.stat { background: #0B6E4F; color: #FFF8E7; border-radius: 14px; padding: 8px 14px; display: inline-block; font-weight: 600; margin-bottom: 8px; }
</style>
"""
st.markdown(STYLE.replace("__BACKGROUND__", PAGE_BACKGROUND), unsafe_allow_html=True)


# ---------------------------------------------------------------- database
def cfg(key, default):
    """Read a setting from .streamlit/secrets.toml ([postgres] section) or from an environment variable."""
    try:
        return st.secrets["postgres"][key]
    except Exception:
        return os.environ.get("PG" + key.upper(), default)

def run_query(sql, params=None):
    url = os.environ.get("DATABASE_URL")
    try:
        url = url or st.secrets["DATABASE_URL"]
    except Exception:
        pass
    if url:
        conn = psycopg2.connect(url)  # Neon (sslmode=require url mein hota hai)
    else:
        conn = psycopg2.connect(
            host=cfg("host", "localhost"),
            port=cfg("port", "5432"),
            dbname=cfg("dbname", "food_guid_project"),
            user=cfg("user", "postgres"),
            password=str(cfg("password", "")),
            sslmode=cfg("sslmode", "prefer"),
        )
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [c[0] for c in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=columns)
    finally:
        conn.close()


@st.cache_data(ttl=600)
def q(sql, params=None):
    return run_query(sql, params)


# ---------------------------------------------------------------- queries
CITIES_SQL = "SELECT name FROM city ORDER BY name"
MEALS_SQL = "SELECT DISTINCT meal_type FROM dish WHERE meal_type IS NOT NULL ORDER BY meal_type"

# Screen 1: city + meal type + spice level -> 3 local dishes ("Any" = no filter)
DISHES_SQL = """
SELECT d.dish_id, d.name AS dish, d.category, d.meal_type, d.spice_level, d.is_veg, cd.popularity_rank
FROM   city c
JOIN   city_dish cd ON cd.city_id = c.city_id
JOIN   dish d       ON d.dish_id  = cd.dish_id
WHERE  c.name = %s
  AND  (%s IS NULL OR d.meal_type   = %s)
  AND  (%s IS NULL OR d.spice_level = %s)
ORDER  BY cd.popularity_rank NULLS LAST, d.name
LIMIT  3
"""

# Screen 2: dish facts and ingredients
DISH_SQL = "SELECT name, category, meal_type, spice_level, is_veg FROM dish WHERE dish_id = %s"
INGREDIENTS_SQL = """
SELECT i.name AS ingredient
FROM   dish_ingredient di
JOIN   ingredient i ON i.ingredient_id = di.ingredient_id
WHERE  di.dish_id = %s
ORDER  BY i.name
"""

# Screen 3: outlets in the chosen city that serve the dish
OUTLETS_SQL = """
SELECT o.name AS outlet, o.address, o.latitude, o.longitude
FROM   dish d
JOIN   outlet_dish od ON od.dish_id   = d.dish_id
JOIN   outlet o       ON o.outlet_id  = od.outlet_id
JOIN   city c         ON c.city_id    = o.city_id
WHERE  d.dish_id = %s AND c.name = %s
ORDER  BY o.name
"""

SPICE_LABELS = {
    "Any": "Any spice level 😋",
    "mild": "Mild 😌",
    "medium": "Medium 🌶️",
    "spicy": "Spicy 🔥",
}
SPICE_SHORT = {"mild": "Mild 😌", "medium": "Medium 🌶️", "spicy": "Spicy 🔥"}


# ---------------------------------------------------------------- navigation
def go(page, **values):
    st.session_state.page = page
    for key, value in values.items():
        st.session_state[key] = value


if "page" not in st.session_state:
    st.session_state.page = "search"

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">🍛 Pakistan Ka Zaiqa 🍛</div>
        <div class="hero-sub">The famous food of every city, all in one place.</div>
    </div>
    """,
    unsafe_allow_html=True,
)
if HERO_PHOTO:
    st.markdown(f'<img class="hero-photo" src="{HERO_PHOTO}" alt="Pakistani food">', unsafe_allow_html=True)
st.markdown('<div class="bunting">🎉🌶️🍢🫓🍛🥘🍢🌶️🎉</div>', unsafe_allow_html=True)

try:
    cities = q(CITIES_SQL)["name"].tolist()
    meals = q(MEALS_SQL)["meal_type"].tolist()
except Exception as error:
    st.error("Could not connect to the database. Please check the settings in .streamlit/secrets.toml.")
    st.code(str(error))
    st.stop()


# ---------------------------------------------------------------- screen 1: search
if st.session_state.page == "search":
    st.markdown('<div class="section-title">Find your <span>Zaiqa</span></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="how"><b>How to use:</b> choose a city, a meal and how spicy you like your food, '
        "then tap <b>Find dishes</b>. Open any dish to see its ingredients and where to eat it.</div>",
        unsafe_allow_html=True,
    )

    city = st.selectbox(
        "📍 City", cities, index=cities.index("Lahore") if "Lahore" in cities else 0
    )
    meal = st.selectbox("🕐 Meal type", ["Any"] + meals, format_func=lambda m: "Any meal 🍽️" if m == "Any" else m.title())
    spice = st.selectbox("🌶️ Spice level", ["Any", "mild", "medium", "spicy"], format_func=lambda s: SPICE_LABELS[s])
    st.caption("Note: spice level is known for only 17 of our 44 dishes, so choosing a level can show fewer results.")

    if st.button("🔍 Find dishes", type="primary", width="stretch"):
        st.session_state.search = (city, meal, spice)

    if "search" in st.session_state:
        s_city, s_meal, s_spice = st.session_state.search
        meal_filter = None if s_meal == "Any" else s_meal
        spice_filter = None if s_spice == "Any" else s_spice
        dishes = q(DISHES_SQL, (s_city, meal_filter, meal_filter, spice_filter, spice_filter))

        st.markdown(f'<div class="section-title">Top dishes in <span>{escape(s_city)}</span></div>', unsafe_allow_html=True)
        if dishes.empty:
            st.info("No dish matches these choices. Try 'Any' for meal type or spice level.")
        for position, (_, row) in enumerate(dishes.iterrows(), start=1):
            with st.container(border=True):
                kind = '<span class="badge b-veg">🥬 Veg</span>' if row["is_veg"] else '<span class="badge b-nonveg">🍖 Non-veg</span>'
                spice_text = SPICE_SHORT.get(row["spice_level"], "Spice not listed")
                st.markdown(
                    f'<span class="rank">#{position}</span><span class="dish-name">{escape(str(row["dish"]))}</span><br>'
                    f"{kind}"
                    f'<span class="badge b-info">📂 {escape(str(row["category"] or "n/a"))}</span>'
                    f'<span class="badge b-info">🕐 {escape(str(row["meal_type"] or "n/a").title())}</span>'
                    f'<span class="badge b-spice">{escape(spice_text)}</span>',
                    unsafe_allow_html=True,
                )
                st.button(
                    "👀 View details",
                    key=f"view_{row['dish_id']}",
                    on_click=go,
                    args=("dish",),
                    kwargs={"dish_id": int(row["dish_id"]), "dish_city": s_city},
                )

# ---------------------------------------------------------------- screen 2: dish details
elif st.session_state.page == "dish":
    st.button("⬅️ Back to results", on_click=go, args=("search",))
    dish_id = st.session_state.dish_id
    dish = q(DISH_SQL, (dish_id,)).iloc[0]
    ingredients = q(INGREDIENTS_SQL, (dish_id,))["ingredient"].tolist()

    st.markdown(f'<div class="section-title">{escape(str(dish["name"]))}</div>', unsafe_allow_html=True)
    kind = '<span class="badge b-veg">🥬 Veg</span>' if dish["is_veg"] else '<span class="badge b-nonveg">🍖 Non-veg</span>'
    spice_text = SPICE_SHORT.get(dish["spice_level"], "Spice not listed")
    st.markdown(
        f"{kind}"
        f'<span class="badge b-info">🕐 {escape(str(dish["meal_type"] or "meal type not listed").title())}</span>'
        f'<span class="badge b-spice">{escape(spice_text)}</span>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown("### 🧂 Ingredients")
        if ingredients:
            st.markdown("".join(f'<span class="chip">{escape(str(item))}</span>' for item in ingredients), unsafe_allow_html=True)
        else:
            st.write("No ingredients are listed for this dish in our data.")

    st.write("")
    st.button(
        "🍴 Where can I eat it?",
        type="primary",
        width="stretch",
        on_click=go,
        args=("outlets",),
    )

# ---------------------------------------------------------------- screen 3: outlets
else:
    st.button("⬅️ Back to dish", on_click=go, args=("dish",))
    dish_id = st.session_state.dish_id
    city = st.session_state.dish_city
    dish_name = q(DISH_SQL, (dish_id,)).iloc[0]["name"]
    outlets = q(OUTLETS_SQL, (dish_id, city))

    st.markdown(f'<div class="section-title">{escape(str(dish_name))} in <span>{escape(city)}</span></div>', unsafe_allow_html=True)
    if outlets.empty:
        st.info(
            "No outlet in our data has this dish in its name. "
            "We match outlets to dishes by the dish name inside the outlet name."
        )
    else:
        st.markdown(f'<div class="stat">🎯 {len(outlets)} outlets serve this dish</div>', unsafe_allow_html=True)
        points = outlets[["latitude", "longitude"]].apply(pd.to_numeric)
        st.map(points)
        outlets["address"] = outlets["address"].fillna("Address not available")
        outlets = outlets.rename(columns={"outlet": "Outlet", "address": "Address"})
        st.dataframe(outlets[["Outlet", "Address"]], hide_index=True, width="stretch")

# ---------------------------------------------------------------- footer
st.markdown('<div class="stripe"></div><div class="foodstrip">🍢 🫓 🍛 🥘 🍗 🍚 🫖</div>', unsafe_allow_html=True)
