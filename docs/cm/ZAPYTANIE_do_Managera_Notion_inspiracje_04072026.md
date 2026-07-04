# ZAPYTANIE: inspiracje z Notion dla planera CM - od BE do Managera AGS

**Data:** 04/07/2026. **Kontekst:** planer Fazy 2 DZIAŁA E2E (pierwszy plan: 27 pozycji, zarys miesiąca,
kadencja kanoniczna). Planer czerpie dziś ze SCHOWKA (tabela inspirations) - Tomasz: "więcej inspiracji
jest w Notion" i prosi o rozstrzygnięcie, skąd CM ma je brać, dopóki ich nie wyczerpie.

## Pytanie do Managera (właściciela audytu Notion per decyzja #7 z 04/07)
1. **Które konkretnie strony/bazy Notion** zawierają inspiracje CONTENTOWE do skonsumowania przez CM?
   (Z Twojego audytu strukturalnego: content plans / zlecenia #31-49 / X Content Queue / inne pule pomysłów -
   proszę o listę page/database ID z krótkim opisem zawartości i formatu.)
2. Które z nich są ŻYWE (Tomasz dopisuje) vs ZAMROŻONE (jednorazowa pula do wyczerpania)?
3. Czy coś z tej puli jest już obsługiwane przez legacy X-agenta (Notion X Content Queue) i ma tam ZOSTAĆ
   do czasu cutoveru D4 - żeby ETL nie zdublował źródła?

## Rekomendacja BE (do zatwierdzenia): JEDNORAZOWY ETL do schowka, nie żywy odczyt Notion
- **Mechanizm:** BE robi jednorazowy import wskazanych pul -> tabela `inspirations` (kolumny już czekają:
  source='notion', **notion_page_id** - była projektowana pod to od 31/05), status='new', brand per mapping.
  Duplikaty łapane po notion_page_id (idempotentnie, można doimportowywać).
- **Dlaczego nie żywy odczyt:** kanon "baza = jedyne źródło prawdy" + CM nie powinien mieć zależności od
  API Notion (sprzedawalność: klient może nie mieć Notion); planer już umie czerpać ze schowka - zero zmian kodu.
- **Zamrożone pule:** import raz, w Notion oznaczyć stronę "ZAIMPORTOWANE DO CM [data]" (bez kasowania).
- **Żywe pule:** przejściowo re-import na żądanie ("dociągnij z Notion") albo lekki cron shadow-sync 1x/dzień
  (tylko INSERT nowych po notion_page_id) - do decyzji Managera; docelowo żywe pule umierają naturalnie,
  bo intake przejmuje Idea Bot/Sekretarka (wszystko z Telegrama, kanon).
- **Zgodność z D4:** to NIE jest pełna migracja Notion->Postgres (ta zostaje PO MVP per D4) - to ETL jednej
  domeny (inspiracje), zsynchronizowany z Fazą 2 dokładnie tak, jak zarekomendowałeś przy pytaniu #7.

**Proszę o:** listę źródeł (pkt 1-3) + approve rekomendacji. Po odpowiedzi BE wykonuje ETL (skrypt
read-only na Notion, INSERT do inspirations, raport z liczbami per pula).
