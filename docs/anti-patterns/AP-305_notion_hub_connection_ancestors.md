# AP-305: Notion 404 = brak dostepu integracji, nie zle ID

**Data incydentu:** 05/07/2026, TASK #71 Faza D (silnik ETL, 3 strony GHL).

## Co poszlo nie tak
Silnik ETL dostal `404 Not Found` na 3 zrodlach (strony pod 🏠 Nawrocki Business Hub),
mimo ze page ID byly poprawne (zweryfikowane fetchem przez MCP tego samego dnia).

## Przyczyna
Notion API zwraca 404 rowniez wtedy, gdy strona ISTNIEJE, ale integracja (token `ntn_`)
nie ma do niej connection. MCP uzywa uprawnien uzytkownika (widzi caly workspace);
token integracji widzi TYLKO drzewa stron, ktorym recznie dodano Connection.
Dotychczasowe zrodla #71 lezaly pod AGS Operations Hub (udostepniony) - nowe lezaly
pod Nawrocki Business Hub (nieudostepniony). Uwaga: w workspace sa 3+ integracje
(n8n-TNM, n8n-AGS, AGS Automation) - connection musi dostac TA, ktorej klucz siedzi
w app_secrets, nie ktorakolwiek.

## Regula
1. Przed dodaniem zrodla ETL spoza dotychczas udostepnionego drzewa: sprawdz/zapewnij
   Connection integracji na page-root nowego drzewa (dziedziczy na podstrony).
2. Diagnoza 404 ZAWSZE z dowodu: `GET /v1/users/me` tokenem z sejfu (nazwa bota mowi,
   KTOREJ integracji szukac w Connections) + `GET /v1/pages/{id}` (`%{http_code}`).
3. To, ze MCP widzi strone, NIE znaczy ze widzi ja token ETL.
