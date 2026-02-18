"""
config.py — الإعدادات المركزية لنظام مهووس
"""
import streamlit as st
import json, os

APP_VERSION     = "v21.0"
GEMINI_MODEL    = "gemini-2.0-flash"
ROWS_PER_PAGE   = 25
DB_PATH         = "mahwous.db"

# ── قراءة Secrets آمنة ──────────────────────
def _s(key, default=""):
    for fn in [
        lambda: st.secrets[key],
        lambda: st.secrets.get(key),
        lambda: os.environ.get(key, ""),
    ]:
        try:
            v = fn()
            if v:
                return v
        except Exception:
            pass
    return default

def _parse_keys():
    keys = []
    raw = _s("GEMINI_API_KEYS", "")
    if isinstance(raw, list):
        keys = [k for k in raw if k]
    elif isinstance(raw, str) and raw.strip():
        r = raw.strip()
        if r.startswith("["):
            try:
                keys = [k for k in json.loads(r) if k]
            except Exception:
                keys = [k.strip() for k in r.strip("[]").replace('"','').replace("'","").split(",") if k.strip()]
        else:
            keys = [r]
    for n in ["GEMINI_API_KEY","GEMINI_KEY_1","GEMINI_KEY_2","GEMINI_KEY_3","GEMINI_KEY_4"]:
        k = _s(n, "")
        if k and k not in keys:
            keys.append(k)
    return [k.strip() for k in keys if len(k.strip()) > 20]

GEMINI_API_KEYS = _parse_keys()

WEBHOOK_UPDATE_PRICES = _s("WEBHOOK_UPDATE_PRICES",
    "https://hook.eu2.make.com/99oljy0d6r3chwg6bdfsptcf6bk8htsd")
WEBHOOK_NEW_PRODUCTS  = _s("WEBHOOK_NEW_PRODUCTS",
    "https://hook.eu2.make.com/xvubj23dmpxu8qzilstd25cnumrwtdxm")

# ── إعدادات المطابقة ────────────────────────
MATCH_THRESHOLD = 62   # الحد الأدنى للمطابقة
AUTO_THRESHOLD  = 97   # فوق هذا → تلقائي بدون AI
PRICE_TOLERANCE = 10   # ريال → ✅ موافق عليها
AI_BATCH_SIZE   = 12   # عدد المنتجات لكل استدعاء Gemini

# ── كلمات الاستبعاد ─────────────────────────
REJECT_KEYWORDS = ["sample","عينة","عينه","decant","تقسيم","تقسيمة","split","miniature"]
TESTER_KEYWORDS = ["tester","تستر","تيستر"]
SET_KEYWORDS    = ["set","gift set","طقم","مجموعة","coffret"]

# ══════════════════════════════════════════════
# ماركات مهووس الكاملة (523 ماركة)
# استُخرجت من ملف ماركات_مهووس.csv
# ══════════════════════════════════════════════
BRANDS_EN = [
    "4711","Abercrombie","Acacia","Acqua Monaco","Acqua di Parma","Adam Levine",
    "Adidas","Afnan","Agent Provocateur","Aigner","Ajmal","Al Majed Oud",
    "Al-Ezz for Oud","Alaia Paris","Alexander McQueen","Alexander Wang",
    "Alfred Sung","Alghabra","Amouage","Amouroud","Amr Diab","Angel Schlesser",
    "Anna Sui","Annick Goutal","Antonio Banderas","Antonio Puig","Aquolina",
    "Aramis","Ard Al Khaleej","Armaf","Armand Basi","Atkinsons",
    "Atelier Cologne","Atelier Des Ors","Azzaro","BDK","Baldessarini",
    "Balenciaga","Balmain","Banafa for Oud","Bentley","Beyonce","Bill Blass",
    "Billie Eilish","Blumarine","Boadicea","Bois 1920","Bond No 9",
    "Bottega Veneta","Boucheron","Brioni","Britney Spears","Brut","Burberry",
    "Bvlgari","Byredo","Cacharel","Calvin Klein","Caron","Cartier","Carven",
    "Cerruti","Chanel","Charlotte Tilbury","Charriol","Chloe","Chopard",
    "Christian Audigier","Christian Lacroix","Christian Louboutin",
    "Clive Christian","Clinique","Coach","Comme des Garcons","Comptoir Sud Pacifique",
    "Costume National","Courreges","Creed","Cristiano Ronaldo","Davidoff",
    "Diesel","Dior","Diptyque","Dolce Gabbana","Donna Karan","Dsquared",
    "Dunhill","Elie Saab","Elizabeth Arden","Elizabeth Taylor","Escada",
    "Escentric Molecules","Estee Lauder","Etro","Ex Nihilo","Fendi","Ferrari",
    "Floris","Franck Olivier","Fred Hayman","Frederic Malle","Gianfranco Ferre",
    "Givenchy","Giorgio Armani","Giorgio Beverly Hills","Goldfield Banks",
    "Gres","Gucci","Guerlain","Guess","Guy Laroche","Hermes","Histoires de Parfums",
    "Hollister","Houbigant","Hugo Boss","Hummer","Iceberg","Initio","Issey Miyake",
    "Jacomo","Jacques Bogart","Jaguar","James Bond","Jean Paul Gaultier",
    "Jean Patou","Jennifer Lopez","Jeroboam","Jessica Simpson","Jil Sander",
    "Jimmy Choo","Jo Malone","John Varvatos","Joop","Jovan","Jovoy Paris",
    "Juicy Couture","Juliette Has A Gun","Justin Bieber","Karl Lagerfeld",
    "Katy Perry","Kayali","Kenneth Cole","Kenzo","Kilian","Kim Kardashian",
    "Kiton","Korloff","La Perla","Lacoste","Lady Gaga","Lalique","Lamborghini",
    "Lancome","Lanvin","Laura Biagiotti","Laurent Mazzone","Le Labo","Liz Claiborne",
    "Loewe","Lolita Lempicka","Lorenzo Villoresi","Louis Vuitton","MAC","Mancera",
    "Mandarina Duck","Marc Jacobs","Mariah Carey","Maserati","Masque Milano",
    "Mauboussin","Memo Paris","Mercedes-Benz","Mexx","Michael Kors","Missoni",
    "Miu Miu","Montale","Montblanc","Moschino","Mugler","Narciso Rodriguez",
    "Nasomatto","Nautica","Nina Ricci","Nishane","Oscar De La Renta",
    "Paco Rabanne","Paloma Picasso","Paris Hilton","Paul Smith","Penhaligons",
    "Pepe Jeans","Perry Ellis","Police","Porsche Design","Prada","Ralph Lauren",
    "Rasasi","Reminiscence","Revlon","Rihanna","Roberto Cavalli","Rochas",
    "Roger Gallet","Roja Dove","Rosendo Mateu","Salvador Dali","Salvatore Ferragamo",
    "Sean John","Serge Lutens","Shakira","Shiseido","Sisley","Stella McCartney",
    "T Dupont","Tauer Perfumes","Ted Baker","Ted Lapidus","Thameen",
    "Thomas Kosmala","Tiffany","Tiziana Terenzi","Tom Ford","Tommy Hilfiger",
    "Tory Burch","Tous","Trussardi","Ulric de Varens","Valentino","Van Cleef",
    "Vera Wang","Versace","Vertus","Victor Rolf","Victorias Secret",
    "Vince Camuto","Xerjoff","Yves Saint Laurent","Yves Rocher","Zegna",
    "Arabian Oud","Lattafa","Al Haramain","Rasasi","Ajmal","Armaf","Gissah",
    "Deraah","Nasmat Najd","Khalasat",
]

BRANDS_AR = [
    "جيفنشي","فيرساتشي","أجمل","أرماف","رصاصي","لطافة","لطافه","أمواج",
    "كريد","ديور","شانيل","قوتشي","برادا","توم فورد","أرماني","غيرلان",
    "هيرميس","كارتييه","بولغاري","فالنتينو","جورجيو أرماني","هوغو بوس",
    "كالفن كلاين","رالف لورين","تومي هيلفيغر","مون بلان","دافيدوف",
    "جو مالون","باكو رابان","فراجرانس دو بوا","مانسيرا","مونتال",
    "العربية للعود","الحرمين","بربري","بنتلي","باريس هيلتون","كارولينا هيريرا",
    "جيمي شو","لانكوم","لافيرن","لاكوست","لاليك","لو لابو","مارك جاكوبس",
    "مايكل كورس","ميمو باريس","نارسيسو","نيشاني","زيرجوف","إيف سان لوران",
    "إيسي مياكي","إيلي صعب","إسكادا","فندي","فيراري","باكوما","بوشرون",
    "كليفكريستيان","كيليان","سيرج لوتنس","ديبتيك","جان بول غولتير",
    "ترساردي","روجا دوف","فريدريك مال","ديزل","موغلر","جيسادا","سمام",
    "درعة","نسمات نجد","خلاصات","قصة",
]

# دمج موحد لاستخدامه في المحرك
ALL_BRANDS = sorted(set(BRANDS_EN + BRANDS_AR))
