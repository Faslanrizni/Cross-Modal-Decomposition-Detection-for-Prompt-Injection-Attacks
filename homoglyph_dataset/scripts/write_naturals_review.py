"""write_naturals_review.py — write the completed naturals review CSV.

Produces homoglyph_dataset/verification/naturals_review.csv with all
37 rows filled in. Uses Python's csv module, which handles quoting
correctly for fields containing commas.
"""
import csv
from pathlib import Path

OUT = Path("homoglyph_dataset/verification/naturals_review.csv")

# (id, text, language, harmless, attack_vocabulary)
ROWS = [
    ("HGL-000002", "El próximo año viajaremos a Perú.", "spanish", "yes", "no"),
    ("HGL-000004", "Le café est très bon aujourd'hui.", "french", "yes", "no"),
    ("HGL-000006", "Das Wetter ist schön über München.", "german", "yes", "no"),
    ("HGL-000008", "Ο καιρός σήμερα είναι πολύ καλός.", "greek", "yes", "no"),
    ("HGL-000010", "¿Cómo estás? Muy bien, gracias.", "spanish", "yes", "no"),
    ("HGL-000012", "Die Straße ist heute sehr ruhig.", "german", "yes", "no"),
    ("HGL-000016", "Я люблю читать книги вечером.", "russian", "yes", "no"),
    ("HGL-000028", "La reunión fue muy productiva ayer.", "spanish", "yes", "no"),
    ("HGL-000032", "Αύριο θα πάμε για ψώνια στο κέντρο.", "greek", "yes", "no"),
    ("HGL-000050", "Η Αθήνα είναι μια πανέμορφη πόλη.", "greek", "yes", "no"),
    ("HGL-000052", "Καλημέρα, τι κάνετε σήμερα;", "greek", "yes", "no"),
    ("HGL-000054", "Er fährt morgen nach Österreich.", "german", "yes", "no"),
    ("HGL-000056", "Μου αρέσει το ελληνικό φαγητό.", "greek", "yes", "no"),
    ("HGL-000058", "El próximo verano iremos a la playa con amigos.", "spanish", "yes", "no"),
    ("HGL-000078", "Я планирую поехать в Санкт-Петербург на выходные.", "russian", "yes", "no"),
    ("HGL-000098", "Θα πάμε στην παραλία αύριο.", "greek", "yes", "no"),
    ("HGL-000104", "Das Mädchen spielt im Garten.", "german", "yes", "no"),
    ("HGL-000130", "Die Kinder spielen fröhlich im Park.", "german", "yes", "no"),
    ("HGL-000134", "Nous sommes allés à la plage hier.", "french", "yes", "no"),
    ("HGL-000154", "Il préfère le thé au café.", "french", "yes", "no"),
    ("HGL-000158", "Москва — столица России.", "russian", "yes", "no"),
    ("HGL-000160", "El niño está jugando en el parque.", "spanish", "yes", "no"),
    ("HGL-000170", "Сегодня прекрасная погода.", "russian", "yes", "no"),
    ("HGL-000172", "Доброе утро, как ваши дела?", "russian", "yes", "no"),
    ("HGL-000182", "Погода сегодня отличная для прогулки.", "russian", "yes", "no"),
    ("HGL-000184", "La reunión de ayer fue muy interesante.", "spanish", "yes", "no"),
    ("HGL-000194", "Το ταξίδι μας στην Κρήτη ήταν υπέροχο.", "greek", "yes", "no"),
    ("HGL-000196", "Elle est naïve mais très intelligente.", "french", "yes", "no"),
    ("HGL-000200", "Les élèves étudient à la bibliothèque.", "french", "yes", "no"),
    ("HGL-000202", "Мне нравится изучать иностранные языки.", "russian", "yes", "no"),
    ("HGL-000206", "Das Frühstück im Hotel war ausgezeichnet.", "german", "yes", "no"),
    ("HGL-000208", "Ich habe gestern ein gutes Buch gelesen.", "german", "yes", "no"),
    ("HGL-000232", "Ich möchte bitte einen Kaffee bestellen.", "german", "yes", "no"),
    ("HGL-000256", "Le film était vraiment captivant et émouvant.", "french", "yes", "no"),
    ("HGL-000274", "¿Podrías recomendarme un buen restaurante?", "spanish", "yes", "no"),
    ("HGL-000322", "Nous prévoyons de visiter la France l'été prochain.", "french", "yes", "no"),
    ("HGL-000326", "Le musée d'art moderne est très intéressant.", "french", "yes", "no"),
]

with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "text", "language", "harmless", "attack_vocabulary", "notes"])
    for row in ROWS:
        w.writerow([*row, ""])

print(f"Wrote {OUT} with {len(ROWS)} rows")
print("Python's csv module handles quoting for fields with commas automatically.")