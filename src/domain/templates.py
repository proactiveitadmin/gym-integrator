DEFAULT_FAQ = {
    "hours": "Godziny otwarcia: pn-pt 6:00-22:00, sb-nd 8:00-20:00.",
    "price": "Cennik: karnet miesięczny od 149 PLN, jednorazowe wejście 30 PLN.",
    "location": "Adres: ul. Przykładowa 1, 00-000 Miasto.",
    "contact": "Kontakt: +48 123 123 123, email: klub@example.com",
}
def render_template(template_str: str, context: dict) -> str:
    out = template_str
    for k, v in (context or {}).items():
        out = out.replace("{"+k+"}", str(v))
    return out
