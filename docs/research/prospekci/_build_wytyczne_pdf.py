# -*- coding: utf-8 -*-
"""Generator PDF wytycznych do rozmowy z Grupa Adamietz (v2, 22/07/2026).
Uruchomienie (z tego katalogu): python _build_wytyczne_pdf.py
Wymaga: reportlab + czcionki Arial (Windows). Aktualizacja = edycja story + rerun."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('PL', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('PLB', 'C:/Windows/Fonts/arialbd.ttf'))
GRAF = HexColor('#1a1a1a')
AKC = HexColor('#8a6d1a')
S = getSampleStyleSheet()
st_t = ParagraphStyle('t', parent=S['Title'], fontName='PLB', fontSize=17, textColor=GRAF, spaceAfter=2)
st_sub = ParagraphStyle('sub', parent=S['Normal'], fontName='PL', fontSize=9, textColor=HexColor('#666666'), spaceAfter=10)
st_h = ParagraphStyle('h', parent=S['Heading2'], fontName='PLB', fontSize=12.5, textColor=AKC, spaceBefore=11, spaceAfter=4)
st_n = ParagraphStyle('n', parent=S['Normal'], fontName='PL', fontSize=10, leading=14, spaceAfter=3)
st_b = ParagraphStyle('b', parent=st_n, leftIndent=6 * mm, bulletIndent=2 * mm)
st_q = ParagraphStyle('q', parent=st_n, leftIndent=6 * mm, textColor=HexColor('#333333'),
                      backColor=HexColor('#f4efe2'), borderPadding=4, spaceBefore=3, spaceAfter=5)


def P(t, s=st_n):
    return Paragraph(t, s)


def B(t):
    return Paragraph('• ' + t, st_b)


story = [
    P('WYTYCZNE DO ROZMOWY: GRUPA ADAMIETZ', st_t),
    P('AGS | wersja 2, 22/07/2026 (+ ściąga relacyjna z researchu osobowego) | poufne', st_sub),

    P('1. CEL ROZMOWY (jeden jedyny)', st_h),
    P('<b>Umówić PŁATNĄ DIAGNOZĘ przepływu informacji</b> (2-4 tygodnie, 15-30 tys. PLN).'),
    B('NIE sprzedajesz programu, NIE wysyłasz oferty PDF, NIE obiecujesz wdrożenia.'),
    B('Sukces = zgoda na diagnozę ALBO umówione spotkanie z decydentem. Nic innego się nie liczy.'),

    P('2. Z KIM ROZMAWIASZ', st_h),
    B('<b>Rajmund Adamietz</b> (właściciel, wizjoner): od kostki brukowej w Niemczech do 1,45 mld zł; '
      'wartości: śląski etos pracy, zaufanie, rodzina, sukcesja dla córek; Honorowy Obywatel Strzelec '
      'Opolskich, Złota Statuetka Lidera Polskiego Biznesu (BCC).'),
    B('<b>Łukasz Obrusznik</b> (wiceprezes, dyrektor generalny od 03/2025): w firmie od 2006, przeszedł '
      'wszystkie szczeble, MBA; Osobowość Branży 2025; prowadzi Data Center, energetykę i defense '
      '(Opolski Klaster Obronny).'),
    B('Firma: 873 pracowników, S.A., własne fabryki (ARPANEL, FORMOPEX, PREFAR), 18 przetargów '
      'za 178 mln zł w 2025.'),

    P('3. OTWARCIE (pierwsze 2 minuty)', st_h),
    B('Podziękuj za czas, powołaj się na Piotra JEDNYM zdaniem i zostaw ten wątek.'),
    B('Gratulacje z faktu (wybierz jeden): S.A. / Budowlana Firma Roku 2025 / droga od Kadłuba '
      'do Tesli i Sali Kongresowej.'),
    P('"Nie dzwonię z ofertą. Chciałem zapytać o parę rzeczy, bo to, jak rośniecie, jest z zewnątrz '
      'naprawdę ciekawe."', st_q),

    P('4. CO MÓWIĆ - osie rozmowy', st_h),
    B('<b>Język:</b> architektura informacji, przepływ ustaleń, "żeby nic nie ginęło". '
      'AI = narzędzie koordynacji, raz, bez hype.'),
    B('<b>Z Adamietzem:</b> długowieczność, sukcesja, firma działająca bez ciągłej obecności szefa. '
      'Zero przesady - u niego "słowo i podanie ręki" znaczą więcej niż umowa, więc lepiej obiecać mało.'),
    B('<b>Z Obrusznikiem:</b> płaska struktura przy 900 ludziach, rygor raportowania pod '
      'Data Center/defense, biuro ofert.'),
    B('<b>Słuchaj 70% czasu.</b> Każdy ich przykład to paliwo diagnozy.'),

    P('5. TRZY PYTANIA DIAGNOSTYCZNE', st_h),
    P('1. "Przy setkach dokumentów ofertowych - jak chronicie się, żeby kluczowe informacje wam '
      'nie uciekały?"', st_q),
    P('2. "Jak spinacie przepływ budowa - własne fabryki - podwykonawcy, żeby uniknąć głuchego '
      'telefonu?"', st_q),
    P('3. "Jak trzymacie rygor informacyjny pod Data Center i defense bez zatykania skrzynek '
      'inżynierów?"', st_q),

    P('6. CZEGO NIE MÓWIĆ - czerwone linie', st_h),
    B('ZERO nawiązań do opinii podwykonawców (płatności, komunikacja). '
      'Mów: "wyzwania komunikacyjne przy tej skali".'),
    B('ZERO pytań o szczegóły obiektów wojskowych.'),
    B('NIE proponuj "usprawnienia" ani "naprawy" - Ty PROJEKTUJESZ przepływ na kolejną dekadę.'),
    B('NIE wymieniaj nazw narzędzi. NIE zgadzaj się na "prześlijcie ofertę". '
      'NIE mów o cenach przed pytaniem.'),
    B('<b>Nigdy nie mów "nie da się"</b> - w tej firmie to słowo zakazane przez właściciela. '
      'I nie rozmawiaj wyłącznie o zysku - dla Adamietza zysk to efekt uboczny jakości i ludzi.'),

    P('7. PIENIĄDZE (gdy zapytają) - od góry, spokojnie', st_h),
    P('"Docelowo firmy tej skali robią z nami programy roczne rzędu 300-500 tysięcy. Ale nie od tego '
      'się zaczyna. Zaczyna się od diagnozy: 2-4 tygodnie, mapa gdzie informacja ginie i ile to '
      'kosztuje, plan co z tym zrobić - 15-30 tysięcy zależnie od zakresu. Po diagnozie sami '
      'zdecydujecie, czy cokolwiek dalej robimy."', st_q),
    B('Kotwica: przy 1,45 mld przychodu 0,1% poprawy marży = ok. 1,45 mln zł rocznie. '
      'Zysk netto spadł z 38 do 18 mln przy tych samych obrotach.'),
    B('<b>PODŁOGA: diagnoza nigdy poniżej 12 tys. zł.</b> "Próbka za 5 tysięcy" = niewłaściwa osoba, '
      'nie obniżka.'),

    P('8. PRZEWIDYWANE OBIEKCJE', st_h),
    P('<b>"Prześlijcie ofertę."</b> - "Oferta z półki byłaby zgadywaniem. Wolę 30 minut konkretnych '
      'pytań - wtedy albo powiem, gdzie mogę pomóc, albo uczciwie, że nie ma tematu."', st_q),
    P('<b>"Mamy IT, wdrażamy ERP."</b> - "Świetnie, ERP trzyma dane. Ja zajmuję się tym, co dzieje '
      'się MIĘDZY systemami i ludźmi: ustaleniami, które żyją w mailach i pamięci. Tego żaden ERP '
      'nie łapie."', st_q),
    P('<b>"Za drogo."</b> - Nie obniżaj. Koszt jednej zgubionej sprawy przy tej skali. '
      'Zawęź ZAKRES, nigdy cenę za tę samą pracę.', st_q),
    P('<b>"Czemu Pan, a nie duża firma?"</b> - "Duża firma przyśle zespół juniorów i 200 stron. '
      'Ja robię to osobiście, kończę planem i takie systemy buduję u siebie codziennie - mogę '
      'pokazać na żywo."', st_q),

    P('9. DOMKNIĘCIE', st_h),
    P('"Proponuję tak: dwa tygodnie diagnozy, konkretna mapa i plan. Jeśli po niej uznacie, że to '
      'nie to - rozchodzimy się i zostaje Wam mapa. Od kogo powinienem zacząć rozmowy '
      'o szczegółach?"', st_q),
    B('Po rozmowie NATYCHMIAST: notatka do Sprzedawcy (dziennik kapitański) + follow-up mail tego '
      'samego dnia: 3 zdania, zero PDF.'),

    PageBreak(),
    P('10. ŚCIĄGA RELACYJNA - RAJMUND ADAMIETZ', st_h),
    P('<b>Jego dewizy (znaj na pamięć, cytuj ostrożnie):</b>'),
    B('"Rzeczy niemożliwe załatwiamy od ręki, a na cuda trzeba trochę poczekać."'),
    B('"Nie ma rozłożystego drzewa bez mocnych korzeni" (o powrocie z Niemiec do Kadłuba).'),
    B('"Słowo i podanie ręki są dla mnie równie ważne jak umowy grubości książki."'),
    P('<b>Tematy naturalnie otwierające rozmowę:</b>'),
    B('Śląsk i Kadłub: wrócił z Niemiec, żeby ludzie stąd nie musieli wyjeżdżać za pracą.'),
    B('Droga od układania kostki brukowej do fabryki Tesli i remontu Sali Kongresowej.'),
    B('Zaufanie jako rzadkość w dzisiejszym biznesie (jego ulubiona struna).'),
    B('Sukcesja: przekazanie firmy córkom, utrzymanie rodzinnego charakteru.'),
    B('Renowacja zabytków i dziedzictwo regionu (publiczna pasja).'),
    P('<b>Sponsoring (wspólne tematy sportowe):</b> Asseco Resovia (siatkówka), PGE Wybrzeże Gdańsk '
      '(ręczna), szachy w Strzelcach, Silesia Equestrian, Poland Business Run.'),
    P('<b>Czego przy nim nie robić:</b> korporacyjnej nowomowy i rozwiązań komplikujących proste '
      'rzeczy; słowa "nie da się"; rozmowy wyłącznie o pieniądzach.'),

    P('11. ŚCIĄGA RELACYJNA - ŁUKASZ OBRUSZNIK', st_h),
    P('<b>Tematy otwierające:</b>'),
    B('Data Center i infrastruktura krytyczna: jego priorytet; Defence Cooperation Forum, '
      'Opolski Klaster Obronny, współpraca z PGZ.'),
    B('100% polskiego kapitału + prosta struktura = szybsze decyzje niż korporacje (jego teza).'),
    B('20 lat w firmie: od wsparcia produkcji do CEO - dowód kultury organizacyjnej.'),
    B('Transformacja energetyczna (magazyny energii, Żarnowiec).'),
    P('<b>Czego przy nim nie robić:</b> teoretyzowania (praktyk z MBA - operacyjny konkret); '
      'traktowania Adamietz jak "zwykłej budowlanki"; pomijania roli założyciela.'),

    P('12. GDZIE MOŻNA ICH SPOTKAĆ (sierpień-październik 2026)', st_h),
    B('<b>Targi EXPOBUD, 19-20.09, PreZero Arena Gliwice</b> - kluczowe targi regionalne '
      '(równolegle EXPO-INSTAL: energetyka/OZE - działka Obrusznika).'),
    B('Mecze Asseco Resovia (PlusLiga) i PGE Wybrzeże Gdańsk (Superliga) - sezon od przełomu '
      'sierpnia i września; Adamietz sponsoruje oba kluby.'),
    B('Gale Builder Awards i Opolskie Laury - dopiero wiosna 2027; BCC (jest członkiem) organizuje '
      'wydarzenia w ciągu roku.'),
    P('Pełne portrety i źródła: "Portrety Relacyjne" + "Analiza Kierownictwa" w tym samym katalogu.',
      st_sub),
]

doc = SimpleDocTemplate('WYTYCZNE_ROZMOWA_adamietz.pdf', pagesize=A4,
                        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
                        title='Wytyczne do rozmowy: Grupa Adamietz (v2)', author='AGS')
doc.build(story)
import os
print('PDF v2 OK:', os.path.getsize('WYTYCZNE_ROZMOWA_adamietz.pdf'), 'bajtow')
