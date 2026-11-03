import json,sqlite3,tempfile
from pathlib import Path
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from database import CARD_DB,CardDatabase
from discovery import DiscoveryService
from identification import IdentificationCandidate,IdentificationResult
from journal import JournalRepository,JournalSession

root=Path(tempfile.mkdtemp(prefix='vitadex-review-'))
def match(organism):
 return IdentificationResult((IdentificationCandidate(organism,1.0),),source='review-probe')
dog=CARD_DB.organisms['Dog']
# Taxonomic synonyms should be one discovery but currently are different keys.
session=JournalSession(JournalRepository(root/'aliases.sqlite3'))
service=DiscoveryService(CARD_DB,session)
a=service.encounter(match(dog));b=service.encounter(match(replace(dog,scientific_name='Canis familiaris')))
print('alias_probe:', a.is_first,b.is_first,'cards=',len(session.cards))
# Paired arrivals from future sensors can both pass the lookup before either saves.
catalog=CardDatabase.from_json(json.loads(Path('data/database.json').read_text()))
barrier=Barrier(2); original=catalog.build_card
catalog.build_card=lambda organism: (barrier.wait(timeout=3),original(organism))[1]
session=JournalSession(JournalRepository(root/'concurrent.sqlite3'))
service=DiscoveryService(catalog,session)
with ThreadPoolExecutor(max_workers=2) as pool:
 results=list(pool.map(lambda _:service.encounter(match(dog)),range(2)))
print('concurrency_probe: first_results=',sum(x.is_first for x in results),'memory_cards=',len(session.cards))
# Interrupted migration may leave an empty SQLite file before records commit.
legacy=root/'journal.json'; db=root/'migration.sqlite3'
legacy.write_text(json.dumps({'version':1,'cards':[JournalRepository._card_to_dict(CARD_DB.build_card(dog))]}))
sqlite3.connect(db).close()
print('interrupted_migration_probe: legacy_cards=1, loaded=',len(JournalRepository(db,legacy).load_cards()))
# The catalog loader omits full scalar/type validation performed by sync's JSON Schema.
data=json.loads(Path('data/database.json').read_text());data['organisms'][0]['description']=17
invalid=CardDatabase.from_json(data)
print('catalog_type_probe: accepted_description_type=',type(invalid.organisms['Dog'].description).__name__)
# A claim-derived card field can drift from the source-mapped organism snapshot.
card=CARD_DB.build_card(dog);card.selected_details['Habitat']='Invented habitat unrelated to cited source'
repo=JournalRepository(root/'claims.sqlite3');repo.save_cards([card])
print('claim_consistency_probe: accepted_inconsistent_habitat=',repo.load_cards()[0].selected_details['Habitat'])
