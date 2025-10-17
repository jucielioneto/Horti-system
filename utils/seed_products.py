from models.produto import init_schema, seed_default_stores, upsert_product


ITEMS = [
    ("1778", "ABACATE ORGANICO KG", "KG"),
    ("1915", "ABACAXI ORGANICO UN", "UN"),
    ("2009", "ABOBORA CABOTIA (JAPONESA) KG", "KG"),
    ("3041", "ABOBORA MARANHAO ORG KG", "KG"),
    ("1880", "ABOBRINHA ORGANICA 600 KG", "KG"),
    ("5433", "ACEROLA CONG 1KG", "KG"),
    ("1882", "AIPIM ORGANICO KG", "KG"),
    ("3222", "ALFACE AMERICANA ORGANICO UN", "UN"),
    ("10052", "ALFACE LISA ROXA ORGANICA", "UN"),
    ("3470", "ALFACE CRESPA ORGANICA", "UN"),
    ("1883", "ALHO DENTE DE ALHO ORGANICO KG", "KG"),
    ("1916", "ALHO PORO ORGANICO UM", "UN"),
    ("4907", "AMORA CONG SITIO ARCANJO ORG 1KG", "UN"),
    ("2359", "BANANA D´AGUA (CATURRA) ORGANICA KG", "KG"),
    ("1884", "BANANA DA PRATA ORGANICA KG", "KG"),
    ("1885", "BANANA DA TERRA ORGANICA KG", "KG"),
    ("1887", "BANANA MACA ORGANICA KG", "KG"),
    ("2616", "BATATA DOCE ORGANICA KG", "KG"),
    ("4306", "BATATA DOCE ROSA ORGANICA KG", "KG"),
    ("3835", "BATATA DOCE POLPA LARANJA ORG KG", "KG"),
    ("4790", "BATATA DOCE POLPA ROXA ORG KG", "KG"),
    ("3765", "BATATA DOCE ROXA ORGANICA KG", "KG"),
    ("1889", "BATATA INGLESA ORGANICA KG", "KG"),
    ("4429", "BATATA YAKON KG", "KG"),
    ("1890", "BERINJELA ORGANICA KG", "KG"),
    ("1919", "BETERRABA ORGANICA KG", "KG"),
    ("1918", "BETERRABA ORGANICA UN", "UN"),
    ("3962", "BROCOLIS ORGANICA KG", "UN"),
    ("1892", "CEBOLA BRANCA ORGANICA KG", "KG"),
    ("1893", "CEBOLA ROXA ORGANICA KG", "KG"),
    ("1894", "CENOURA ORGANICA KG", "KG"),
    ("1920", "CENOURA ORGANICA UN", "UN"),
    ("904", "CHUCHU ORGANICO KG", "KG"),
    ("1895", "COCO SECO ORGANICO KG", "UN"),
    ("2777", "COUVE-FLOR ORG UNID", "UN"),
    ("3921", "FEIJÃO VERDE SEM AGRO KG", "KG"),
    ("517", "GENGIBRE ORG KG", "KG"),
    ("1897", "GOIABA ORGANICA KG", "KG"),
    ("1859", "INHAME ORGANICO KG", "KG"),
    ("1899", "LARANJA PERA ORGANICA KG", "KG"),
    ("907", "LIMA ORGANICA KG", "KG"),
    ("4120", "LIMAO CRAVO ORGANICO KG", "KG"),
    ("1900", "LIMAO ORGANICO KG", "KG"),
    ("3821", "LIMAO GALEGO ORGANICO KG", "KG"),
    ("4304", "MACA ORGANICA KG", "KG"),
    ("1903", "MAMAO FORMOSA ORGANICO KG", "KG"),
    ("1903", "MAMAO  PAPAYA ORGANICO KG", "KG"),
    ("489", "MANGA ESPADA ORGANICA KG", "KG"),
    ("2666", "MANGA TOMY ORGANICA KG", "KG"),
    ("1905", "MARACUJA ORGANICO KG", "KG"),
    ("1906", "MAXIXE ORGANICO KG", "KG"),
    ("1921", "MELANCIA ORGANICA KG", "KG"),
    ("2673", "MELAO AMARELO ORGANICO KG", "KG"),
    ("1922", "MILHO VERDE ORGANICO UN", "UN"),
    ("1971", "MORANGO FRES SITIO ARC PREM CONG ORG KG", "KG"),
    ("1975", "MORANGO FRES SITIO ARC PREM ORG 250G", "UN"),
    ("2370", "PEPINO JAPONES ORGANICO KG", "KG"),
    ("1907", "PEPINO ORGANICO KG", "KG"),
    ("2459", "PERA ORGANICA KG", "KG"),
    ("498", "PIMENTA FRESCA ORGANICA KG", "KG"),
    ("1908", "PIMENTAO ORGANICO KG", "KG"),
    ("2043", "PINHA ORGANICO KG", "KG"),
    ("1909", "QUIABO ORGANICO KG", "KG"),
    ("500", "RABANETE ORGANICO KG", "KG"),
    ("575", "RAIZ DE CURCUMA FRESCA KG", "KG"),
    ("3480", "REPOLHO ROXO ORGANICO KG", "KG"),
    ("1910", "REPOLHO VERDE ORGANICO KG", "KG"),
    ("2455", "ROMÃ ORGANICO KG", "KG"),
    ("1911", "TANGERINA ORGANICA KG", "KG"),
    ("4123", "TOMATE CEREJA EM COMBUCA ORG", "UN"),
    ("1912", "TOMATE CEREJA COM SOLO VIVO ORG KG", "UN"),
    ("1976", "TOMATE GRAPE  SITIO ARCANJO ORG 180GR", "UN"),
    ("1913", "TOMATE ORGANICO KG", "KG"),
    ("2889", "UMBU-CAJA ORGANICA KG", "KG"),
    ("3516", "UVA S/ SEMENTE ORGANICA 500G UN", "UN"),
    ("5526", "UVA C/ SEMENTE ORGANICA 500G UN", "UN"),
    ("914", "VAGEM ORGANICA", "KG"),
]


def normalize_unit(unit: str) -> str:
    u = (unit or "").strip().upper()
    if u in ("UN", "UND", "UNID", "UM"):
        return "UN"
    return "KG" if u.startswith("K") else "UN"


def main() -> int:
    init_schema()
    seed_default_stores()
    count = 0
    for code, name, unit in ITEMS:
        upsert_product(str(code).strip(), name.strip(), normalize_unit(unit))
        count += 1
    return count


if __name__ == "__main__":
    total = main()
    print(f"Imported products: {total}")


