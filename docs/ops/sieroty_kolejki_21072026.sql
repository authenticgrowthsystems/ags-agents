-- A5 (21/07): sieroty kolejki - wiersze pq w 'review'/'scheduled' nalezace do materialow
-- odrzuconych/zarchiwizowanych (dowod: 242/261/262 ze slotami 21/07 smieca raport KOLEJKA
-- i alarmy ZWIS). Fix na przyszlosc jest w matnav 'no'; to sprzata zaszlosci.
UPDATE post_queue pq SET status='rejected', updated_at=NOW()
FROM content_items ci
WHERE ci.id = pq.content_item_id
  AND pq.status IN ('review','scheduled','queued')
  AND ci.status IN ('rejected','archived');
-- kontrola (oczekiwane: 0 wierszy)
SELECT pq.id, pq.status AS pq_status, ci.status AS item_status
FROM post_queue pq JOIN content_items ci ON ci.id=pq.content_item_id
WHERE pq.status IN ('review','scheduled','queued') AND ci.status IN ('rejected','archived');
