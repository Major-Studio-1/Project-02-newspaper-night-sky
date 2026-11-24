"""Build the local multi-group pulse page from the immutable research release."""
from pathlib import Path
import json, re, sqlite3, shutil, hashlib, datetime
from archive_data.consumer import release_path, verified_file
import time


# On this Windows machine another process (a scanner or an indexer) sometimes holds a file for a moment, and writing it
# fails with EINVAL or EACCES. Writes are tried again a few times instead of failing the whole build.
def _again(write):
    def go(self, *a, **k):
        for attempt in range(20):   # up to 10 seconds: a preview server or a page check elsewhere can hold a file that long
            try:
                return write(self, *a, **k)
            except OSError as e:
                if attempt == 19 or e.errno not in (13, 22):
                    raise
                time.sleep(.5)
    return go


Path.write_text = _again(Path.write_text)
Path.write_bytes = _again(Path.write_bytes)


def copy_if_changed(src, dst):
    """Copy src to dst unless dst already holds the same bytes. Rewriting every unchanged scan crop on each build sometimes
    failed on Windows (EINVAL while another process held the file for a moment), and it was never needed."""
    src, dst = Path(src), Path(dst)
    if dst.exists() and dst.stat().st_size == src.stat().st_size and dst.read_bytes() == src.read_bytes():
        return
    for attempt in range(20):
        try:
            shutil.copyfile(src, dst); return
        except OSError:
            if attempt == 19: raise
            time.sleep(.5)

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'outputs/newspaper_pulses_space'
release=release_path()
manifest=json.loads((release/'manifest.json').read_text(encoding='utf8'))
# The reviewed years. Each has display categories for its overview (an editorial grouping for colour, not part of the
# data release), named for that year, in the same three colour slots: the first is war in both years and the third
# American public life and government. Three colours are the most that stay distinguishable when any two can be on screen
# together. Every top-level story of a reviewed year needs exactly one category, or the build fails. 'children' lists the
# sub-stories shown under a story; 'expect' is the year's newspapers and surviving pages, checked against the release.
REVIEWED={
  # Round two (release v0.7.2) added nine stories; the user agreed the categories on 2026-11-09, with the Howe declarations
  # under Britain and Europe. Each category lists its stories in the order of their first printing.
  1776:{'categories':[
          ('war','War and the armies',['quebec-siege-1776','boston-evacuation-letter','barry-takes-edward','sloop-liberty-gunpowder','hopkins-nassau-letter',
                                       'stuart-letter-to-frontier-inhabitants','savannah-river-letter-13-may-1776','campbell-captured-letter','hudson-warships-1776','washington-patterson-interview','eighty-eight-battalions',
                                       'congress-intelligence-october-1776','gates-carleton-retreat']),
          ('britain','Britain and Europe',['king-speech-october-1775','wilkes-speech-commons','penn-before-the-lords','prohibitory-bill-commons',
                                           'dublin-paper-naval-force','ethan-allen-cork','london-address-to-king-1776','king-speech-may-1776','howe-declarations-1776']),
          ('government','Independence and American government',['congress-bills-of-credit','congress-fast-day-1776','congress-opens-ports','rhode-island-renunciation',
                                       'congress-may-15-resolution','virginia-independence-resolution','pennsylvania-new-instructions','declaration-of-independence',
                                       'cedars-cartel-report','prize-resolutions-extended','staten-island-conference'])],
        'children':{'quebec-siege-1776':['montgomery-letter-to-carleton','quebec-assault-report','quebec-camp-letter'],
                    'hudson-warships-1776':['haverstraw-bay-report','tappan-meadows-report','gondolas-attack-report','fire-ships-attack-report'],
                    'staten-island-conference':['conference-committee-departs','conference-committee-report'],
                    'penn-before-the-lords':['penn-examined-report','penn-examination-lords'],
                    'prohibitory-bill-commons':['prohibitory-bill-committee','prohibitory-clause-settled'],
                    'howe-declarations-1776':['howe-declaration-published-by-congress','howe-declaration-september']},
        'expect':(16,2319)},
  1797:{'categories':[
          ('war','War, revolution and foreign news',['boyd-bantry-coverage','tenerife-defeat-report','camperdown-dispatches','algerine-sicilian-battle',
                                                     'hermione-mutiny','barney-escapes-blockade','sonthonax-departure','quito-earthquake',
                                                     # round three (release v0.11.8, 23 November 2026): read again by the one rule at 4 papers
                                                     'truguet-letter-6-november-1796-ireland','bournonville-letter-3-brumaire-neuwied','crauford-letter-27-october-1796-moreau-retreats',
                                                     'berthier-letter-milan-28-november-1796','delarue-report-march-of-the-troops-august-1797','vienna-report-26-july-1797-peace-talks',
                                                     'nassau-letter-26-september-1797']),
          ('ships','Ships, privateers and wrecks',['peace-cayenne-context','peace-and-plenty-boarding','brothers-privateer-boarding','two-sisters-wreck','havana-french-captures']),
          ('public','American public life',['adams-senate-farewell','special-session-1797','blount-affair','brown-house-fire','congress-opening-nov-1797',
                                            'kosciuszko-land-warrant','jefferson-madison-letter','nh-governor-address-1797','wilmington-report-12-october-1797-spanish-posts'])],
        'children':{'boyd-bantry-coverage':['boyd-core-report','fleet-return-account'],'peace-cayenne-context':['peace-seizure-report','cayenne-decree-commentary'],
                    'peace-and-plenty-boarding':['peace-and-plenty-report'],'hermione-mutiny':['hermione-particulars'],
                    'special-session-1797':['adams-special-session-speech','special-session-proclamation','special-session-house-answer'],
                    'blount-affair':['blount-letter','blount-knoxville-welcome','blount-committee-report']},
        'expect':(8,1587),
        'order':['sn84038410','sn83025588','sn82014782','sn83025881','sn83025525','sn84023150','sn83025527','sn84024710']},   # the pilot papers first
  # The third reviewed year (release v0.8.0, page shifts corrected in v0.8.1): 14 stories. The user agreed the proposed
  # categories on 2026-11-10 ("可以，上线 1807"); the Chesapeake affair is with the ships, as a top-level story takes one category.
  1807:{'categories':[
          ('war','War in Europe and Haiti',['lubeck-stormed','hayti-news-baltimore-february-1807','harford-jones-russian-army','bennigsen-pultusk-account','bulletin-66','bulletin-78','armistice-france-russia']),
          ('ships','Britain, France and American ships',['monroe-pinkney-treaty-letter','driver-at-charleston','chesapeake-affair-1807','douglas-and-the-mayor-of-norfolk',
                                                         'macdonald-funeral-norfolk-1807','national-intelligencer-on-the-seamen-1807','antwerp-letter-capture-order','britain-answer-peace-or-war']),
          ('government','American public life and government',['wilkinson-speech-new-orleans-1806','burr-conspiracy-1807','special-session-1807'])],
        'children':{'burr-conspiracy-1807':['burr-conspiracy-message','burr-in-arms-new-orleans','marshall-commitment-opinion','burr-treason-verdict','marshall-october-opinion'],
                    'driver-at-charleston':['kalteisen-letter-driver','driver-answer-charleston'],
                    'chesapeake-affair-1807':['chesapeake-attack-account','july-2-proclamation','berkeley-order','chesapeake-court-of-inquiry','house-report-chesapeake'],
                    'douglas-and-the-mayor-of-norfolk':['douglas-letter-3-july','mayor-answer-4-july','tazewell-report','douglas-letter-6-july'],
                    'special-session-1807':['proclamation-convening-congress','president-message-october-27']},
        'expect':(11,4162)},   # v0.10.2 dated one Kentucky Gazette issue filed under 1807 to 1805
  # The fourth reviewed year (release v0.9.0): 20 stories. Categories as proposed by the review; the owner agreed on
  # 2026-11-10 ("Follow your recommendations on the data review. And then publish all").
  1808:{'categories':[
          ('war','War and conflict',['latest-from-portugal-dec-1807','alicante-letters-1808','charles-iv-appoints-murat','sevier-letter-marble-springs-1808','order-in-council-4-july',
                                              'arcturus-news-from-spain','reding-dispatch-baylen','conventions-in-portugal']),
          ('ships','Britain, France and American ships',['decrees-on-neutral-trade','algiers-1808','papers-before-congress-march-1808','canning-on-america-24-june']),
          ('government','The embargo and American government',['embargo-laws','wilkinson-accused','president-message-25-feb-military-force','embargo-in-force-spring-1808',
                                              'adams-resigns-senate','jefferson-answers-new-hampshire','jefferson-answer-embargo-petitions','burlington-revenue-cutter-1808','wilkinson-harper-correspondence-1808','message-8-november',
                                              'foreign-relations-report-22-november'])],
        'children':{'embargo-laws':['embargo-act-22-dec-1807','embargo-supplementary-act-9-jan','embargo-additional-act-12-march','embargo-suspension-act-22-april','embargo-act-25-april'],
                    'wilkinson-accused':['wilkinson-randolph-letters','clark-statement-on-wilkinson','president-message-20-jan-wilkinson','wilkinson-court-of-inquiry'],
                    'decrees-on-neutral-trade':['orders-in-council-11-nov-1807','amsterdam-letter-milan-decree','british-instructions-11-april'],
                    'algiers-1808':['algiers-war-report','lear-circular-peace-with-algiers','dey-of-algiers-june'],
                    'papers-before-congress-march-1808':['president-message-22-march','canning-monroe-chesapeake-correspondence','rose-madison-letters','champagny-letter-15-jan'],
                    'embargo-in-force-spring-1808':['georgia-letter-mobile-pensacola','proclamation-lake-champlain','president-circular-governors-6-may'],
                    'alicante-letters-1808':['alicante-letter-aranjuez-rumour','alicante-letter-guards-ordered'],
                    'conventions-in-portugal':['russian-fleet-tagus-convention','cintra-convention'],
                    'message-8-november':['message-8-november-text','canning-to-pinkney-23-september','armstrong-letter-28-august','madison-to-erskine-25-march']},
        'expect':(10,4060)},   # v0.10.2 dated the 98 Kentucky Gazette issues filed under 1808 to 1806
  # The fifth reviewed year (releases v0.10.0 and v0.10.1): 12 stories. The owner agreed a 6-paper threshold for 1793 (fewer
  # papers survive) and the proposed categories on 2026-11-10 ("Follow your recommendations on the data review").
  1793:{'categories':[
          ('war','War and diplomacy',['emigrant-armies-disbanded','dumouriez-letter-brussels','powers-at-war-with-france-list','dumouriez-defection-1793',
                                      'tournai-bulletin-3-may','death-of-general-dampierre','convention-president-declaration-plot','news-from-cap-francais-1793','cadiz-letter-24-june',
                                      'madeira-report-battle-near-lisle','german-creek-letter-1793','war-office-treaty-commissioners-1793']),
          ('ships','Ships and the sea',['sea-serpent-captain-crabtree','treasury-circular-rules-on-neutrality']),
          ('public','American public life',['genet-appeal-to-the-people-1793'])],
        'children':{'dumouriez-defection-1793':['clairfayt-letter-tournay','sun-rumour-dumouriez-left-army','dumouriez-address-french-nation','cobourg-proclamation-5-april'],
                    'genet-appeal-to-the-people-1793':['jay-king-statement-on-genet','genet-letter-to-the-president-13-august','jefferson-answer-to-genet-16-august'],
                    'news-from-cap-francais-1793':['fanning-account-cap-francais','brig-mary-passengers-cap-francais']},
        'expect':(12,1751)},
  # The sixth reviewed year (release v0.11.0): 33 stories, the categories as the review proposed them.
  1806:{'categories':[
          ('war','War and foreign news',['vienna-opens-its-gates','lisbon-and-st-ubes-report','austerlitz-in-the-papers-1806','speech-opening-parliament-21-january',
                                         'treaty-of-pressburg','bremen-letter-austrian-officers','napoleon-speech-legislative-body-1806','st-domingo-report-may-1806',
                                         'linois-taken-1806','dodge-report-cape-francois','swedish-bulletin-lauenburg','louis-napoleon-king-of-holland',
                                         'francis-ii-gives-up-the-imperial-crown','buenos-ayres-captured-1806','hague-17-october-war-france-prussia']),
          ('ships','Britain, France and American ships',['antigua-letter-american-vessels','trade-with-st-domingo-1806','riley-journal-rochefort-squadron',
                                         'british-seizures-papers-1806','british-goods-resolutions-1806','tunisian-cruiser-message-april-1806','leander-affair-1806',
                                         'fox-note-blockade-may-1806']),
          ('government','American public life and government',['hamet-caramalli-1806','yrujo-and-the-government-1806','miranda-expedition-1806',
                                         'house-secret-journal-spain-1806','heath-declines-lieutenant-governor','detroit-letter-1-june-1806',
                                         'spanish-troops-near-the-sabine-1806','lewis-and-clark-return-1806','burr-enterprise-1806','annual-message-2-december-1806'])],
        'children':{'hamet-caramalli-1806':['message-13-january-hamet-caramalli','eaton-hamet-convention','hamet-letter-to-the-president','senate-report-hamet-caramalli'],
                    'trade-with-st-domingo-1806':['message-french-complaints-st-domingo','act-suspending-trade-with-st-domingo'],
                    'british-seizures-papers-1806':['message-17-january-1806','monroe-to-mulgrave-1805','madison-report-new-principles'],
                    'yrujo-and-the-government-1806':['yrujo-circular-to-the-foreign-ministers','madison-yrujo-letters-january-1806'],
                    'british-goods-resolutions-1806':['gregg-resolution-29-january','randolph-speech-5-march','national-intelligencer-on-the-vote-of-17-march',
                                                      'non-importation-act-18-april','message-3-december-1806'],
                    'austerlitz-in-the-papers-1806':['london-bulletin-17-december-1805','berthier-letter-to-massena','thirtieth-bulletin-grand-army','napoleon-proclamation-after-austerlitz'],
                    'miranda-expedition-1806':['serious-questions-to-mr-madison','leander-letter-from-jacmel','miranda-proclamation-28-june','miranda-defeat-report'],
                    'leander-affair-1806':['new-york-meeting-resolutions-leander','proclamation-against-the-leander'],
                    'spanish-troops-near-the-sabine-1806':['hostile-appearance-letter-2-august','freeman-party-turned-back','wilkinson-letter-red-river'],
                    'lewis-and-clark-return-1806':['lewis-arrival-announced','clark-letter-to-his-brother'],
                    'burr-enterprise-1806':['kentucky-affidavit-against-burr','proclamation-27-november-1806']},
        'expect':(12,4381)},
  # The seventh reviewed year (release v0.11.5): 20 stories, the categories as the review proposed them. The Creek
  # paragraph is green, as the government paper's report of a treaty made at Washington; the St. Thomas report is blue.
  1805:{'categories':[
          ('war','War and foreign news',['napoleon-peace-letter-and-british-answer-1805','haytian-army-before-santo-domingo-1805','folger-report-toulon-fleet-off-cadiz-1805',
                                         'calder-dispatch-23-july-1805','paris-article-on-the-austrian-armaments-31-august-1805','napoleon-speech-to-the-senate-september-1805',
                                         'collingwood-dispatch-on-trafalgar-22-october-1805']),
          ('ships','Tripoli, Algiers and American ships',['tripoli-squadron-letters-1805','cowdery-letter-from-tripoli-1805','madison-answer-to-the-charleston-insurers-10-july-1805',
                                         'peace-with-tripoli-news-1805','british-orders-on-american-vessels-with-colonial-produce-1805','algiers-insurrection-and-change-of-dey-1805',
                                         'spanish-order-on-american-vessels-at-algeziras-5-september-1805']),
          ('government','American public life and government',['chase-impeachment-trial-1805','jefferson-second-inaugural-address-1805','strong-speech-to-massachusetts-legislature-june-1805',
                                         'lewis-and-clark-news-from-fort-mandan-1805','creek-treaty-washington-paragraph-1805','president-message-3-december-1805'])],
        'children':{'tripoli-squadron-letters-1805':['obrien-letter-on-tripoli-5-september-1804','preble-letter-18-september-1804'],
                    'chase-impeachment-trial-1805':['chase-address-to-the-senate-2-january-1805','house-replication-to-chase-answer-1805','chase-answer-and-pleas-4-february-1805',
                                                    'chase-acquittal-declared-1-march-1805'],
                    'napoleon-peace-letter-and-british-answer-1805':['napoleon-letter-to-the-king-of-england-1805','mulgrave-answer-to-napoleon-letter-1805'],
                    'lewis-and-clark-news-from-fort-mandan-1805':['kentucky-account-of-the-party-of-discovery-1805','lewis-letter-to-the-president-7-april-1805'],
                    'peace-with-tripoli-news-1805':['salem-register-report-by-the-belleisle-1805','rodgers-letter-on-the-peace-with-tripoli-8-june-1805',
                                                    'hull-letter-on-the-attack-on-derne-28-april-1805','barron-letter-to-eaton-22-march-1805'],
                    'british-orders-on-american-vessels-with-colonial-produce-1805':['london-paragraph-order-to-detain-american-vessels-1805','privy-council-minute-3-august-1805'],
                    'algiers-insurrection-and-change-of-dey-1805':['shillaber-report-from-algiers-1805','mountford-letter-from-algiers-9-september-1805']},
        'expect':(14,3811)},
  # The eighth reviewed year (release v0.11.6): 36 stories, the categories as the review proposed them. The Toulon report
  # is orange (news of ships), the Spanish envoy Onis green (like Yrujo in 1806) and the message of 17 January orange
  # (mostly Canning's and Pinkney's letters).
  1809:{'categories':[
          ('war','War and foreign news',['havana-letter-news-from-spain-january-1809','cadiz-report-battle-near-valladolid','french-bulletin-on-corunna-thirtieth-bulletin',
                                         'french-account-of-saragossa-from-the-moniteur','british-expedition-to-macao-admiral-drury','austria-goes-to-war-april-1809',
                                         'first-austrian-bulletin-sacile-17-april','aspern-essling-two-bulletins-1809','buenos-ayres-liniers-1809','french-twenty-fifth-bulletin-wagram',
                                         'castlereagh-note-on-talavera','scheldt-expedition-chatham-dispatches','treaty-of-vienna-14-october-1809']),
          ('ships','Britain, France and American ships',['message-17-january-1809-canning-pinkney-letters','arrangement-with-british-minister-april-1809',
                                         'france-lifts-embargo-on-american-vessels-1809','order-in-council-26-april-1809-and-papers','erskine-arrangement-disavowed-1809',
                                         'new-york-report-capture-of-the-toulon-fleet','proclamation-of-9-august-and-treasury-circular','russian-decree-on-neutral-vessels-1809',
                                         'jackson-dismissed-november-1809','champagny-to-armstrong-altenburg-22-august','documents-with-the-message-of-29-november']),
          ('government','American public life and government',['embargo-and-non-intercourse-laws-1809','massachusetts-senate-report-on-enforcing-act',
                                         'madison-inaugural-address-4-march-1809','john-adams-letter-against-division-of-the-union','war-department-circular-militia-29-april-1809',
                                         'president-message-23-may-1809','new-orleans-account-camp-terre-aux-boeufs','spanish-envoy-onis-1809','nashville-clarion-death-of-governor-lewis',
                                         'presidents-message-29-november-1809','senate-resolution-on-jacksons-letters','treasury-report-7-december-1809'])],
        'children':{'austria-goes-to-war-april-1809':['emperor-francis-proclamation-april-1809','austrian-address-to-the-german-nation-1809'],
                    'aspern-essling-two-bulletins-1809':['french-tenth-bulletin-ebersdorf-23-may','austrian-bulletin-breitenlee-23-may'],
                    'buenos-ayres-liniers-1809':['london-report-liniers-defeated-at-buenos-ayres','rio-janeiro-letter-new-viceroy-at-buenos-ayres'],
                    'scheldt-expedition-chatham-dispatches':['chatham-dispatch-surrender-of-flushing','chatham-dispatch-29-august-operations-closed'],
                    'arrangement-with-british-minister-april-1809':['national-intelligencer-on-erskine-arrangement-19-april','erskine-smith-correspondence-17-19-april-1809',
                                                                    'proclamation-19-april-1809','secretary-of-state-answer-to-fitzsimons-april-1809'],
                    'france-lifts-embargo-on-american-vessels-1809':['imperial-decree-25-february-1809','armstrong-letter-23-february-1809'],
                    'order-in-council-26-april-1809-and-papers':['british-order-in-council-26-april-1809','board-of-trade-explanation-of-order-26-april',
                                                                 'message-june-1809-pinkney-canning-papers','erskine-note-june-1809-on-order-26-april'],
                    'erskine-arrangement-disavowed-1809':['canning-in-the-commons-on-erskines-agreement','order-in-council-24-may-1809','canning-instructions-to-erskine-23-january',
                                                          'intelligencer-on-erskines-explanation-16-august'],
                    'proclamation-of-9-august-and-treasury-circular':['presidents-proclamation-9-august-1809','treasury-circular-9-august-1809'],
                    'jackson-dismissed-november-1809':['intelligencer-statement-13-november-on-jackson','intelligencer-article-15-november-negotiation-suspended',
                                                       'jacksons-circular-13-november-1809'],
                    'documents-with-the-message-of-29-november':['documents-erskines-explanations-july-august','documents-smith-and-jackson-october-november',
                                                                 'documents-smith-to-pinkney-23-november','documents-armstrong-and-champagny'],
                    'embargo-and-non-intercourse-laws-1809':['enforcing-act-9-january-1809','non-intercourse-act-1-march-1809','treasury-circular-3-march-1809',
                                                             'non-intercourse-amending-act-28-june-1809'],
                    'spanish-envoy-onis-1809':['new-york-report-onis-arrives-in-the-cornelia','new-york-report-onis-not-received']},
        'expect':(13,4172)},
  # The ninth reviewed year (release v0.11.9): 16 stories by the standard rule, the categories as the review proposed them.
  1800:{'categories':[
          ('war','War and foreign news',['convention-of-alkmaar-october-1799', 'bonaparte-letter-to-the-king-and-grenville-answer', 'siege-and-evacuation-of-genoa-1800', 'ratisbon-report-vienna-answer-to-first-consul', 'constantinople-letter-28-july-1800-kleber-murdered', 'london-report-floods-in-china-1800', 'convention-prolonging-the-armistice-in-germany-1800', 'king-george-speech-11-november-1800']),
          ('ships','Ships, trade and the peace with France',['spanish-order-against-trade-with-gibraltar-1800', 'paris-6-august-1800-conferences-with-american-envoys', 'whitworth-convention-with-denmark-1800', 'salem-report-ship-brutus-from-algiers-december-1800', 'convention-between-france-and-the-united-states-1800']),
          ('government','American public life and government',['congress-honours-washington-1799-1800', 'congress-and-the-27th-article-february-1800', 'congress-meets-in-washington-november-1800'])],
        'children':{'congress-honours-washington-1799-1800':['joint-resolutions-23-december-1799-on-washington', 'president-message-8-january-1800-mrs-washington-letter'],
                    'congress-and-the-27th-article-february-1800':['livingston-resolutions-3-february-1800', 'president-message-7-february-1800-papers-on-the-27th-article'],
                    'siege-and-evacuation-of-genoa-1800':['melas-summons-to-massena-genoa', 'massena-report-evacuation-of-genoa-7-june-1800'],
                    'congress-meets-in-washington-november-1800':['president-speech-22-november-1800', 'senate-address-25-november-1800', 'president-reply-to-the-senate-november-1800', 'house-address-november-1800', 'president-reply-to-the-house-november-1800']},
        'expect':(14, 2575)},
  # The tenth reviewed year (release v0.11.10): 20 stories by the standard rule, the categories as the review proposed them.
  1804:{'categories':[
          ('war','War and foreign news',['haitian-proclamation-of-independence-29-november-1803', 'frigate-philadelphia-lost-and-burned-1804', 'preble-letter-from-malta-17-january-1804', 'general-moreau-in-the-papers-1804', 'new-york-report-massacre-at-cape-francois-june-1804', 'london-report-pitt-returns-to-office-may-1804', 'preble-letter-off-tripoli-14-june-1804']),
          ('west','Louisiana, Spain and the West',['louisiana-taken-into-possession-december-1803', 'osage-chiefs-visit-the-president-1804', 'west-florida-rising-august-1804', 'spanish-minister-yrujo-and-w-jackson-1804', 'ursuline-nuns-memorial-and-the-presidents-answer-1804', 'house-motion-on-drawbacks-at-new-orleans-12-november-1804', 'documents-on-spain-and-louisiana-sent-to-congress-november-1804']),
          ('government','American public life and government',['norfolk-report-of-the-fire-of-22-february-1804', 'impeachment-of-judge-chase-1804', 'death-of-general-hamilton-1804', 'wythe-court-house-letter-the-clinch-mountain-sunk', 'notice-that-the-amendment-on-electing-the-president-is-ratified-1804', 'presidents-message-8-november-1804'])],
        'children':{'louisiana-taken-into-possession-december-1803':['wilkinson-orders-before-new-orleans-17-december-1803', 'claiborne-proclamation-at-new-orleans-20-december-1803'],
                    'frigate-philadelphia-lost-and-burned-1804':['bainbridge-letter-with-the-presidents-message-march-1804', 'preble-letter-to-the-consul-at-gibraltar-on-the-philadelphia', 'decatur-letter-to-preble-17-february-1804', 'decatur-made-captain-official-notice-may-1804'],
                    'impeachment-of-judge-chase-1804':['chase-articles-reported-26-march-1804', 'chase-memorial-on-the-impeachment-april-1804', 'chase-articles-reported-30-november-1804'],
                    'general-moreau-in-the-papers-1804':['letter-attributed-to-moreau-nouvelles-a-la-main-march-1804', 'nouvelles-a-la-main-no-3-letters-of-madame-bonaparte-and-madame-moreau', 'moniteur-announces-moreau-banished-to-america'],
                    'osage-chiefs-visit-the-president-1804':['lexington-report-osage-chiefs-on-their-way-to-washington', 'presidents-address-to-the-osage-chiefs-1804'],
                    'death-of-general-hamilton-1804':['bishop-moore-letter-on-general-hamilton', 'gouverneur-morris-funeral-oration-over-general-hamilton', 'hamilton-burr-correspondence-published-july-1804', 'general-hamilton-will-july-1804', 'general-hamilton-statement-on-the-expected-interview', 'coroners-jury-verdict-on-general-hamilton-august-1804'],
                    'west-florida-rising-august-1804':['natchez-letter-of-7-august-armed-men-near-bayou-sara', 'natchez-report-of-14-august-a-party-marches-on-baton-rouge'],
                    'spanish-minister-yrujo-and-w-jackson-1804':['w-jackson-statement-in-the-political-register-september-1804', 'yrujo-letter-to-the-secretary-of-state-october-1804']},
        'expect':(14,3472)},
  # The eleventh reviewed year (release v0.11.11): 14 stories by the standard rule, the categories as the review proposed them.
  1802:{'categories':[
          ('foreign','Europe and St. Domingo',['baltimore-report-of-the-death-of-toussaint-january-1802', 'french-army-arrives-at-st-domingo-february-1802', 'treaty-of-madrid-21-march-1801-printed-1802', 'definitive-treaty-of-amiens-1802', 'leclerc-proclamation-on-the-arrest-of-toussaint-june-1802', 'french-senate-proclaims-bonaparte-consul-for-life-august-1802']),
          ('ships','Ships, trade and the Barbary states',['havana-circular-ports-of-cuba-closed-december-1801', 'new-york-report-algerine-cruisers-take-a-portuguese-frigate-1802', 'washington-report-letters-from-algiers-of-7-july-1802', 'madrid-letter-convention-with-spain-on-claims-august-1802']),
          ('government','American public life and government',['breckenridge-speech-on-repealing-the-judiciary-act-january-1802', 'act-fixing-the-military-peace-establishment-1802', 'paine-returns-to-america-1802', 'new-york-report-fire-of-2-november-1802'])],
        'children':{'french-army-arrives-at-st-domingo-february-1802':['consuls-proclamation-to-the-inhabitants-of-st-domingo-november-1801', 'baltimore-report-conflagration-of-the-cape-march-1802'],
                    'paine-returns-to-america-1802':['jefferson-letter-to-paine-published-august-1802', 'paine-letter-the-first-to-the-citizens-november-1802', 'paine-letter-the-second-to-the-citizens-november-1802']},
        'expect':(14, 2968)},
  # The twelfth reviewed year (release v0.11.12): 23 stories by the standard rule, the categories as the review proposed them.
  1803:{'categories':[
          ('war','War and foreign news',['despard-speech-on-the-scaffold-21-february-1803', 'gascoigne-letter-war-expected-march-1803', 'french-note-to-the-british-ambassador-13-may-1803', 'convention-of-suhlingen-for-hanover-june-1803', 'king-message-on-the-batavian-republic-1803', 'london-report-american-claims-paid-july-1803', 'dublin-letter-of-24-july-1803-on-the-rising', 'havre-letters-on-the-invasion-flotilla-august-1803', 'president-message-on-morocco-november-1803', 'calamity-at-madeira-9-october-1803']),
          ('west','Louisiana, Spain and the West',['deposit-at-new-orleans-before-congress-1802-1803', 'spanish-and-french-ministers-on-the-deposit-1803', 'laussat-proclamation-to-the-louisianians-1803', 'louisiana-expedition-suspended-rotterdam-april-1803', 'monroe-received-at-paris-april-1803', 'national-intelligencer-on-the-treaty-of-cession-july-1803', 'fifteen-millions-the-price-of-louisiana-1803', 'treaty-and-conventions-for-the-cession-of-louisiana-1803']),
          ('government','American public life and government',['samuel-adams-and-thomas-paine-letters-1802-1803', 'proclamation-convening-congress-16-july-1803', 'president-message-17-october-1803', 'treasury-report-25-october-1803', 'gold-ore-found-in-cabarrus-county-december-1803'])],
        'children':{'deposit-at-new-orleans-before-congress-1802-1803':['president-message-22-december-1802-on-the-deposit-at-new-orleans', 'house-resolution-7-january-1803-on-the-mississippi', 'senate-resolutions-for-80000-militia-february-1803'],
                    'spanish-and-french-ministers-on-the-deposit-1803':['yrujo-letter-to-the-secretary-of-state-10-march-1803', 'pichon-letter-to-the-governor-of-louisiana-11-march-1803', 'yrujo-letter-on-the-deposit-restored-19-april-1803'],
                    'treaty-and-conventions-for-the-cession-of-louisiana-1803':['louisiana-treaty-of-cession-30-april-1803', 'convention-for-sixty-million-francs-30-april-1803', 'convention-on-debts-due-to-american-citizens-30-april-1803']},
        'expect':(17, 3250)},
  # The thirteenth reviewed year (release v0.11.14): 20 stories by the standard rule, the categories as the review proposed them.
  1810:{'categories':[
          ('war','War and foreign news',['burdett-address-to-the-people-of-england-1810', 'caracas-address-of-the-supreme-junta-1810', 'west-florida-september-december-1810', 'tunis-bey-and-american-consul-malta-august-1810', 'lucien-bonaparte-address-to-the-roman-citizens-1810']),
          ('ships','Britain, France and American ships',['leib-resolutions-on-the-erskine-arrangement-march-1810', 'cadore-note-to-armstrong-14-february-1810', 'act-concerning-commercial-intercourse-1-may-1810', 'correspondence-on-jacksons-recall-published-may-1810', 'despatches-received-by-the-john-adams-june-1810', 'rambouillet-decree-23-march-1810', 'vixen-fired-on-by-the-moselle-june-1810', 'brig-two-marias-seized-at-malaga-1810', 'cadore-letter-to-armstrong-5-august-1810', 'pinkney-letter-with-wellesley-answer-on-the-decrees-1810', 'president-proclamation-of-2-november-1810-and-treasury-circular']),
          ('government','American public life and government',['president-message-on-the-militia-3-january-1810', 'gallatin-statement-on-erskine-despatch-1810', 'president-annual-message-5-december-1810', 'treasury-report-december-1810'])],
        'children':{'correspondence-on-jacksons-recall-published-may-1810':['pinkney-note-to-wellesley-2-january-1810', 'wellesley-answer-to-pinkney-14-march-1810'],
                    'despatches-received-by-the-john-adams-june-1810':['armstrong-despatch-of-10-march-1810-with-letter-to-cadore', 'armstrong-letter-of-7-april-1810'],
                    'west-florida-september-december-1810':['baton-rouge-fort-taken-natchez-report-september-1810', 'west-florida-declaration-26-september-1810', 'letter-from-washington-mississippi-territory-30-october-1810', 'president-proclamation-on-west-florida-27-october-1810'],
                    'president-proclamation-of-2-november-1810-and-treasury-circular':['president-proclamation-2-november-1810', 'treasury-circular-2-november-1810']},
        'expect':(11, 3933)},
  # The fourteenth reviewed year (release v0.11.15): 15 stories by the standard rule, the categories as the review proposed them;
  # two sub-stories in 6 papers give the other side of two admitted documents, at the owner's word (X-1801-08).
  1801:{'categories':[
          ('war','War and peace in Europe',['augereau-notice-ending-the-armistice-november-1800', 'moreau-report-of-hohenlinden-december-1800', 'nelson-letter-on-the-battle-of-copenhagen-april-1801', 'london-account-second-attack-on-boulogne-august-1801', 'london-surrender-of-cairo-confirmed-august-1801', 'preliminary-articles-of-peace-britain-and-france-october-1801']),
          ('sea','Ships, the navy and Tripoli',['bashaw-of-tripoli-war-on-the-united-states-1801', 'baxter-journal-from-cadiz-august-1801', 'court-martial-on-captain-little-september-1801']),
          ('government','American public life and government',['jefferson-letter-of-4-september-1800', 'jefferson-elected-and-inaugurated-february-march-1801', 'new-haven-remonstrance-and-the-president-reply-july-1801', 'treaty-with-the-cherokees-at-south-west-point-1801', 'census-of-1800-total-population-september-1801', 'john-appleton-brings-the-ratified-convention-october-1801'])],
        'children':{'jefferson-elected-and-inaugurated-february-march-1801':['house-committee-notifies-jefferson-february-1801', 'jefferson-farewell-to-the-senate-28-february-1801', 'jefferson-inaugural-address-4-march-1801'],
                    'bashaw-of-tripoli-war-on-the-united-states-1801':['cathcart-circular-of-3-january-1801', 'cathcart-circular-of-15-may-1801-war-declared', 'dale-letter-enterprize-takes-a-tripoline-cruiser-august-1801', 'president-letter-to-lieutenant-sterett-1-december-1801'],
                    'new-haven-remonstrance-and-the-president-reply-july-1801':['new-haven-merchants-remonstrance-1801', 'president-reply-to-the-new-haven-remonstrance-july-1801'],
                    'treaty-with-the-cherokees-at-south-west-point-1801':['nashville-general-wilkinson-and-the-cherokee-treaty-august-1801', 'knoxville-report-cherokee-treaty-broken-up-september-1801']},
        'expect':(14, 2372)},
  # A thin year (release v0.11.16): 3 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1770:{'categories':[
          ('trade','Trade and the colonies',['boston-merchants-vote-to-alter-non-importation-october-1770']),
          ('government','Colonial government',['williamsburg-report-death-of-lord-botetourt-october-1770', 'letter-from-london-6-september-1770-hutchinson-governor'])],
        'children':{},
        'expect':(4, 448)},
  # A thin year (release v0.11.17): 11 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1772:{'categories':[
          ('colonies','London and the colonies',['london-report-the-king-in-council-on-the-duke-of-cumberland-1771', 'london-report-proclamation-for-emigrants-to-america-1772', 'st-james-receiver-general-of-virginia-1772', 'boston-report-bernard-expected-governor-of-barbados-1772', 'boston-report-dudingston-promoted-captain-1772', 'london-report-dartmouth-lenient-measures-1772', 'london-war-office-orders-for-officers-in-america-1772']),
          ('frontier','The frontier',['philadelphia-report-of-11-november-1772-on-the-frontier']),
          ('abroad','The islands and Europe',['new-york-report-captain-prince-fire-at-grenada-1772', 'christiansted-report-hurricane-september-1772', 'hamburg-letter-on-the-revolution-in-sweden-1772'])],
        'children':{'philadelphia-report-of-11-november-1772-on-the-frontier':['philadelphia-report-seneca-chief-from-johnson-hall-1772', 'philadelphia-report-forts-chartres-and-pitt-1772', 'philadelphia-report-frontier-petition-1772']},
        'expect':(6, 675)},
  # A thin year (release v0.11.18): 25 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1774:{'categories':[
          ('crown','The Crown, Parliament and the governor',['kings-speech-to-parliament-13-january-1774', 'privy-council-hearing-on-the-massachusetts-petition-january-1774', 'boston-port-act-1774', 'bills-for-massachusetts-bay-printed-june-1774', 'gage-proclamation-against-illegal-combinations-june-1774', 'gage-proclamation-for-piety-and-virtue-july-1774', 'gage-and-the-selectmen-of-boston-on-town-meetings-august-1774', 'sketch-of-a-popular-noblemans-speech-on-american-affairs-1774', 'quebec-act-1774', 'general-brattle-letter-to-governor-gage-august-1774', 'gage-letter-to-peyton-randolph-20-october-1774', 'kings-proclamation-dissolving-parliament-1-october-1774', 'scarborough-man-of-war-express-to-england-autumn-1774']),
          ('colonies','The colonies: meetings, assemblies and the Congress',['philadelphia-resolutions-on-the-tea-ship-polly-december-1773', 'boston-the-judges-salaries-february-1774', 'franklin-declaration-on-the-hutchinson-letters-1773', 'virginia-burgesses-resolution-for-a-fast-on-1-june-1774', 'suffolk-resolves-september-1774', 'continental-congress-at-philadelphia-september-october-1774', 'members-chosen-for-the-general-court-meet-at-salem-october-1774', 'provincial-congress-at-cambridge-1-december-1774']),
          ('world','Europe and the world',['lord-viscount-pitt-to-tour-the-colonies-january-1774', 'letter-from-the-lower-elbe-on-the-insurrection-in-russia-1774', 'gentleman-in-england-on-the-warlike-preparations-of-the-french-1774', 'peace-between-russia-and-the-porte-vienna-august-1774'])],
        'children':{'bills-for-massachusetts-bay-printed-june-1774':['bill-for-regulating-the-government-of-massachusetts-bay-1774', 'bill-for-the-impartial-administration-of-justice-massachusetts-bay-1774'],
                    'continental-congress-at-philadelphia-september-october-1774':['continental-congress-resolution-of-22-september-1774', 'continental-congress-resolves-of-8-october-1774', 'continental-congress-declaration-and-resolves-14-october-1774', 'continental-association-1774'],
                    'scarborough-man-of-war-express-to-england-autumn-1774':['portsmouth-letter-on-the-scarborough-4-october-1774', 'scarborough-returns-to-boston-december-1774']},
        'expect':(8, 1205)},
  # A thin year (release v0.11.19): 24 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1775:{'categories':[
          ('crown','The Crown, Parliament and London',['opening-of-parliament-november-december-1774', 'london-member-asks-the-lord-mayor-about-the-kings-speech-1774', 'london-ministers-said-to-be-offended-with-general-gage-1774', 'london-transports-for-ireland-howe-and-draper-1774', 'lord-north-on-the-merchants-meetings-january-1775', 'livery-of-london-address-and-the-kings-answer-april-1775', 'west-indies-report-of-the-parliament-house-pulled-down-1775', 'city-of-london-address-and-petition-july-1775', 'kings-proclamation-for-suppressing-rebellion-and-sedition-1775']),
          ('colonies','The colonies and the Congress',['continental-congress-petition-to-the-king-printed-1775', 'massachusetts-provincial-congress-resolves-february-1775', 'new-york-assembly-mr-thomas-motion-23-february-1775', 'addresses-to-generals-washington-and-lee-june-july-1775', 'continental-congress-july-1775']),
          ('war','The war in America',['admiral-parry-ordered-to-boston-march-1775', 'provincial-congress-on-the-commencement-of-hostilities-april-1775', 'ticonderoga-taken-report-of-john-brown-may-1775', 'providence-letter-on-the-contest-of-17-june-1775', 'burgoyne-and-lee-letters-june-july-1775', 'philadelphia-letter-of-29-july-on-a-london-letter-of-31-may-1775', 'letter-on-a-skirmish-near-st-johns-september-1775', 'washington-address-to-the-inhabitants-of-canada-1775', 'captain-mowat-and-the-burning-of-falmouth-october-1775', 'halifax-report-of-the-newfoundland-storm-1775'])],
        'children':{'opening-of-parliament-november-december-1774':['kings-speech-to-parliament-30-november-1774', 'house-of-lords-protest-against-the-address-december-1774', 'house-of-commons-address-of-thanks-december-1774'],
                    'continental-congress-petition-to-the-king-printed-1775':['continental-congress-petition-to-the-king-october-1774', 'colony-agents-letter-on-the-congress-petition-24-december-1774'],
                    'provincial-congress-on-the-commencement-of-hostilities-april-1775':['provincial-congress-depositions-on-the-commencement-of-hostilities-1775', 'deposition-of-lieutenant-gould-april-1775'],
                    'livery-of-london-address-and-the-kings-answer-april-1775':['livery-of-london-address-remonstrance-and-petition-april-1775', 'kings-answer-to-the-livery-of-london-april-1775'],
                    'addresses-to-generals-washington-and-lee-june-july-1775':['new-york-provincial-congress-address-to-washington-june-1775', 'massachusetts-provincial-congress-address-to-washington-july-1775', 'washington-answer-to-the-massachusetts-provincial-congress-july-1775', 'massachusetts-provincial-congress-address-to-general-lee-july-1775'],
                    'continental-congress-july-1775':['continental-congress-resolve-on-the-restraining-acts-4-july-1775', 'declaration-of-the-causes-and-necessity-of-taking-up-arms-1775', 'continental-congress-second-petition-to-the-king-8-july-1775'],
                    'burgoyne-and-lee-letters-june-july-1775':['burgoyne-letter-to-lee-july-1775', 'lee-answer-to-burgoyne-11-july-1775'],
                    'city-of-london-address-and-petition-july-1775':['common-council-of-london-address-and-petition-july-1775', 'kings-answer-to-the-common-council-of-london-1775']},
        'expect':(7, 1286)},
  # A thin year (release v0.11.20): 26 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1777:{'categories':[
          ('war','War and the armies',['new-london-report-hessian-troops-recalled-january-1777', 'philadelphia-report-accomack-militia-march-to-salisbury-february-1777', 'pittsburgh-letter-of-24-march-1777-indians-assembled', 'washington-and-the-british-commanders-on-the-exchange-of-prisoners-1777', 'lewistown-letter-ship-morris-run-ashore-and-blown-up-april-1777', 'boston-report-privateer-takes-six-prizes-for-the-british-army-may-1777', 'washington-letters-to-congress-on-the-british-movements-in-new-jersey-june-1777', 'evacuation-of-ticonderoga-july-august-1777', 'washington-letter-to-howe-16-july-1777-prescott-for-lee', 'moses-creek-letter-26-july-1777-a-brush-with-the-enemy-at-fort-edward', 'burgoyne-proclamation-1777', 'washington-letters-of-11-september-1777-brandywine', 'convention-of-saratoga-october-1777', 'washington-proclamation-pardon-to-deserters-who-return-1777']),
          ('britain','Britain, France and Europe',['king-speech-opening-parliament-31-october-1776', 'king-proclamation-for-a-general-fast-and-burke-remarks-1776', 'charleston-report-brigantine-notre-dame-from-france-february-1777', 'baltimore-report-of-a-french-fleet-at-charleston-march-1777', 'london-paragraph-preparations-for-a-decisive-campaign-february-1777', 'franklin-and-deane-to-lord-stormont-2-april-1777-and-his-reply', 'close-of-the-session-of-parliament-6-june-1777']),
          ('government','Congress and American government',['american-crisis-number-one-1777', 'washington-proclamation-on-british-protections-25-january-1777', 'congress-orders-monuments-to-warren-and-mercer-april-1777', 'congress-thanks-to-meigs-and-barton-25-july-1777', 'congress-resolution-on-loan-office-interest-in-bills-on-paris-10-september-1777'])],
        'children':{'king-proclamation-for-a-general-fast-and-burke-remarks-1776':['king-proclamation-for-a-general-fast-1776', 'burke-remarks-on-the-proclamation-for-a-fast-1776'],
                    'washington-and-the-british-commanders-on-the-exchange-of-prisoners-1777':['cornwallis-letter-to-washington-3-april-1777-walcott-demand', 'washington-letter-to-howe-9-april-1777-on-the-exchange-of-prisoners', 'howe-letter-to-washington-21-april-1777-on-the-exchange-of-prisoners', 'washington-letter-to-howe-10-june-1777-final-determination-on-prisoners'],
                    'washington-letters-to-congress-on-the-british-movements-in-new-jersey-june-1777':['washington-letter-to-congress-25-june-1777-the-enemy-retreat-to-amboy', 'washington-letter-to-congress-28-june-1777-howe-advances-from-amboy'],
                    'evacuation-of-ticonderoga-july-august-1777':['council-of-general-officers-at-ticonderoga-5-july-1777', 'st-clair-letter-to-congress-14-july-1777-on-the-evacuation', 'congress-inquiry-into-the-evacuation-of-ticonderoga-29-july-1777'],
                    'close-of-the-session-of-parliament-6-june-1777':['speaker-of-the-commons-address-to-the-king-6-june-1777', 'king-speech-closing-parliament-6-june-1777'],
                    'washington-letters-of-11-september-1777-brandywine':['washington-letter-chadds-ford-11-september-1777-five-in-the-afternoon', 'washington-letter-chester-11-september-1777-midnight'],
                    'convention-of-saratoga-october-1777':['articles-of-convention-between-burgoyne-and-gates-october-1777', 'burgoyne-letter-to-howe-after-the-convention-october-1777']},
        'expect':(11, 1320)},
  # A thin year (release v0.11.21): 26 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1778:{'categories':[
          ('war','The war in America',['civil-usage-owners-present-a-coach-to-john-hancock-january-1778', 'congress-on-provisions-for-prisoners-19-december-1777', 'washington-address-to-the-inhabitants-on-cattle-for-the-army-february-1778', 'congress-on-the-exchange-of-prisoners-26-february-1778', 'shreve-party-at-billingsport-april-1778', 'washington-to-congress-24-may-1778-barren-hill', 'british-army-completes-the-evacuation-of-philadelphia-june-1778', 'the-battle-of-monmouth-june-july-1778', 'british-landing-at-bedford-september-1778', 'privateer-general-hancock-and-the-levant-frigate-september-1778', 'colonel-clark-takes-fort-chartres-and-the-western-posts-1778', 'count-pulaski-to-the-president-of-congress-16-october-1778', 'admiral-byron-fleet-in-the-storm-november-1778']),
          ('britain',"Britain's peace offers, Parliament and Congress",['house-of-lords-debate-on-the-address-20-november-1777', 'lord-norths-conciliatory-bills-and-congress-april-1778', 'governor-livingston-message-to-the-new-jersey-assembly-may-1778', 'congress-on-lord-howe-and-general-clinton-letters-6-june-1778', 'kings-speech-to-parliament-3-june-1778', 'the-commissioner-johnstone-and-congress-august-september-1778', 'the-troops-of-the-convention-of-saratoga-august-september-1778', 'the-commissioners-manifesto-and-the-congress-manifesto-october-1778']),
          ('france','France, the alliance and Europe',['simeon-deane-arrives-at-congress-with-the-treaties-with-france-may-1778', 'kings-message-on-the-french-declaration-17-march-1778', 'count-destaing-offer-of-protection-to-american-armaments-july-1778', 'congress-receives-the-french-minister-gerard-6-august-1778', 'letter-from-the-hague-on-american-proposals-for-a-treaty-june-1778'])],
        'children':{'lord-norths-conciliatory-bills-and-congress-april-1778':['draught-of-a-bill-declaring-the-intentions-of-parliament-on-taxation-1778', 'draught-of-a-bill-to-appoint-commissioners-1778', 'congress-report-on-the-draught-bills-22-april-1778'],
                    'the-battle-of-monmouth-june-july-1778':['washington-to-congress-1-july-1778-on-the-battle-of-monmouth', 'congress-thanks-to-washington-and-the-army-7-july-1778'],
                    'the-commissioner-johnstone-and-congress-august-september-1778':['congress-declaration-on-george-johnstone-11-august-1778', 'commissioners-declaration-of-26-august-1778', 'george-johnstone-declaration-of-26-august-1778'],
                    'the-troops-of-the-convention-of-saratoga-august-september-1778':['commissioners-requisition-on-the-troops-of-the-convention-26-august-1778', 'congress-on-the-troops-of-the-convention-of-saratoga-4-september-1778'],
                    'the-commissioners-manifesto-and-the-congress-manifesto-october-1778':['commissioners-manifesto-and-proclamation-3-october-1778', 'congress-manifesto-30-october-1778']},
        'expect':(11, 970)},
  # A thin year (release v0.11.22): 27 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1779:{'categories':[
          ('war','The war in America',['fuser-summons-to-the-fort-at-sunbury-and-the-answer-november-1778', 'putnam-letter-on-the-incursion-to-horseneck-march-1779', 'washington-proclamation-pardoning-deserters-10-march-1779', 'charlestown-report-campbell-retreat-from-augusta-march-1779', 'livingston-answer-to-clinton-15-april-1779', 'thomson-mason-letter-enemy-in-hampton-road-may-1779', 'philadelphia-last-advices-from-south-carolina-may-1779', 'fishkill-british-vessels-in-the-north-river-june-1779', 'collier-and-tryon-address-to-the-inhabitants-of-connecticut-july-1779', 'officer-of-rank-letter-on-the-attack-at-stono-ferry-june-1779', 'stony-point-taken-july-1779', 'lovell-letter-from-majorbagaduce-28-july-1779', 'charlestown-report-militia-turn-out-volunteers-september-1779', 'officer-in-sullivan-army-letter-9-september-1779', 'gates-letter-rhode-island-evacuated-27-october-1779', 'lincoln-letter-on-the-siege-of-savannah-22-october-1779']),
          ('abroad','Britain, Spain and the war at sea',['king-speech-opening-parliament-26-november-1778', 'basseterre-report-byron-and-estaing-off-grenada-july-1779', 'spanish-manifesto-delivered-by-almodovar-june-1779', 'continental-frigates-with-jamaica-prizes-august-1779', 'king-proclamation-on-the-threatened-invasion-july-1779']),
          ('congress','Congress, the currency and public life',['congress-and-the-paper-money-january-1779', 'philadelphia-general-meeting-on-prices-may-1779', 'congress-address-to-the-inhabitants-26-may-1779', 'congress-appoints-jay-minister-to-spain-september-1779', 'congress-audience-of-the-french-minister-17-november-1779', 'congress-resolutions-on-prices-19-november-1779'])],
        'children':{'congress-and-the-paper-money-january-1779':['congress-resolutions-of-2-january-1779-on-the-bills-of-credit', 'congress-address-of-13-january-1779-on-the-paper-money'],
                    'stony-point-taken-july-1779':['washington-letter-of-16-july-1779-with-wayne-note', 'washington-letter-of-21-july-1779-with-wayne-report', 'congress-thanks-for-stony-point-26-july-1779']},
        'expect':(9, 1660)},
  # A thin year (release v0.11.23): 23 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1780:{'categories':[
          ('war','War and the armies',['washington-letter-to-congress-18-january-1780-staten-island', 'the-serapis-and-paul-jones-letters-of-the-two-commanders-1779', 'papers-of-the-capitulation-of-charlestown-may-1780', 'boston-june-1780-brig-from-cork-taken-by-the-hermione', 'letter-from-near-morristown-9-june-1780-the-enemy-at-elizabethtown', 'the-french-fleet-and-army-for-america-1780', 'washington-letter-to-congress-26-july-1780-bergen-neck', 'gates-letter-to-congress-20-august-1780-the-defeat-near-camden', 'general-arnold-september-november-1780', 'jefferson-letter-to-congress-15-october-1780-with-dispatches-from-the-south', 'philadelphia-31-october-1780-the-privateer-holker-returns-with-prizes', 'philadelphia-14-november-1780-the-enemy-force-in-virginia']),
          ('britain','Britain, Europe and the West Indies',['king-speech-opening-parliament-25-november-1779', 'limerick-rejoicing-at-lord-north-order-december-1779', 'britain-and-the-states-general-1780', 'declaration-of-the-empress-of-russia-on-neutral-commerce-1780', 'london-8-june-1780-the-riots', 'london-october-1780-the-warrant-committing-henry-laurens-to-the-tower', 'barbados-28-october-1780-the-hurricane']),
          ('government','Congress and American government',['congress-and-the-currency-march-1780', 'jonathan-williams-letter-to-merchants-who-remit-bills-of-exchange-nantes-8-february-1780', 'the-crisis-number-ix-1780', 'congress-resolutions-on-the-memorial-of-the-general-officers-august-1780'])],
        'children':{'the-serapis-and-paul-jones-letters-of-the-two-commanders-1779':['paul-jones-letter-off-the-texel-3-october-1779', 'pearson-letter-on-the-action-with-paul-jones-6-october-1779'],
                    'congress-and-the-currency-march-1780':['congress-recommends-the-states-revise-their-tender-laws-20-march-1780', 'congress-resolutions-on-the-currency-18-march-1780'],
                    'britain-and-the-states-general-1780':['hague-23-march-1780-sir-joseph-yorke-memorial-to-the-states-general', 'order-in-council-on-the-states-general-17-april-1780'],
                    'the-french-fleet-and-army-for-america-1780':['boston-29-june-1780-the-french-fleet-sailed-from-brest', 'washington-general-orders-20-july-1780-on-the-arrival-of-the-french'],
                    'general-arnold-september-november-1780':['arnold-letter-to-washington-on-board-the-vulture-25-september-1780', 'congress-4-october-1780-arnold-name-erased-and-3-november-the-captors-of-andre']},
        'expect':(7, 1406)},
  # A thin year (release v0.11.24): 25 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1781:{'categories':[
          ('war','The war in America',['richmond-report-of-a-repulse-of-tarletons-legion-december-1780', 'morgan-to-greene-on-the-action-at-the-cowpens-january-1781', 'philadelphia-intelligence-from-the-southward-3-march-1781', 'account-of-the-action-off-the-chesapeake-16-march-1781', 'greene-to-congress-iron-works-10-march-1781', 'cornwallis-proclamation-after-the-action-of-15-march-1781', 'de-barras-arrives-at-boston-may-1781', 'letter-from-newcastle-virginia-28-may-1781', 'lafayette-to-greene-27-june-1781', 'militia-officer-letter-from-new-london-7-september-1781', 'albany-letter-on-a-scout-from-fort-plain-september-1781', 'new-york-account-of-the-engagement-off-the-chesapeake-5-september-1781', 'greene-proclamation-after-the-execution-of-colonel-hayne-1781', 'de-grasse-to-de-la-luzerne-13-september-1781', 'greene-to-congress-martins-tavern-11-september-1781', 'the-surrender-at-york-october-december-1781', 'fishkill-report-of-an-enemy-party-under-major-ross-november-1781']),
          ('europe','Britain, the Dutch Republic and Europe',['kings-speech-to-parliament-6-november-1780', 'britain-and-the-united-provinces-december-1780', 'letter-from-st-eustatius-14-february-1781', 'london-on-the-capture-of-the-st-eustatius-convoy-may-1781', 'amsterdam-letter-on-mr-adams-memorial-may-1781', 'parker-letter-on-the-engagement-on-the-dogger-bank-august-1781']),
          ('congress','Congress and the public finances',['plan-for-a-national-bank-may-1781', 'congress-on-a-loan-for-citizens-of-south-carolina-and-georgia-23-july-1781'])],
        'children':{'britain-and-the-united-provinces-december-1780':['kings-manifesto-against-the-united-provinces-december-1780', 'order-for-general-reprisals-against-the-united-provinces-20-december-1780'],
                    'the-surrender-at-york-october-december-1781':['washington-to-congress-near-york-19-october-1781', 'cornwallis-to-clinton-york-town-20-october-1781']},
        'expect':(7, 1623)},
  # A thin year (release v0.11.25): 30 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1782:{'categories':[
          ('war','The war in America',['head-quarters-orders-of-10-january-1782-on-leave-of-absence', 'cornwallis-letter-to-clinton-of-13-october-1781', 'letter-from-camden-south-carolina-february-1782', 'washington-letter-of-10-may-1782-with-carleton-letter', 'greene-letters-of-may-1782', 'charlestown-report-savannah-evacuated-july-1782', 'fishkill-report-rochambeau-at-verplanck-point-september-1782', 'brig-brought-into-beverly-by-her-prisoners-september-1782', 'letter-from-fort-pitt-3-september-1782', 'greene-letters-of-28-and-29-august-1782-with-leslie-and-gist', 'portsmouth-report-captain-snider-from-canada-october-1782', 'letter-from-greene-camp-of-2-september-1782', 'fishkill-report-lloyds-neck-evacuated-october-1782', 'head-quarters-verplanck-point-orders-of-24-october-1782', 'letter-from-uxbridge-near-charlestown-5-october-1782']),
          ('abroad','Britain, France, Spain and Holland; the war at sea',['king-speech-opening-parliament-27-november-1781', 'martinique-merchant-letter-on-st-kitts-march-1782', 'boston-comment-on-a-treaty-between-france-and-holland-april-1782', 'martinico-gazette-account-of-the-sea-engagement-april-1782', 'handbill-from-amsterdam-holland-declares-america-independent-march-1782', 'king-speech-closing-the-session-11-july-1782', 'siege-of-gibraltar-autumn-1782', 'london-report-royal-george-lost-at-spithead-august-1782', 'boston-report-bouille-at-martinique-december-1782']),
          ('congress','Congress, the peace and public life',['vermont-relinquishes-its-unions-february-1782', 'carleton-and-digby-letter-and-congress-august-1782', 'office-for-foreign-affairs-arret-on-prize-goods-september-1782', 'congress-resolutions-of-4-october-1782-on-peace', 'congress-proclamation-of-a-day-of-thanksgiving-october-1782', 'congress-order-of-7-november-1782-releasing-captain-asgill'])],
        'children':{'carleton-and-digby-letter-and-congress-august-1782':['carleton-and-digby-letter-to-washington-2-august-1782', 'congress-resolutions-of-12-august-1782-on-the-letter'],
                    'greene-letters-of-may-1782':['greene-letter-of-21-may-1782-on-a-proposed-cessation-of-hostilities', 'greene-letter-of-31-may-1782-with-wayne-letter'],
                    'siege-of-gibraltar-autumn-1782':['gibraltar-paragraph-of-10-august-1782', 'elliot-letter-of-12-september-1782-from-a-cork-gazette', 'boston-report-of-a-brig-from-cadiz-29-november-1782', 'hague-1-october-1782-letter-from-paris-on-the-siege']},
        'expect':(8, 1509)},
  # A thin year (release v0.11.26): 22 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1783:{'categories':[
          ('peace','The peace',['paris-the-negotiations-for-peace-seem-to-be-broken-up-october-1782', 'townshend-letter-to-the-bank-of-england-november-1782', 'basseterre-report-of-a-peace-concluded-january-1783', 'brig-ranger-and-mr-townshends-letter-to-the-lord-mayor-december-1782', 'the-articles-of-peace-and-the-cessation-of-arms-printed-march-may-1783', 'lisbon-treaty-of-commerce-with-the-united-states-nearly-agreed-april-1783']),
          ('war','The end of the war: the army, the prisoners and the debt',['general-clark-letter-on-the-expedition-from-the-ohio-november-1782', 'major-burnet-arrives-with-general-greenes-dispatches-january-1783', 'prize-ship-of-20-guns-to-the-frigate-hague-january-1783', 'mr-morris-letter-to-congress-on-his-office-january-1783', 'tell-it-to-the-whole-world-the-prisoners-at-new-york-april-1783', 'continental-troops-march-to-charleston-june-1783', 'versailles-dispatches-of-m-de-suffren-march-1783', 'maryland-act-to-invest-congress-with-power-to-levy-duties-june-1783', 'virginia-assembly-votes-50000-pounds-to-congress-june-1783', 'captain-dalton-arrives-from-canada-august-1783']),
          ('ships','Ships, ports and news by sea',['mr-miller-late-printer-of-the-london-evening-post-arrives-january-1783', 'london-evening-post-statement-of-the-jamaica-fleet-of-july-1782', 'philadelphia-port-open-to-vessels-from-any-foreign-port-april-1783', 'french-frigate-with-stores-for-the-america-portsmouth-june-1783', 'schooner-molly-from-grenada-report-on-the-stadtholder-july-1783', 'no-foreign-vessels-entered-at-new-york-july-1783'])],
        'children':{'the-articles-of-peace-and-the-cessation-of-arms-printed-march-may-1783':['provisional-articles-of-peace-30-november-1782', 'preliminary-articles-between-great-britain-and-france-20-january-1783', 'kings-proclamation-of-the-cessation-of-arms-february-1783', 'congress-proclamation-of-the-cessation-of-arms-11-april-1783', 'washington-orders-for-proclaiming-the-cessation-of-hostilities-18-april-1783']},
        'expect':(9, 1100)},
  # A thin year (release v0.11.27): 13 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1787:{'categories':[
          ('convention','The Convention and the Constitution',['result-of-the-federal-convention-the-constitution-september-1787', 'wilmington-report-general-washington-at-the-bridge-near-the-head-of-elk-1787', 'mr-jay-letter-denying-sentiments-against-the-constitution-december-1787']),
          ('foreign','Foreign powers, trade and the sea',['heads-of-the-treaty-with-the-emperor-of-morocco-1786', 'boston-report-british-ship-maria-on-lake-champlain-1787', 'cape-francois-letter-passes-required-for-american-vessels-in-french-west-indies-1787', 'london-letter-on-virginia-additional-duty-on-british-ships-1787', 'philadelphia-report-ship-caractacus-taken-by-an-algerine-corsair-1787']),
          ('government','Congress and American government',['congress-recommends-the-states-repeal-laws-inconsistent-with-the-treaty-of-peace-april-1787', 'congress-12-july-1787-certificates-for-pensioned-officers', 'ordinance-for-the-government-of-the-territory-north-west-of-the-river-ohio-1787', 'congress-requisition-for-1787-11-october-1787', 'congress-appoints-judges-in-the-western-territory-october-1787'])],
        'children':{},
        'expect':(10, 1297)},
  # A thin year (release v0.11.28): 7 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1788:{'categories':[
          ('constitution','The Constitution and Congress',['letter-of-the-president-of-the-federal-convention-to-a-friend-in-fredericksburg-january-1788', 'congress-on-the-district-of-kentucky-june-1788', 'virginia-convention-ratifies-the-constitution-june-1788', 'congress-on-putting-the-constitution-into-operation-13-september-1788']),
          ('abroad','News from abroad',['french-council-of-state-act-on-commerce-with-the-united-states-december-1787', 'letter-from-lorient-on-troubles-in-france-july-1788', 'nova-scotia-report-that-benedict-arnold-is-suspected-of-setting-fire-to-his-house-1788'])],
        'children':{},
        'expect':(7, 2379)},
  # A thin year (release v0.11.29): 6 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1789:{'categories':[
          ('government','The new federal government',['act-establishing-the-department-of-foreign-affairs-1789', 'revenue-officers-appointed-by-the-president-august-1789']),
          ('war','War and unrest in Europe',['london-report-of-a-tumult-at-barcelona-1789', 'vienna-13-may-1789-report-from-croatia', 'london-report-of-a-letter-from-ancona-on-the-fleets-1789']),
          ('public','American public life',['boston-paragraph-on-american-genius-abroad-july-1789'])],
        'children':{},
        'expect':(5, 742)},
  # A thin year (release v0.11.30): 5 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1790:{'categories':[
          ('government','The federal government',['president-speech-to-both-houses-8-january-1790', 'treasury-report-of-4-march-1790-on-further-revenue']),
          ('public','American public life',['anecdote-of-a-french-gentleman-1790', 'essay-on-the-idea-that-wars-are-necessary-1790']),
          ('west','The western posts and Britain',['boston-paragraph-the-western-posts-still-retained-november-1790'])],
        'children':{},
        'expect':(5, 950)},
  # A thin year (release v0.11.31): 1 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1771:{'categories':[
          ('parliament','London and Parliament',['wilkes-letter-to-the-speaker-march-1771'])],
        'children':{},
        'expect':(4, 546)},
  # A thin year (release v0.11.32): 49 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1773:{'categories':[
          ('colonies','The colonies and the tea',['boston-custom-house-notice-on-registers-december-1772', 'letter-from-a-gentleman-on-fortifying-the-town-1773', 'new-york-report-the-ministry-to-repeal-the-tea-duty-january-1773', 'london-letter-on-the-orphan-house-in-georgia-1772', 'london-report-dispatches-for-the-governors-in-america-1772', 'virginia-burgesses-resolutions-of-12-march-1773', 'boston-report-fire-in-the-custom-house-march-1773', 'massachusetts-house-resolutions-answering-virginia-may-1773', 'annapolis-letter-on-the-maryland-bank-stock-july-1773', 'london-report-emigration-from-the-north-of-ireland-1773', 'new-york-report-the-mississippi-packet-sails-july-1773', 'london-gazette-governors-of-south-carolina-and-nova-scotia-june-1773', 'south-carolina-commons-house-on-the-virginia-letter-july-1773', 'london-report-a-governor-for-the-ohio-colony-july-1773', 'london-report-french-refugees-for-new-york-july-1773', 'new-york-report-three-tea-ships-october-1773', 'london-report-colony-agents-warned-on-the-bounties-august-1773', 'new-york-report-tea-agents-appointed-december-1773']),
          ('britain','King, Parliament and London',['chester-letter-on-a-gunpowder-explosion-november-1772', 'london-report-amherst-sworn-of-the-privy-council-1772', 'king-speech-opening-parliament-26-november-1772', 'london-report-the-recorder-s-charge-to-the-grand-jury-1772', 'london-report-a-sudden-fog-1773', 'london-report-burke-on-the-door-keepers-april-1773', 'london-report-the-speaker-reads-the-sheriffs-letter-april-1773', 'wilkes-letter-to-the-speaker-20-april-1773', 'london-report-ships-for-the-north-pole-1773', 'london-common-council-on-the-east-india-bill-28-may-1773', 'portsmouth-letter-on-the-king-s-visit-to-the-fleet-may-1773', 'london-report-lord-north-moves-a-mark-of-favour-for-general-monckton-1773', 'london-report-the-midsummer-day-common-hall-june-1773', 'king-speech-closing-the-session-1-july-1773', 'london-report-the-french-ambassador-at-portsmouth-1773', 'london-report-the-king-s-gifts-at-portsmouth-june-1773', 'london-paragraph-a-scotch-peruke-maker-july-1773']),
          ('abroad','Europe, the war and the islands',['london-report-a-frigate-fired-upon-at-carthagena-1772', 'report-captain-henshaw-from-st-vincent-february-1773', 'london-report-the-hotel-dieu-burnt-at-paris-1773', 'st-vincent-report-a-treaty-with-the-caribs-february-1773', 'paris-report-rumours-of-war-april-1773', 'london-report-a-loss-on-the-river-canton-1773', 'vienna-report-advices-from-constantinople-may-1773', 'dresden-report-a-storm-at-reichenbach-june-1773', 'temeswar-letter-on-the-turks-and-russians-may-1773', 'philadelphia-report-french-and-spanish-navy-laid-up-july-1773', 'honduras-letter-on-a-species-of-tigers-june-1773', 'constantinople-letter-on-the-turkish-fleet-may-1773', 'amsterdam-letter-a-courier-from-paris-august-1773', 'paris-letter-the-charge-d-affaires-to-leave-london-august-1773'])],
        'children':{},
        'expect':(6, 846)},
  # A thin year (release v0.11.33): 18 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1791:{'categories':[
          ('government','The new government: Congress, the President and the Federal District',['the-acts-admitting-kentucky-and-vermont-into-the-union-february-1791', 'presidents-message-of-14-february-1791-on-commerce-with-great-britain', 'act-for-raising-and-adding-another-regiment-march-1791', 'alexandria-the-first-corner-stone-of-the-federal-district-april-1791', 'the-presidents-speech-and-the-answers-of-the-two-houses-october-1791']),
          ('frontier','The frontier: expeditions and treaties',['general-scotts-account-of-the-expedition-against-the-wabash-towns-june-1791', 'a-correspondent-on-the-treaty-held-by-timothy-pickering-with-the-six-nations-july-1791', 'danville-letter-an-express-from-general-wilkinson-august-1791', 'general-st-clairs-defeat-november-1791']),
          ('abroad','News from abroad: France, Britain, the West Indies and the East',['calcutta-paper-on-tippoo-saib-and-the-rajah-of-travancore-january-1791', 'letter-from-paris-of-10-march-1791-on-the-importation-of-oil', 'the-english-papers-on-the-battle-near-carpentras-july-1791', 'london-the-plague-rages-in-turkey-june-1791', 'm-drouet-recital-before-the-national-assembly-on-stopping-the-king-june-1791', 'the-insurgents-of-birmingham-had-made-a-gridiron-july-1791', 'london-prince-john-the-african-prince-arrives-from-sierra-leone-september-1791', 'by-the-schooner-hardy-from-cape-francois-the-insurrection-october-1791', 'letter-of-the-king-of-france-to-the-national-assembly-accepting-the-constitution-september-1791'])],
        'children':{'the-acts-admitting-kentucky-and-vermont-into-the-union-february-1791':['act-declaring-the-consent-of-congress-to-the-state-of-kentucky-february-1791', 'act-for-the-admission-of-the-state-of-vermont-february-1791'],
                    'the-presidents-speech-and-the-answers-of-the-two-houses-october-1791':['presidents-speech-to-both-houses-25-october-1791', 'answer-of-the-house-of-representatives-october-1791', 'address-of-the-senate-to-the-president-october-1791'],
                    'general-st-clairs-defeat-november-1791':['general-scotts-circular-letter-to-the-county-lieutenants-november-1791', 'general-st-clairs-letter-to-the-secretary-of-war-9-november-1791']},
        'expect':(6, 1242)},
  # A thin year (release v0.11.34): 29 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1792:{'categories':[
          ('war','War, revolution and foreign news',['paragraph-the-prince-royal-of-denmark-abolishes-the-slave-trade-after-1803-1792', 'baltimore-report-brigantine-greyhound-from-cape-francois-1792', 'decree-of-the-national-assembly-declaring-war-against-the-king-of-hungary-and-bohemia-april-1792', 'general-advertiser-report-la-fayette-army-takes-the-citadel-of-namur-1792', 'boston-letter-from-macao-captain-kendrick-attacked-on-the-coast-1792', 'paris-the-assembly-sends-a-deputation-to-the-funeral-of-paul-jones-1792', 'decree-of-the-national-assembly-accusing-m-la-fayette-august-1792', 'paris-essay-comparative-statement-of-the-forces-of-the-concerting-kings-1792', 'dublin-letter-subscription-of-three-millions-sterling-1792', 'general-dumourier-letter-to-servan-the-prussians-in-full-retreat-october-1792']),
          ('west','The frontiers and the Indian nations',['english-paper-colonel-simcoe-to-deliver-up-the-british-posts-1791', 'the-president-letter-and-the-secretary-of-war-statement-on-the-indian-war-january-1792', 'albany-paragraph-the-brothertown-indians-petition-to-be-free-citizens-1792', 'act-for-the-protection-of-the-frontiers-1792', 'charleston-letter-from-the-rock-landing-mr-bowles-seized-by-the-spaniards-1792', 'albany-gazette-deputation-of-the-five-nations-to-the-miami-village-1792', 'knoxville-paragraph-the-governors-of-louisiana-and-pensacola-arm-the-creeks-and-cherokees-1792', 'mr-seagrove-letter-to-the-citizens-of-georgia-on-the-creek-nation-october-1792']),
          ('government','American public life and government',['boston-paragraph-colonel-humphreys-resident-in-portugal-1792', 'act-to-establish-the-post-office-and-post-roads-1792', 'the-president-message-the-king-of-france-letter-accepting-the-constitution-march-1792', 'philadelphia-paragraph-loan-of-three-millions-of-guilders-at-amsterdam-1792', 'the-president-returns-the-apportionment-act-with-his-objections-april-1792', 'act-establishing-a-mint-and-regulating-the-coins-1792', 'act-more-effectually-to-provide-for-the-national-defence-by-an-uniform-militia-1792', 'petersburg-paragraph-alarming-accounts-of-an-insurrection-on-the-eastern-shore-1792', 'philadelphia-paragraph-the-constitution-of-kentucky-ratified-1792', 'the-president-proclamation-against-proceedings-obstructing-the-laws-on-distilled-spirits-september-1792', 'the-president-speech-to-both-houses-of-congress-november-1792'])],
        'children':{},
        'expect':(8, 1629)},
  # A thin year (release v0.11.35): 33 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them,
  # and the first pilot's document group on the clearance resolution of May 1794 (two printings, in the data since v0.1.0),
  # listed with 1794's stories as 1797's pilot groups are with 1797's (register, X-1794-P).
  1794:{'categories':[
          ('europe','The war in Europe',['havre-letter-on-the-retaking-of-toulon-december-1793', 'london-report-french-descent-put-off-for-jersey-march-1794', 'king-of-prussia-declaration-against-a-general-armament-1794', 'london-thirty-one-sail-at-brest-march-1794', 'new-york-news-from-brest-by-the-brig-mary-may-1794', 'brussels-allied-armies-on-the-defensive-march-1794', 'london-king-of-prussia-to-give-no-more-assistance-march-1794', 'brussels-report-of-french-money-for-the-king-of-prussia-march-1794', 'duke-of-york-letter-from-tournay-13-may-1794', 'tournay-account-of-the-british-column-18-may-1794', 'paris-another-action-near-tournay-21-may-1794', 'boston-news-from-lisbon-by-marblehead-september-1794', 'british-note-to-the-imperial-court-on-subsidies-1794', 'london-dispatches-from-warsaw-retreat-of-the-king-of-prussia-october-1794', 'london-duke-of-brunswick-to-command-the-allied-armies-october-1794', 'vienna-retreat-of-the-prussians-from-warsaw-september-1794']),
          ('seas','Neutral ships, Britain and France',['queen-of-portugal-proclamation-convoy-for-american-vessels-1794', 'fayetteville-letter-on-an-action-near-charleston-january-1794', 'norfolk-french-fleet-arrives-in-hampton-roads-february-1794', 'british-additional-instructions-of-november-1793', 'report-of-a-british-order-on-american-prizes-april-1794', 'boston-report-on-captain-talbot-under-a-french-commission-may-1794', 'clearance-resolution-1794', 'house-of-commons-on-the-american-embargo-26-may-1794', 'order-in-council-on-appeals-of-american-ships-6-august-1794', 'jay-memorial-to-lord-grenville-july-1794']),
          ('america','Congress, the frontier and the insurrection',['madison-resolutions-on-the-commerce-of-foreign-nations-january-1794', 'charleston-letter-from-georgia-on-enlisting-for-the-french-service-january-1794', 'president-message-on-an-encroachment-by-british-troops-21-may-1794', 'letter-from-an-officer-of-the-legion-near-greenville-28-july-1794', 'the-insurrection-in-the-western-counties-of-pennsylvania-1794', 'wayne-letter-on-the-action-of-20-august-1794', 'news-from-the-westward-general-wayne-november-1794', 'house-of-representatives-address-to-the-president-29-november-1794'])],
        'children':{'the-insurrection-in-the-western-counties-of-pennsylvania-1794':['president-proclamation-of-25-september-1794', 'pittsburgh-report-of-the-meeting-at-parkinsons-ferry-october-1794', 'resolutions-of-the-meeting-at-parkinsons-ferry-2-october-1794']},
        'expect':(9, 2119)},
  # A thin year (release v0.11.36): 21 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1795:{'categories':[
          ('government','The government and its treaties: the President, Congress and the Secretary of State',['presidents-proclamation-for-a-day-of-thanksgiving-1-january-1795', 'the-presidents-message-on-the-georgia-land-sales-february-1795', 'the-western-posts-to-be-delivered-up-in-june-1796-described-february-1795', 'a-correspondent-on-a-treaty-with-the-dey-of-algiers-march-1795', 'act-to-establish-an-uniform-rule-of-naturalization-january-1795', 'secretary-of-states-circular-of-16-april-1795-on-ships-of-war', 'treaty-of-amity-commerce-and-navigation-with-great-britain-november-1794']),
          ('home','At home and on the frontier: the insurrection, the peace talks, ships and ports',['philadelphia-insurgents-from-the-westward-lodged-in-the-jail-december-1794', 'baltimore-letter-french-ships-of-the-line-in-the-chesapeake-february-1795', 'fort-washington-letter-the-indians-apply-for-a-treaty-of-peace-february-1795', 'boston-unwarrantable-proceedings-a-vessel-burned-at-the-long-wharf-june-1795', 'philadelphia-the-schooner-white-fish-from-lake-erie-november-1795']),
          ('abroad','News from Europe and the colonies',['the-kings-speech-at-the-opening-of-parliament-30-december-1794', 'new-york-the-brig-lydia-from-amsterdam-march-1795', 'proclamation-of-the-revolutionary-committees-of-amsterdam-january-1795', 'the-sloop-delia-from-st-martins-the-island-taken-april-1795', 'from-the-argus-the-port-mary-from-liverpool-may-1795', 'treaty-of-peace-between-the-french-republic-and-the-king-of-prussia-april-1795', 'london-the-judgment-of-mr-hastings-in-westminster-hall-may-1795', 'london-war-with-holland-august-1795', 'commodore-warrens-dispatches-from-quiberon-bay-september-1795'])],
        'children':{},
        'expect':(11, 1668)},
  # A thin year (release v0.11.37): 28 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1796:{'categories':[
          ('war','War and foreign news',['paris-papers-borders-of-the-rhine-changes-in-the-french-army-november-1795', 'port-au-prince-letter-unsuccessful-attack-on-leogane-1796', 'london-paragraph-the-paris-papers-to-the-6th-march-1796', 'new-york-paragraph-london-paper-probability-of-war-between-spain-and-england-1796', 'paris-paragraph-pichegru-resigns-the-command-of-the-army-of-the-rhine-1796', 'london-papers-communicated-by-lord-grenville-on-a-general-pacification-1796', 'london-oracle-mr-grey-notice-of-resolutions-impeaching-ministers-1796', 'paris-paragraph-royalist-assemblages-in-the-department-of-cher-1796', 'paris-army-of-italy-buonaparte-letter-tortona-taken-1796', 'baltimore-report-brig-harriot-from-cape-francois-fleet-from-brest-1796', 'paris-report-the-emperor-requests-an-armistice-june-1796', 'boston-report-fort-dauphin-delivered-to-the-french-1796', 'madrid-the-prince-of-peace-declaration-to-lord-bute-1796', 'st-croix-report-english-ships-carried-into-guadaloupe-1796', 'general-moreau-official-details-of-the-action-at-neresheim-august-1796', 'proclamation-of-sir-john-wentworth-at-halifax-on-hostilities-with-spain-1796']),
          ('ships','Ships and the sea',['boston-report-schooner-industry-from-st-malo-oral-intelligence-from-france-1796', 'philadelphia-paragraph-the-ship-america-brings-home-an-elephant-1796', 'philadelphia-paragraph-brig-sophia-sails-for-algiers-with-the-means-of-the-treaty-1796', 'newburyport-report-capt-seward-from-bermuda-attachments-expected-1796', 'new-york-report-brig-baron-de-carondelet-plundered-by-french-privateers-1796']),
          ('government','American public life and government',['charleston-paper-forms-of-ratification-of-the-treaty-with-great-britain-1796', 'house-of-representatives-mr-blount-resolutions-on-treaties-april-1796', 'treaty-of-friendship-limits-and-navigation-with-spain-1795', 'albany-paragraph-express-with-lord-dorchester-dispatches-western-posts-1796', 'new-york-paragraph-letter-from-paris-on-a-conspiracy-against-the-british-treaty-1796', 'albany-paragraph-gentleman-from-niagara-british-preparing-to-evacuate-the-garrisons-1796', 'captain-bruff-letter-to-the-secretary-of-war-fort-oswego-delivered-1796'])],
        'children':{},
        'expect':(7, 1552)},
  # A thin year (release v0.11.38): 19 stories by the thin-year rule (Y-THIN as amended, B1), the categories as the review proposed them.
  1798:{'categories':[
          ('envoys','The envoys and France',['paris-report-of-what-the-directory-demands-of-the-american-envoys-november-1797', 'the-envoys-dispatches-the-presidents-messages-march-and-april-1798', 'amsterdam-20-march-1798-the-american-consuls-letter-on-the-ship-america', 'president-message-of-21-june-1798-on-general-marshalls-arrival', 'french-papers-of-june-1798-on-the-envoys-dispatches', 'mr-gerry-and-the-french-minister-of-foreign-relations-july-1798']),
          ('measures','The President, Congress and the navy',['the-senate-on-a-motion-to-repeal-the-stamp-duty-january-1798', 'president-proclamation-of-23-march-1798-for-a-day-of-humiliation-fasting-and-prayer', 'the-senate-a-motion-on-removing-aliens-april-1798', 'act-more-effectually-to-protect-the-commerce-and-coasts-may-1798', 'the-house-6-june-1798-mr-fosters-resolutions-on-the-treaties-with-france', 'the-delaware-sloop-of-war-captain-decatur-and-a-french-privateer-july-1798', 'act-for-the-punishment-of-certain-crimes-sedition-july-1798', 'president-message-of-18-july-1798-with-general-washingtons-letter', 'the-presidents-speech-of-8-december-1798-and-the-senates-answer']),
          ('europe','The war in Europe and Egypt',['havre-letter-of-6-november-1797-a-project-of-a-descent-on-england', 'berne-5-march-1798-general-schauenburgs-letter', 'alexandria-letter-on-the-preparations-for-buonapartes-expedition-1798', 'the-action-off-the-mouth-of-the-nile-august-1798'])],
        'children':{'the-envoys-dispatches-the-presidents-messages-march-and-april-1798':['president-message-of-5-march-1798-the-first-dispatches-from-the-envoys', 'president-message-of-19-march-1798-on-the-dispatches-from-the-envoys', 'treasury-circular-of-21-march-1798-to-the-collectors-of-the-customs', 'president-message-of-3-april-1798-laying-the-instructions-and-dispatches-before-congress'],
                    'mr-gerry-and-the-french-minister-of-foreign-relations-july-1798':['minister-of-foreign-relations-to-mr-gerry-12-july-1798', 'mr-gerrys-answer-to-the-minister-20-july-1798'],
                    'the-action-off-the-mouth-of-the-nile-august-1798':['minute-of-facts-stated-in-the-dispatches-to-lord-st-vincent-1798', 'rear-admiral-nelsons-letter-of-3-august-1798'],
                    'the-presidents-speech-of-8-december-1798-and-the-senates-answer':['president-speech-to-both-houses-8-december-1798', 'the-senates-answer-to-the-presidents-speech-12-december-1798']},
        'expect':(8, 1656)}}
CATEGORY_COLORS=['#3987e5','#d95926','#199e70']   # dataviz slots 1-3, validated all-pairs on #050711
short_names={'sn82014782':'Kentucky Gazette','sn83025525':'The Mirror','sn83025527':'Republican Gazetteer','sn83025588':'New Hampshire Gazette','sn83025881':'Gazette of the United States','sn84023150':'The Eagle','sn84024710':'Virginia Argus','sn84038410':'Patowmac Guardian'}
# Map layout: each series is placed at its town of publication (from the catalogue's places_json).
# Coordinates are present-day town centres (latitude, longitude), used only for display.
TOWNS=[('Portland, Me.',r'portland',43.661,-70.255),('Portsmouth, N.H.',r'portsmouth',43.071,-70.763),('Concord, N.H.',r'concord',43.208,-71.538),
       ('Exeter, N.H.',r'exeter',42.981,-70.948),('Dover, N.H.',r'dover,? n\.? ?h',43.198,-70.874),('Hanover, N.H.',r'hanover',43.702,-72.290),
       ('Keene, N.H.',r'keene',42.934,-72.278),('Newburyport, Mass.',r'newbury-?port',42.812,-70.877),('Salem, Mass.',r'salem',42.519,-70.897),
       ('Boston, Mass.',r'boston',42.360,-71.058),('Providence, R.I.',r'providence',41.824,-71.413),('Warren, R.I.',r'warren',41.730,-71.282),
       ('Newport, R.I.',r'newport',41.490,-71.313),('Hartford, Conn.',r'hartford',41.764,-72.685),('Kingston, N.Y.',r'kingston',41.927,-73.997),
       ('New York, N.Y.',r'new[- ]york',40.713,-74.006),('Chatham, N.J.',r'chatham',40.741,-74.383),('Burlington, N.J.',r'burlington',40.071,-74.865),
       # Pennsylvania Packet: "Lancaster, Pa.;Philadelphia, Pa." -- Lancaster only during the British occupation (1777-78).
       ('Philadelphia, Pa.',r'philadelphia',39.952,-75.165),('Wilmington, Del.',r'wilmington',39.746,-75.547),('Dover, Del.',r'dover,? del',39.158,-75.524),
       ('Washington, D.C.',r'washington',38.895,-77.036),('Alexandria, Va.',r'alexandria',38.805,-77.047),('Shepherdstown, W. Va.',r'shepherdstown',39.430,-77.804),
       ('Martinsburg, W. Va.',r'martinsburg',39.456,-77.964),('Wheeling, W. Va.',r'wheeling',40.064,-80.721),('Richmond, Va.',r'richmond',37.541,-77.436),
       ('Williamsburg, Va.',r'williamsburg',37.271,-76.707),('Norfolk, Va.',r'norfolk',36.851,-76.286),('Lynchburg, Va.',r'lynchburg',37.414,-79.142),
       ('Lexington, Ky.',r'lexington',38.040,-84.503),('Charleston, S.C.',r'charles-?town|charleston',32.777,-79.931)]
# Regions colour the telescope's stars by the town where each story was first printed in this archive, grouped as the
# early republic grouped its states. Three hues at most: the stars form a scatter, where any two colours can meet, and only
# three categorical hues stay distinguishable there for colour-blind readers (dataviz check, all pairs, on #050711).
REGIONS=[('New England','Maine, New Hampshire, Massachusetts, Rhode Island and Connecticut','#9085e9',{'Me.','N.H.','Mass.','R.I.','Conn.','Vt.'}),
         ('Middle States','New York, New Jersey, Pennsylvania and Delaware','#199e70',{'N.Y.','N.J.','Pa.','Del.'}),
         ('South and West','Washington, Virginia (with today\'s West Virginia), Kentucky and South Carolina','#d95926',{'D.C.','Va.','W. Va.','Ky.','S.C.'})]
def region_of(place):
    state_abbr=place.split(', ',1)[1]
    found=[i for i,r in enumerate(REGIONS) if state_abbr in r[3]]
    assert len(found)==1, 'Give this town a region in REGIONS: '+place
    return found[0]
for t in TOWNS: region_of(t[0])
def town(places_json):
    raw='; '.join(json.loads(places_json)); low=raw.lower().replace('[','').replace(']','')
    hits=[t for t in TOWNS if re.search(t[1],low)]
    assert hits, 'No town coordinates for place: '+raw
    name,_,lat,lon=hits[0] if len(hits)==1 else next(t for t in hits if t[0].startswith('Philadelphia'))
    return {'place':name,'place_raw':raw,'lat':lat,'lon':lon}
boyd=json.loads(verified_file('views/pulse_boyd.json',release).read_text(encoding='utf8'))
old={o['observation_id']:o for o in boyd['observations']}
summaries={'H012':'A report of the seizure of Peace, attributed to Captain Whitney.','X016':'The Peace seizure report with additional Mercury-attributed commentary.','H013':'A translated Cayenne decree with an attached editorial allegation.',
           # The first pilot's 1794 clearance resolution, shown with 1794's stories since v0.11.35 (register, X-1794-P).
           'H017':'A report that Congress resolved on the 7th that the President may direct clearances for loaded vessels bound beyond the Cape of Good Hope, the embargo notwithstanding.',
           'H019':'The resolution of both Houses on clearances for loaded vessels bound beyond the Cape of Good Hope, printed with its approval of 7 May 1794.'}
notes={'H012':'Publication date differs from the internal Providence dateline of May 13. The seizure date is not supplied.','X016':'The shared report and appended commentary are distinct textual elements. The commentary is not independently corroborated.','H013':'A contextual document, not an established legal cause of the Peace seizure. The original decree and itemized allegations remain unresolved.',
       'H017':'An excerpted version: it keeps the conditions (vessels already loaded, owned by citizens, bound beyond the Cape of Good Hope, security given). "U. S." for "United States" changes nothing of substance.',
       'H019':'Includes the approval of 7 May 1794 and the signature GEO. WASHINGTON. Checked against the Statutes at Large, vol. 1, p. 401, Resolution V: the text, not its effect.'}
OUT.mkdir(exist_ok=True);(OUT/'assets').mkdir(exist_ok=True)
import collections, sys
sys.path.insert(0,str(ROOT/'python_packages'))
import pyarrow.parquet as pq
REV='0b97906ad32e269376872934820357fc333151d8';DATASET='RevolutionCrossroads/loc_chronicling_america_1770-1810'
SMALL={'and','or','of','the','in','at','for','to','a'}
def short_name(lccn,title):
    if lccn in short_names: return short_names[lccn]
    t=re.sub(r'^\s*the\s+','',title.strip(),flags=re.I)
    t=re.split(r'[,;:(\[]|\. | and the | & the ',t)[0].strip(' .')
    head=re.split(r' and | & ',t)[0]
    if len(t)>32 and len(head.split())>=2: t=head  # "Kentucky gazette and general advertiser" -> "Kentucky gazette"
    words=[w if (i and w.lower() in SMALL) else w[:1].upper()+w[1:] for i,w in enumerate(t.split())]
    while len(' '.join(words))>32 and len(words)>1: words.pop()  # cut at a word boundary
    while len(words)>1 and words[-1].lower() in SMALL|{'&'}: words.pop()
    return ' '.join(words) or lccn
def name_papers(papers):
    """Make newspaper names distinct within one set (a year, or all years): some years hold several series with the same
    short name (title changes, rival printers)."""
    names=collections.Counter(p['name'] for p in papers)
    for p in papers:
        if names[p['name']]>1 and p['lccn'] not in short_names:
            full=' '.join(w[:1].upper()+w[1:] if w.lower().strip(',;') not in SMALL else w.lower() for w in re.sub(r'^\s*the\s+','',p['title'],flags=re.I).strip(' .').split())
            p['name']=full if len(full)<=60 and sum(q['title'].lower()==p['title'].lower() for q in papers)==1 else p['name']+' · '+p['lccn']
    names=collections.Counter(p['name'] for p in papers)
    for p in papers:
        if names[p['name']]>1 and p['lccn'] not in short_names: p['name']+=' · '+p['lccn']
    assert len({p['name'] for p in papers})==len(papers), 'newspaper names must be distinct'
    return papers
# ---- The reviewed years: stories read and grouped by hand, every printing checked against its scan ----
observations={};stories=[];reviewed_data={}
with sqlite3.connect(verified_file('research.sqlite',release).as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    titles={r['lccn']:(r['id'],json.loads(r['titles_json'])[0]) for r in db.execute('SELECT * FROM newspapers')}
    towns={r['lccn']:town(r['places_json']) for r in db.execute('SELECT lccn,places_json FROM newspapers')}
    # Newspaper names, distinct over all years: the same names as in the all-years index below.
    paper_name={p['lccn']:p['name'] for p in name_papers([{'lccn':l,'name':short_name(l,t),'title':t} for l,(_,t) in sorted(titles.items())])}
    children={r[0] for r in db.execute('SELECT child_id FROM group_hierarchy')}
    for year,spec in sorted(REVIEWED.items()):
        tops=[t for _,_,ts in spec['categories'] for t in ts]
        shown=[g for t in tops for g in [t]+spec['children'].get(t,[])]   # by category: each top-level story, then its sub-stories
        cat_of={g:f'{year}-{c}' for c,_,ts in spec['categories'] for t in ts for g in [t]+spec['children'].get(t,[])}
        released={r[0][6:] for r in db.execute('SELECT DISTINCT group_id FROM group_publications WHERE publication_date LIKE ?',(f'{year}%',))}
        assert released==set(shown) and len(shown)==len(set(shown)), \
            f'{year}: list every reviewed group of the year once (not listed: {sorted(released-set(shown))}; not in the release: {sorted(set(shown)-released)})'
        papers=[{'id':r['id'],'lccn':r['lccn'],'name':paper_name[r['lccn']],'title':titles[r['lccn']][1],'issues':r['issues'],**towns[r['lccn']]}
                for r in db.execute('SELECT n.id,n.lccn,COUNT(DISTINCT i.id) AS issues FROM newspapers n JOIN issues i ON i.newspaper_id=n.id WHERE i.publication_date LIKE ? GROUP BY n.id ORDER BY n.lccn',(f'{year}%',))]
        if 'order' in spec: papers.sort(key=lambda p:spec['order'].index(p['lccn']))
        coverage=[dict(r) for r in db.execute('SELECT * FROM newspaper_date_coverage WHERE publication_date LIKE ? ORDER BY publication_date,newspaper_id',(f'{year}%',))]
        assert (len(papers),sum(c['observed_pages'] for c in coverage))==spec['expect'], f"{year}: newspapers and surviving pages differ from {spec['expect']}"
        groups=[];year_obs={}
        for short in shown:
            g=dict(db.execute('SELECT * FROM groups WHERE id=?',('group:'+short,)).fetchone())
            rows=list(db.execute('SELECT * FROM group_publications WHERE group_id=? ORDER BY publication_date,newspaper_id,observation_id',(g['id'],)))
            g['members']=[]
            for r in rows:
                oid=r['observation_id'];g['members'].append({'id':oid,'roles':json.loads(r['roles_json'])})
                if oid in year_obs:continue
                assets=[]
                for a in db.execute('SELECT path FROM assets WHERE object_id=? ORDER BY path',(oid,)):
                    path=verified_file(a['path'],release);copy_if_changed(path,OUT/a['path']);assets.append(a['path'])
                o=dict(r);legacy=o['legacy_id'];prior=old.get(oid,{})
                # Selections added after v0.1.0 carry their summary and note in an observation_review annotation.
                review=db.execute("SELECT value_json FROM current_annotations WHERE object_id=? AND annotation_type='observation_review'",(oid,)).fetchone()
                review=json.loads(review[0]) if review else {}
                field=db.execute('SELECT transcription_field FROM observations WHERE id=?',(oid,)).fetchone()[0]
                year_obs[oid]={'id':oid,'legacy_id':legacy,'node':o['lccn'],'page_id':o['page_id'],'issue_id':o['issue_id'],'date':o['publication_date'],'page':o['page_number'],'excerpt':'\n\n'.join(json.loads(o['excerpts_json'])),'source_url':o['pinned_scan_url'],'scans':assets,'transcription':{'RevX_OCR_text':'RevX','ca_ocr_text':'CA'}[field],'summary':prior.get('summary',summaries.get(legacy,review.get('summary',''))),'note':prior.get('note',notes.get(legacy,review.get('note','')))}
            groups.append({**{k:g[k] for k in ['id','kind','label','definition','members']},'category':cat_of[short],'child':short not in tops})
        # The year's overview plays its top-level stories (groups with no parent).
        year_stories=[{'id':g['id'],'label':g['label'],'category':g['category'],'members':[m['id'] for m in g['members']]} for g in groups if g['id'] not in children]
        assert {s['id'][6:] for s in year_stories}==set(tops), f'{year}: every top-level story needs exactly one display category'
        year_stories.sort(key=lambda s:min(year_obs[m]['date'] for m in s['members']))
        # Each passage must belong to exactly one story, so the overview never pulses a passage twice.
        members=[m for s in year_stories for m in s['members']]
        assert len(members)==len(set(members))==len(year_obs), f'{year}: top-level stories must partition the passages'
        for o in year_obs.values():
            assert o['scans'] and o['excerpt'] and o['summary'] and o['date'].startswith(str(year))
            paper_id=next(p['id'] for p in papers if p['lccn']==o['node'])
            assert any(c['newspaper_id']==paper_id and c['publication_date']==o['date'] for c in coverage)
        for g in groups: assert len({m['id'] for m in g['members']})==len(g['members'])
        assert not set(year_obs)&set(observations), 'a passage belongs to one reviewed year'
        observations.update(year_obs); stories+=[{**s,'year':year} for s in year_stories]
        reviewed_data[year]={'year':year,'newspapers':papers,'coverage':coverage,'groups':groups,
                             'categories':[{'id':f'{year}-{c}','label':label,'stories':['group:'+t for t in ts]} for c,label,ts in spec['categories']],
                             'stories':year_stories,'observations':list(year_obs.values())}
reviewed_list=[reviewed_data[y] for y in sorted(reviewed_data)]
# ---- Stories: storylines from the ledger work/stories.json, checked against the reviewed data and the scan verdicts
# (work/stories_parts.py). Pulses and the telescope link each story that one tells ('Read the storyline'). ----
import stories_parts
storylines=stories_parts.check(json.loads((ROOT/'stories.json').read_text(encoding='utf8')),reviewed_data,{y:spec['children'] for y,spec in REVIEWED.items()},ROOT.parent)
storyline_links=stories_parts.links(storylines)
print(f"stories: {len(storylines)} storylines, {sum(len(s['by']) for s in storylines)} pieces, {sum(len(s['every']) for s in storylines)} printings")
# ---- All years: automatic reuse families (not checked against scans), one data file per year ----
years_dir=OUT/'years';years_dir.mkdir(exist_ok=True)
fam_path=release/'derived/reuse_families.parquet'
families=pq.read_table(verified_file('derived/reuse_families.parquet',release)).to_pylist() if fam_path.exists() else []
# Automatic titles (v0.5.1 on): the item's opening words, plus a dateline place when printings agree.
story_titles={}
if (release/'derived/reuse_family_titles.parquet').exists():
    story_titles={t['family_id']:t['title'] for t in pq.read_table(verified_file('derived/reuse_family_titles.parquet',release),columns=['family_id','title']).to_pylist()}
apps_by=collections.defaultdict(list)
if families:
    for a in pq.read_table(verified_file('derived/reuse_family_appearances.parquet',release)).to_pylist(): apps_by[a['family_id']].append(a)
# Transcription checks (v0.6.0 on): whether each printing's passage is also in the page's other machine transcription.
# Stored per observation in the year files as one letter; the pulse page says it in words.
CHECK_CODE={'confirmed':'c','partly':'p','missing_in_other':'m','other_unreadable':'u','no_second_transcription':'n'}
printing_checks={}
if (release/'derived/transcription_checks.parquet').exists():
    printing_checks={(r['family_id'],r['seq']):CHECK_CODE[r['status']] for r in pq.read_table(verified_file('derived/transcription_checks.parquet',release),columns=['family_id','seq','status']).to_pylist()}
    assert len(printing_checks)==sum(len(v) for v in apps_by.values()), 'every printing needs exactly one transcription check'
    assert all(len({a['page_id'] for a in v})==len(v) for v in apps_by.values()), 'one printing per story and page'
by_year=collections.defaultdict(list)
for f in families: by_year[int(f['first_date'][:4])].append(f)
years_index=[]
with sqlite3.connect(verified_file('research.sqlite',release).as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    for year in range(1770,1811):
        fams=sorted(by_year.get(year,[]),key=lambda f:(f['first_date'],-f['newspapers']))
        last=max([f['last_date'] for f in fams]+[f'{year}-12-31'])
        lccns=[r[0] for r in db.execute("SELECT DISTINCT n.lccn FROM newspapers n JOIN issues i ON i.newspaper_id=n.id WHERE i.publication_date LIKE ? ORDER BY n.lccn",(f'{year}%',))]
        if year in reviewed_data:   # a reviewed year keeps its papers in the reviewed order
            first=[p['lccn'] for p in reviewed_data[year]['newspapers']]; lccns=first+[l for l in lccns if l not in first]
        extra_l=sorted({a['lccn'] for f in fams for a in apps_by[f['family_id']]}-set(lccns))
        papers=name_papers([{'id':titles[l][0],'lccn':l,'name':short_name(l,titles[l][1]),'title':titles[l][1],**towns[l]} for l in lccns+extra_l])
        cov=[dict(r) for r in db.execute("SELECT * FROM newspaper_date_coverage WHERE publication_date BETWEEN ? AND ? ORDER BY publication_date,newspaper_id",(f'{year}-01-01',last))]
        # Compact rows: the page expands them (page and issue ids, scan URL, labels and notes are derived, not repeated).
        obs=[];grps=[];days={(c['newspaper_id'],c['publication_date']) for c in cov}
        for f in fams:
            members=[]
            for a in apps_by[f['family_id']]:
                _,lccn,filed,ed,page=a['page_id'].split(':'); date=a['publication_date']   # the printed date; the id keeps the filed one
                assert (titles[lccn][0],date) in days, 'Every matched appearance joins to observed date coverage'
                oid=f"auto:{f['family_id']}:{a['seq']}"
                obs.append({'id':oid,'node':lccn,'date':date,**({'fd':filed} if filed!=date else {}),'ed':int(ed),'page':int(page),'excerpt':a['excerpt'],'tr':a['transcription'],
                            **({'ck':printing_checks[f['family_id'],a['seq']]} if printing_checks else {})})
                members.append(oid)
            grps.append({'id':'auto:'+f['family_id'],'label':story_titles.get(f['family_id'],f['label']),'newspapers':f['newspapers'],'first':f['first_date'],'last':f['last_date'],
                         'long_running':bool(f['long_running']),'members':members})
        (years_dir/f'{year}.json').write_text(json.dumps({'year':year,'scan_base':f'https://huggingface.co/datasets/{DATASET}/resolve/{REV}/media/',
                                                          'newspapers':papers,'coverage':cov,'groups':grps,'observations':obs},ensure_ascii=False,separators=(',',':')),encoding='utf8')
        # The year strip on the pulse page: how many newspapers and pages survive each year (the archive's shape).
        pages_y=db.execute("SELECT COUNT(*) FROM pages p JOIN issues i ON i.id=p.issue_id WHERE i.publication_date LIKE ?",(f'{year}%',)).fetchone()[0]
        years_index.append({'year':year,'reviewed':len(reviewed_data[year]['stories']) if year in reviewed_data else 0,'matched':len(fams),'matched3':sum(f['newspapers']>=3 for f in fams),
                            'papers':len(set(lccns)),'pages':pages_y})
# ---- Story telescope: every story as a star, placed by real values ----
# day = first printing (days since 1 Jan 1770); lat = mean latitude of the towns of the papers that printed it.
EPOCH=datetime.date(1770,1,1).toordinal()
dnum=lambda s:datetime.date.fromisoformat(s).toordinal()-EPOCH
# Each reviewed story's twin in the matched layer: the automatic story that holds at least half of its printings (same
# newspaper, printed date and page). They are one story found twice, so the sky draws it once (the reviewed star), links
# to the twin reach the reviewed story, and the Pulses shelf lists it once. 85 of the 98 stories had one on 2026-11-11.
page_owner=collections.defaultdict(set)
for fid,apps in apps_by.items():
    for a in apps: page_owner[(a['lccn'],a['publication_date'],int(a['page_id'].split(':')[4]))].add(fid)
twins={};paired=[];twin_of=collections.Counter()
for s in stories:
    obs_s=[observations[m] for m in s['members']]
    c=collections.Counter(f for o in obs_s for f in page_owner.get((o['node'],o['date'],int(o['page'])),()))
    if c:
        fid,k=min(c.items(),key=lambda x:(-x[1],x[0]))   # ties go to the first id, so every build pairs the same way
        if k*2>=len(obs_s): paired.append(s['id']); twins.setdefault(fid,s['id']); twin_of[fid]+=1   # two reviewed stories can share one automatic story
print(f'twins: {len(paired)} of {len(stories)} reviewed stories have one; {len(twins)} matched stories are twins, '
      f'{sum(n>1 for n in twin_of.values())} of them the twin of more than one ({max(twin_of.values(),default=0)} at most)')
assert len(paired)>=80, f'only {len(paired)} reviewed stories found their matched twin'
stars=[]
# Reviewed stars carry their year's category: one list over all reviewed years, each category in its year's colour slot.
tele_cats=[{'id':c['id'],'label':c['label'],'year':y,'slot':i,'color':CATEGORY_COLORS[i]} for y in sorted(reviewed_data) for i,c in enumerate(reviewed_data[y]['categories'])]
cat_index={c['id']:i for i,c in enumerate(tele_cats)}
for s in stories:
    obs_s=[observations[m] for m in s['members']]
    ls=sorted({o['node'] for o in obs_s})
    stars.append({'id':s['id'],'year':s['year'],'kind':1,'cat':cat_index[s['category']],'first':min(dnum(o['date']) for o in obs_s),'last':max(dnum(o['date']) for o in obs_s),
                  'papers':len(ls),'prints':len(obs_s),'lat':round(sum(towns[l]['lat'] for l in ls)/len(ls),3),'long':0,'title':s['label']})
for f in families:
    if f['family_id'] in twins: continue   # drawn as its reviewed star
    ls=sorted({a['lccn'] for a in apps_by[f['family_id']]})
    title=story_titles.get(f['family_id'],f['label'])
    stars.append({'id':f['family_id'],'year':int(f['first_date'][:4]),'kind':0,'cat':-1,'first':dnum(f['first_date']),'last':dnum(f['last_date']),
                  'papers':f['newspapers'],'prints':f['appearances'],'lat':round(sum(towns[l]['lat'] for l in ls)/len(ls),3),'long':int(bool(f['long_running'])),
                  'title':title if len(title)<=110 else title[:108].rstrip()+' …'})
# Story topics (release v0.5.2 on): the frozen 24-topic model applied to every printing; lanes in display order.
topic_rows,topic_list,topic_meta={},[],{'topics':[]}
if (release/'derived/story_topics.parquet').exists():
    topic_rows={r['story_id']:r for r in pq.read_table(verified_file('derived/story_topics.parquet',release),columns=['story_id','top_topic','top_share','second_topic','weights_json']).to_pylist()}
    with sqlite3.connect(verified_file('research.sqlite',release).as_uri()+'?mode=ro',uri=True) as db2:
        topic_meta=json.loads(db2.execute("SELECT value_json FROM metadata WHERE key='story_topics'").fetchone()[0])
    topic_list=sorted(topic_meta['topics'],key=lambda x:x['display_order'])
# The Topic view groups the topics into the seven families of the first study. The site's names for topics and families say what
# the stories in each wedge mostly are: they were checked against 810 matched stories read blind, and renamed where a tested name
# fitted better (topic labels review, 12 Nov 2026: docs/notes/2026-11-12-topic-labels-review.md). Reprinted stories are mostly news,
# so names of kinds of notice fitted few of them. The release's long labels and the study's family names are not shown.
# The families are not used for colour: a spot check (8 Nov 2026) found that among matched stories the model's notice and
# "other" families mostly hold news (fires, bridges, courts), because advertisements were rarely reprinted across papers.
# Each family: (name in the study, the key in the release's topic labels; the site's name; name for phones).
FAMILIES=[('Politics and public institutions','Politics','Politics'),('War, diplomacy and shipping','War, diplomacy and shipping','War and ships'),
          ('Commerce, property and everyday transactions','Commerce and property','Commerce'),('Law, debt and taxation','Law, debt and taxes','Law and debt'),
          ('Coercion and escape','People sought','People sought'),('Literature and reflection','Poems, anecdotes and reflections','Poems'),
          ('Formats and unresolved clusters','Letters and mixed','Mixed')]
SHORT={'T01':'Political argument','T02':'Laws and courts','T03':'Ships and the sea','T04':'Cloth and dry goods','T05':'Horses and other animals',
       'T06':'Federal government','T07':'Land for sale','T08':'Courts and lawsuits','T09':'Battles and armies','T10':'Estates and debts',
       'T11':'France and Europe','T12':'Legislatures','T13':'Mixed: place names','T14':'Poems, anecdotes and reflections','T15':'Money and public finance',
       'T16':'Notices seeking people','T17':'Goods and cargoes','T18':'Mixed: personal names','T19':'Letters','T20':'Rulers, parliaments and officials',
       'T21':'Foreign relations and trade','T22':'Shops, local notices and news','T23':'Taxes, proprietors and public sales'}
# A topic shown in another topic's wedge: T24 (insolvent estates) holds the same estate and debt notices as T10, so its stories take
# T10's wedge, with the two topics' shares added together. The release keeps both topics.
FOLD={'T24':'T10'}
# One plain line for each topic whose name fits mainly one period (the review's samples, by decade), shown on the telescope's hover card.
PERIOD={'T05':'Most horse notices here are from the 1770s; later stories in this wedge are mostly other news.',
        'T10':'Most estate and debt notices here are from the 1770s; later stories in this wedge are mostly other news.',
        'T16':'Most notices here are from the 1770s; after 1780 most stories in this wedge are other news that describes people or things.'}
topic_labels=json.loads(verified_file('sources/work__topic_labels.json',release).read_text(encoding='utf8'))
topic_rel={json.loads(l)['id'].split(':')[-1]:json.loads(l) for l in verified_file('tables/topics.jsonl',release).read_text(encoding='utf8').splitlines() if l.strip()}
fam_index={f[0]:i for i,f in enumerate(FAMILIES)}
tid=lambda x:x['id'].split(':')[-1]
assert topic_list and all((tid(x) in SHORT)!=(tid(x) in FOLD) and topic_labels[tid(x)]['category'] in fam_index for x in topic_list), \
    "every topic needs a site name and a family, or is shown in another topic's wedge"
assert all(t in SHORT for t in FOLD.values()) and set(SHORT)|set(FOLD)=={tid(x) for x in topic_list} and set(PERIOD)<=set(SHORT), \
    'every site name belongs to a topic of the model; folded topics go to shown ones; period lines are for shown topics'
topic_index={tid(x):k for k,x in enumerate(topic_meta['topics'])}   # a topic's place in each story's weights (the model's order)
topic_list=sorted((x for x in topic_list if tid(x) in SHORT),key=lambda x:(fam_index[topic_labels[tid(x)]['category']],x['display_order']))   # by family, then by shared vocabulary
lane_t={tid(x):i for i,x in enumerate(topic_list)}
lane_t.update({a:lane_t[b] for a,b in FOLD.items()})
lane_of={x['id']:lane_t[tid(x)] for x in topic_meta['topics']}
shared_lanes={lane_t[b] for b in FOLD.values()}   # wedges that hold more than one topic
def topic_place(r):
    """A story's wedge, its share of the topic mix in that wedge, and the next wedge (the strongest other one)."""
    lane=lane_of[r['top_topic']]
    if lane not in shared_lanes: return lane,r['top_share'],lane_of.get(r['second_topic'],lane)
    w=json.loads(r['weights_json']);by_lane=collections.defaultdict(float)
    for t,k in topic_index.items(): by_lane[lane_t[t]]+=w[k]
    nxt=max((l for l in by_lane if l!=lane),key=lambda l:(by_lane[l],-l))
    return lane,by_lane[lane],(nxt if by_lane[nxt]>0 else lane)
# Search text: the title plus the opening words of the first printing (lower case), loaded by the page only when searching.
first_excerpt={fid:min(apps,key=lambda a:a['seq'])['excerpt'] for fid,apps in apps_by.items()}
for s in stories:
    first_excerpt[s['id']]=min((observations[m] for m in s['members']),key=lambda o:o['date'])['excerpt']
first_town={fid:towns[min(apps,key=lambda a:(a['publication_date'],a['seq']))['lccn']] for fid,apps in apps_by.items()}
for s in stories:
    first_town[s['id']]=towns[min((observations[m] for m in s['members']),key=lambda o:o['date'])['node']]
town_count=collections.Counter()
for s in stars:
    ft=first_town[s['id']]; s['flat']=ft['lat']; s['flon']=ft['lon']; s['reg']=region_of(ft['place']); town_count[ft['place']]+=1
for s in stars:
    r=topic_rows.get(s['id'])
    lane,share,nxt=topic_place(r) if r else (-1,0,-1)
    s['topic']=lane; s['tconf']=round(share,2)
    s['topic2']=nxt   # the second-strongest wedge: which way a mixed story leans
    s['text']=re.sub(r'\s+',' ',(s['title']+' '+(first_excerpt.get(s['id']) or '')).replace('ſ','s')).lower().strip()
stars.sort(key=lambda s:(s['first'],-s['papers'],s['id']))
tele={'epoch':'1770-01-01','count':len(stars),**{k:[s[k] for s in stars] for k in ['id','year','kind','cat','first','last','papers','prints','lat','long','title','topic','topic2','tconf','flat','flon','reg']},
      'topics':[{'id':x['id'],'label':SHORT[tid(x)],'family':fam_index[topic_labels[tid(x)]['category']],
                 'provisional':topic_rel[tid(x)]['restart_agreement']<0.6,'terms':' · '.join(x['terms'][:3]),
                 **({'period':PERIOD[tid(x)]} if tid(x) in PERIOD else {})} for x in topic_list],
      'families':[{'short':s,'tiny':t} for f,s,t in FAMILIES]}
(OUT/'telescope.json').write_text(json.dumps(tele,ensure_ascii=False,separators=(',',':')),encoding='utf8')
(OUT/'telescope-text.json').write_text(json.dumps({'count':len(stars),'text':[s['text'] for s in stars]},ensure_ascii=False,separators=(',',':')),encoding='utf8')
tele_stamp=hashlib.sha256((OUT/'telescope.json').read_bytes()+(OUT/'telescope-text.json').read_bytes()).hexdigest()[:12]
# ---- Trace: the words of a story's title worth following through the years (the story card's "Trace a word") ----
# Counted the way the telescope's search finds them: at the start of a word, in the title and the opening words. A word
# is offered when its stories are spread over the years, or over the months, unlike the sky's stories as a whole (a
# G-test, p < .001 with 40 and 11 degrees of freedom), so that tracing it shows more than the archive's coverage. Each
# word keeps its number of stories and a score (how far its spread differs, shrunk for small numbers), which orders a
# title's words on the card. The pages split a title into words the same way (titleWords in both pages).
TRACE_STOP=set('''that with this from have been were which their there they them then than what when where will would shall
should could into upon unto your yours ours more most some such other others only also very much many each every both after
before about above below under over again further once here hers himself herself itself themselves those these being having
doing does done same just while during against between through without within along among until because since though
although whether either neither cannot made make makes making said says following extract letter letters dated date
gentleman gentlemen received receive arrived arrive informed inform learn learned hear heard yesterday today last next first
second third days week weeks month months year years time times morning evening night january february march april june july
august september october november december sept monday tuesday wednesday thursday friday saturday sunday inst instant ultimo
messrs sirs cent copy published publish printed print paper papers account accounts news intelligence advices advice late
lately former latter public publick great well good part whole number'''.split())
def title_words(t):
    return {w for w in re.findall(r'[a-z]+',re.sub(r"['’]s\b",'',t.lower().replace('ſ','s'))) if len(w)>=4 and w not in TRACE_STOP}
import bisect, math
post=collections.defaultdict(list)
for i,s in enumerate(stars):
    for tok in set(re.findall(r'[a-z]+',s['text'])): post[tok].append(i)
toks=sorted(post)
year_of=[s['year'] for s in stars]
month_of=[(datetime.date(1770,1,1)+datetime.timedelta(days=s['first'])).month for s in stars]
year_all,month_all,n_all=collections.Counter(year_of),collections.Counter(month_of),len(stars)
def g_test(obs,base,n): return 2*sum(o*math.log(o*n_all/(n*base[k])) for k,o in obs.items() if o)
trace_words={}
for w in sorted(set().union(*(title_words(s['title']) for s in stars))):
    a,b=bisect.bisect_left(toks,w),bisect.bisect_left(toks,w+'{')
    if sum(len(post[t]) for t in toks[a:b])<3: continue
    hit_ix=set().union(*(post[t] for t in toks[a:b])); n=len(hit_ix)
    if not 3<=n<=3000: continue
    gy=g_test(collections.Counter(year_of[i] for i in hit_ix),year_all,n); gm=g_test(collections.Counter(month_of[i] for i in hit_ix),month_all,n)
    if gy<73.4 and gm<31.3: continue   # spread like the archive: its trace would show the archive's coverage
    trace_words[w]=[n,round(1000*max(gy,gm*40/11)/(2*(n+30)))]
(OUT/'trace.json').write_text(json.dumps({'words':trace_words},ensure_ascii=False,separators=(',',':')),encoding='utf8')
trace_stamp=hashlib.sha256((OUT/'trace.json').read_bytes()).hexdigest()[:12]
trace_cover=sum(1 for s in stars if title_words(s['title'])&trace_words.keys())
print(f'trace: {len(trace_words):,} words; {trace_cover:,} of {len(stars):,} stories have at least one')
assert trace_cover>=.9*len(stars), 'most stories should offer a word to trace'
reg_count=collections.Counter(s['reg'] for s in stars)
tele_boot={'release_version':manifest['version'],'stamp':tele_stamp,'trace':trace_stamp,'stories':len(stars),'twins':twins,'storylines':storyline_links,
           # The archive under the timeline, as on the Pulses year strip: [year, newspapers with surviving pages, pages, reviewed stories].
           'years':[[y['year'],y['papers'],y['pages'],y['reviewed']] for y in years_index],
           'regions':[{'label':label,'states':states,'color':color,'stories':reg_count[i]} for i,(label,states,color,_) in enumerate(REGIONS)],
           # Sizes as served, so the loading bar can measure progress even when the server compresses the files.
           'bytes':{'data':(OUT/'telescope.json').stat().st_size,'text':(OUT/'telescope-text.json').stat().st_size},
           'towns':[{'name':n.split(',')[0],'lat':la,'lon':lo,'stories':town_count[n]} for n,_,la,lo in TOWNS if town_count[n]],'categories':[{'label':c['label'],'year':c['year'],'color':c['color']} for c in tele_cats]}
# ---- The site: five pages sharing one header and footer (work/site_parts.py, work/site.css) ----
from site_parts import fill, REPO
from urllib.parse import quote
VER=manifest['version']; N_STARS=len(stars)
shutil.copyfile(ROOT/'site.css',OUT/'site.css')
shutil.copyfile(ROOT/'glass.js',OUT/'glass.js')   # the glass controls shared by the Telescope and Pulses pages
shutil.copyfile(ROOT/'radio.js',OUT/'radio.js')   # the radio's voice and sounds, made in the browser (Radio page, Pulses, Telescope)
shutil.copyfile(ROOT/'music.js',OUT/'music.js')   # music from the data, made in the browser (Pulses); its recordings are in audio/music/, which the build leaves alone
# The offline bundle: the two libraries the pages once loaded from jsdelivr are kept with the site, so it runs without the
# internet (an exhibition machine): three.js r160 for the Telescope and qrcode-generator 1.4.4 for the exhibition's codes.
(OUT/'lib').mkdir(exist_ok=True)
for f in sorted((ROOT/'lib').glob('*.js')): copy_if_changed(f,OUT/'lib'/f.name)
tele_html=(ROOT/'telescope.html').read_text(encoding='utf8').replace('__TELESCOPE_BOOT__',json.dumps(tele_boot,ensure_ascii=False).replace('</','<\\/'))
assert '__TELESCOPE_BOOT__' not in tele_html
(OUT/'telescope.html').write_text(fill(tele_html,'telescope',VER,N_STARS),encoding='utf8')
# ---- All years in one slim index, for pulse views of several years (any stretch of 1770-1810) ----
# The year files carry every passage. This index carries only what the map and the story shelf need: the newspapers,
# the stories (title, reach, dates, topic), the printings (newspaper, day, edition, page, transcription check) and the
# surviving pages. A passage loads from its year file when it is opened.
with sqlite3.connect(verified_file('research.sqlite',release).as_uri()+'?mode=ro',uri=True) as db3:
    db3.row_factory=sqlite3.Row
    cov_all=[dict(r) for r in db3.execute("SELECT newspaper_id,publication_date,observed_pages,observed_issues_editions FROM newspaper_date_coverage ORDER BY publication_date,newspaper_id")]
id_to_lccn={v[0]:k for k,v in titles.items()}
all_l=sorted({id_to_lccn[c['newspaper_id']] for c in cov_all}|{a['lccn'] for v in apps_by.values() for a in v})
idx_papers=name_papers([{'id':titles[l][0],'lccn':l,'name':short_name(l,titles[l][1]),'title':titles[l][1],**towns[l]} for l in all_l])
pix={p['lccn']:i for i,p in enumerate(idx_papers)}
assert all(p['name']==paper_name[p['lccn']] for p in idx_papers), 'a newspaper has one name in every view'
S_={k:[] for k in ['id','label','papers','first','last','long','topic','off','n']};P_={k:[] for k in ['p','d','e','g','q']};checks=[];P_fd={}   # fd: filed days that differ from the printed day
for f in sorted(families,key=lambda f:(f['first_date'],-f['newspapers'],f['family_id'])):   # stories in date order, so a stretch of years is one slice
    fid=f['family_id'];apps=[]
    for a in apps_by[fid]:
        _,lccn,filed,ed,page=a['page_id'].split(':');apps.append((dnum(a['publication_date']),lccn,int(ed),int(page),a['seq'],dnum(filed)))
    apps.sort();r=topic_rows.get(fid);title=story_titles.get(fid,f['label'])
    for k,v in (('id',fid),('label',title if len(title)<=100 else title[:98].rstrip()+' …'),('papers',f['newspapers']),('first',dnum(f['first_date'])),('last',dnum(f['last_date'])),
                ('long',int(bool(f['long_running']))),('topic',lane_of[r['top_topic']] if r else -1),('off',len(P_['p'])),('n',len(apps))): S_[k].append(v)
    for d,lccn,ed,page,seq,fd in apps:
        if fd!=d: P_fd[str(len(P_['p']))]=fd
        P_['p'].append(pix[lccn]);P_['d'].append(d);P_['e'].append(ed);P_['g'].append(page);P_['q'].append(seq)
        checks.append(printing_checks.get((fid,seq),'-') if printing_checks else '-')
assert len(P_['p'])==sum(len(v) for v in apps_by.values()), 'the index holds every printing once'
index={'epoch':'1770-01-01','scan_base':f'https://huggingface.co/datasets/{DATASET}/resolve/{REV}/media/','papers':idx_papers,'stories':S_,'printings':{**P_,'c':''.join(checks),'fd':P_fd},
       'coverage':{'p':[pix[id_to_lccn[c['newspaper_id']]] for c in cov_all],'d':[dnum(c['publication_date']) for c in cov_all],
                   'pages':[c['observed_pages'] for c in cov_all],'issues':[c['observed_issues_editions'] for c in cov_all]}}
(years_dir/'index.json').write_text(json.dumps(index,ensure_ascii=False,separators=(',',':')),encoding='utf8')
# A stamp of the year files' contents (and the index), so browsers fetch fresh copies after a rebuild.
year_stamp=hashlib.sha256(b''.join(hashlib.sha256((years_dir/f'{y}.json').read_bytes()).digest() for y in range(1770,1811))+hashlib.sha256((years_dir/'index.json').read_bytes()).digest()).hexdigest()[:12]
boot={'release_version':VER,'reviewed':reviewed_list,'years':years_index,'year_stamp':year_stamp,'trace':trace_stamp,'twins':twins,'storylines':storyline_links,'index_bytes':(years_dir/'index.json').stat().st_size,
      # Topics for the story shelf's chips: each topic's plain name and family (as in the telescope).
      'topics':[{'label':SHORT[tid(x)],'family':fam_index[topic_labels[tid(x)]['category']]} for x in topic_list],
      'families':[{'short':s,'tiny':t} for f,s,t in FAMILIES]}
payload=json.dumps(boot,ensure_ascii=False).replace('</','<\\/')
html=(ROOT/'pulse_explorer.html').read_text(encoding='utf8').replace('__PULSE_DATA__',payload)
assert '__PULSE_DATA__' not in html
(OUT/'pulses.html').write_text(fill(html,'pulses',VER,N_STARS),encoding='utf8')
(OUT/'data.json').write_text(json.dumps({'release_version':VER,'reviewed':reviewed_list},ensure_ascii=False,indent=2),encoding='utf8')
# The radio: a year dial over the surviving papers of each year. It reads the year files and data.json, read aloud in the browser.
radio_boot={'release_version':VER,'year_stamp':year_stamp,'years':[{k:y[k] for k in ('year','papers','pages','matched','reviewed')} for y in years_index],
            'reviewed_years':sorted(reviewed_data)}
radio=(ROOT/'radio.html').read_text(encoding='utf8').replace('__RADIO_DATA__',json.dumps(radio_boot,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
assert '__RADIO_DATA__' not in radio
(OUT/'radio.html').write_text(fill(radio,'radio',VER,N_STARS),encoding='utf8')

# Stories the exhibition opens (Home is written below, once the findings, the notebook and the storylines are ready).
by_id={s['id']:s for s in stars}
peace=by_id['group:peace-and-plenty-boarding']
decl=by_id['group:declaration-of-independence']   # reviewed in data release v0.7.0
day_text=lambda d:datetime.date.fromordinal(EPOCH+d).strftime('%d %B %Y').lstrip('0')
assert day_text(decl['first'])=='6 July 1776', 'The exhibition says the Declaration was first printed two days after it was adopted'
pulse_link=lambda s:f"pulses.html?year={s['year']}&focus={quote(s['id'] if s['kind'] else 'auto:'+s['id'])}"

# Exhibition: a self-running loop of scenes, each a page in its exhibition mode (?exhibit=1), for a large screen.
# The scenes follow docs/site-plan.md (phase 2); each links to the same view on the web for the QR code.
from site_parts import PAGES
fever_q,july_q='yellow fever, malignant fever, prevailing fever','anniversary of independence, fourth of july, 4th of july'
exhibit_scenes=[
  {'title':f'A sky of {N_STARS:,} stories','seconds':75,
   'text':'Every story printed in at least two newspapers of this archive, 1770–1810. Each star sits where its story was first printed. Time runs into the distance: the front is now, and the further away a star is, the earlier the story.',
   'url':'telescope.html?exhibit=1&view=place&lookback=10&year=1780&drift=on','link':'telescope.html?view=place&lookback=10&year=1780'},
  {'title':'A privateer boards the Peace and Plenty','seconds':60,
   'text':"Captain Dunbar's account of a French privateer boarding his brig, printed in three papers in 1797 and retold in a fourth. Each pulse is one newspaper printing it on its date; every printing was checked against its scan.",
   'url':pulse_link(peace)+'&exhibit=1&speed=7&radio=on','link':pulse_link(peace)},
  {'title':'The Declaration of Independence','seconds':60,
   'text':f"First printed in this archive on {day_text(decl['first'])}, two days after Congress adopted it, and in {decl['papers']} papers by {day_text(decl['last'])[:-5]}. The radio reads the first printing.",
   'url':pulse_link(decl)+'&exhibit=1&speed=7&radio=on','link':pulse_link(decl)},
  {'title':'Some news returns with the seasons','seconds':60,
   'text':'Independence Day in amber, fever in blue. Time of year runs around the ring, and each turn of the spiral is a year; the coloured lines show the months. The Fourth of July comes back every summer, and fever reports cluster in late summer.',
   'url':f"telescope.html?exhibit=1&view=orbit&lookback=all&colour=search&drift=off&q={quote(july_q+' vs '+fever_q)}",'link':f"telescope.html?view=orbit&lookback=all&q={quote(july_q+' vs '+fever_q)}"},
  {'title':'What the papers talked about','seconds':55,
   'text':"The same stars arranged by topic and seen from the side: each wedge is one topic of the project's topic model, and time runs from the front to the back.",
   'url':'telescope.html?exhibit=1&view=topic&angle=side&lookback=10&year=1800&drift=on','link':'telescope.html?view=topic&angle=side&lookback=10&year=1800'},
  {'title':'What is missing','seconds':45,
   'text':'Only two newspaper series survive for 1785–86, against 11 to 17 a year after 1800. A thin sky is a gap in the surviving archive, not silence in the towns.',
   'url':'telescope.html?exhibit=1&view=place&lookback=5&year=1789&drift=off','link':'telescope.html?view=place&lookback=5&year=1789'},
  {'title':'The radio: a morning in 1776','seconds':120,
   'text':'Any day from 1770 to 1810, read aloud: a greeting to the town, then what its newspapers printed that morning. The voices are recorded and modern; the sounds are atmosphere, not recordings of the time.',
   'url':'radio.html?exhibit=1&year=1776&date=07-06&on=1','link':'radio.html?year=1776&date=07-06'}]
assert all(y['papers'] for y in years_index if y['year'] in (1780,1789,1800)), 'every exhibition year has surviving papers'
exhibit=(ROOT/'exhibit.html').read_text(encoding='utf8').replace('__EXHIBIT_DATA__',json.dumps({'pages':PAGES,'scenes':exhibit_scenes},ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
assert '__EXHIBIT_DATA__' not in exhibit
(OUT/'exhibit.html').write_text(fill(exhibit,'exhibit',VER,N_STARS),encoding='utf8')

# How it works and Research notes.
fill_text=lambda s:(s.replace('__N_STORIES__',f'{N_STARS:,}').replace('__N_MATCHED__',f'{len(families):,}')
                     .replace('__N_PRINTINGS__',f"{sum(f['appearances'] for f in families):,}").replace('__RELEASE__',VER).replace('__REPO__',REPO)
                     # the twins sentence on How it works: reviewed stories, how many have an automatic twin, how many matched
                     # stories are the twin of more than one, and how many stars the sky would hold without drawing twins once
                     .replace('__N_ELIGIBLE__',f"{manifest['counts']['eligible_pages']:,}")   # the release's usable pages
                     .replace('__N_REVIEWED__',f'{len(stories):,}').replace('__N_TWINNED__',f'{len(paired):,}')
                     .replace('__N_TWINS_SHARED__',f'{sum(n>1 for n in twin_of.values()):,}').replace('__N_ALL_STARS__',f'{len(families)+len(stories):,}')
                     # the items the reviews read and did not admit (work/not_admitted.py), one row each
                     .replace('__N_NOT_ADMITTED__',f"{len((ROOT.parent/'outputs/not_admitted/not_admitted.csv').read_text(encoding='utf8').splitlines())-1:,}"))
# How it works ends with an appendix of what was handled differently (work/appendix.json, work/appendix_parts.py): each
# printing is checked against the release and shown by its printed date, with a link to its page scan.
import appendix_parts
appendix=json.loads((ROOT/'appendix.json').read_text(encoding='utf8'))
with sqlite3.connect(verified_file('research.sqlite',release).as_uri()+'?mode=ro',uri=True) as db5:
    _one=lambda sql,args:(lambda r:r[0] if r else None)(db5.execute(sql,args).fetchone())
    page_date=lambda key:_one('SELECT i.publication_date FROM pages p JOIN issues i ON i.id=p.issue_id WHERE p.id=?',('page:'+key.replace('|',':'),))
    n_appendix=appendix_parts.check(appendix,page_date,lambda g:_one('SELECT label FROM groups WHERE id=?',('group:'+g,)),
                                    lambda g,y:_one('SELECT COUNT(*) FROM group_publications WHERE group_id=? AND publication_date LIKE ?',('group:'+g,f'{y}%')))
    appendix_html=appendix_parts.render(appendix,page_date,{p['lccn']:p['name'] for p in idx_papers},f'https://huggingface.co/datasets/{DATASET}/resolve/{REV}/media/')
# The three diagrams on How it works (work/method_diagrams.py), drawn from this build's numbers as Findings' charts are.
# Diagram 2 draws one example word for word; if a review or a correction changes it, the build stops here and says what.
import csv, method_diagrams
na_kinds=collections.Counter(r['kind'] for r in csv.DictReader(open(ROOT.parent/'outputs/not_admitted/not_admitted.csv',encoding='utf8',newline='')))
ex_obs=[observations[m] for s in stories if s['id']==method_diagrams.EXAMPLE_STORY for m in s['members']]
ex_problem=method_diagrams.check_example([(o['node'],o['date']) for o in ex_obs],twins.get(method_diagrams.EXAMPLE_TWIN),
    sum(method_diagrams.EXAMPLE_TWIN in page_owner.get((o['node'],o['date'],int(o['page'])),()) for o in ex_obs),[a for o in ex_obs for a in o['scans']])
assert not ex_problem,ex_problem
diagrams=method_diagrams.render({'pages':manifest['counts']['pages'],'newspapers':manifest['counts']['newspapers'],'issues':manifest['counts']['issues'],
    'eligible':manifest['counts']['eligible_pages'],'matched':len(families),'matched_printings':sum(f['appearances'] for f in families),
    'reviewed':len(stories),'reviewed_printings':len(observations),'reviewed_years':len(reviewed_list),'twinned':len(paired),'twins':len(twins),
    'stars':N_STARS,'parts':sum(len(d['groups']) for d in reviewed_list)-len(stories),'kinds':dict(na_kinds)})
method_src=(ROOT/'method.html').read_text(encoding='utf8')
for key,part in {'__DIAGRAMS_CSS__':diagrams['css'],'__DIAGRAM_PAGE_TO_STAR__':diagrams['page_to_star'],'__DIAGRAM_YEAR__':diagrams['year'],'__DIAGRAM_STORY__':diagrams['story']}.items():
    assert method_src.count(key)==1,'method.html needs '+key+' once'; method_src=method_src.replace(key,part)
method_page=fill_text(method_src).replace('__APPENDIX__',appendix_html)
assert '__APPENDIX__' not in method_page and n_appendix==12, ('appendix', n_appendix)
(OUT/'method.html').write_text(fill(method_page,'method',VER,N_STARS),encoding='utf8')
(OUT/'notes.html').write_text(fill(fill_text((ROOT/'notes.html').read_text(encoding='utf8')),'notes',VER,N_STARS),encoding='utf8')
# Findings: what the archive shows, tested (work/findings_parts.py). Drawn from the sky's stars, the year index, the
# Declaration's printings and the checks' outputs: the matched audit and the cycle-length check (run work/check_cycle_lengths.py
# after a new release; without its output the page leaves that finding out and says so here).
import findings_parts
decl_story=next(s for s in stories if s['id']=='group:declaration-of-independence')
cycles_file=ROOT.parent/'outputs/story_discovery_all/cycle_lengths.json'
if not cycles_file.exists(): print('findings: no cycle_lengths.json (run work/check_cycle_lengths.py); finding 6 is left out')
findings_html=findings_parts.render(years=[(y['year'],y['papers'],y['pages']) for y in years_index],stars=stars,
    decl_printings=[(paper_name[o['node']],o['date'],towns[o['node']]['place'],towns[o['node']]['lat'],towns[o['node']]['lon']) for o in (observations[m] for m in decl_story['members'])],
    audit=json.loads((ROOT.parent/'outputs/matched_audit/summary.json').read_text(encoding='utf8')),
    cycles=json.loads(cycles_file.read_text(encoding='utf8')) if cycles_file.exists() else None,repo=REPO)
# What we found wrong in the archive itself (work/archive_errata.py, which reads this build's data.json: after a new
# reviewed year, build, run it, and build again). Without its summary the page leaves the section out and says so here.
errata_file=ROOT.parent/'outputs/archive_errata/summary.json'
errata=json.loads(errata_file.read_text(encoding='utf8')) if errata_file.exists() else None
if not errata: print('findings: no archive_errata/summary.json (run work/archive_errata.py); the archive section is left out')
findings_page=(ROOT/'findings.html').read_text(encoding='utf8').replace('__FINDINGS__',findings_html).replace('__ARCHIVE__',findings_parts.archive(errata,REPO) if errata else '')
if not errata: findings_page=findings_page.replace('<li><a href="#archive">What we found wrong in the archive</a></li>','')
(OUT/'findings.html').write_text(fill(fill_text(findings_page),'findings',VER,N_STARS),encoding='utf8')
# Notebook: how the project was made, from the ledger work/notebook.json (work/notebook_parts.py checks every entry first).
import notebook_parts
notebook=json.loads((ROOT/'notebook.json').read_text(encoding='utf8'))
n_notebook=notebook_parts.check(notebook,{'index.html','telescope.html','pulses.html','radio.html','stories.html','method.html','notes.html','findings.html','exhibit.html','notebook.html'})
(OUT/'notebook.html').write_text(fill(fill_text((ROOT/'notebook.html').read_text(encoding='utf8').replace('__NOTEBOOK__',notebook_parts.render(notebook))),'notebook',VER,N_STARS),encoding='utf8')
print(f'notebook: {n_notebook} entries')
# Stories: the storylines checked above, each piece's opening beside its scan crop (the crops are already in assets/).
from PIL import Image
stories_html=stories_parts.render(storylines,lambda src:Image.open(OUT/src).size)
(OUT/'stories.html').write_text(fill(fill_text((ROOT/'stories.html').read_text(encoding='utf8').replace('__STORIES__',stories_html)),'stories',VER,N_STARS),encoding='utf8')
# Home (work/home_parts.py): the question, three facts about the source, the findings as ready views, a storyline and the
# notebook; and a sample of stars for the hero sky, drawn by the page itself.
import home_parts
per_year_stories,thin_years=findings_parts.year_counts(stars)
home_html=home_parts.render(years=[(y['year'],y['papers'],y['pages']) for y in years_index],thin=thin_years,newspapers=manifest['counts']['newspapers'],
    pages=manifest['counts']['eligible_pages'],matched=len(families),reviewed=len(stories),reviewed_years=sorted(reviewed_data),
    audit=json.loads((ROOT.parent/'outputs/matched_audit/summary.json').read_text(encoding='utf8')),findings=findings_parts.SUMMARY,
    storyline=storylines[0] if storylines else None,notebook_entries=n_notebook)
assert len([f for f in findings_parts.SUMMARY if f[0]>2])>=4, 'Home offers the findings as ready views'
sample=sorted((s for s in stars if not s['long']),key=lambda s:(-s['papers'],-s['prints'],s['first']))[:4500]
sample.sort(key=lambda s:s['first'])
palette=['rgba(170,182,207,A)','rgba(57,135,229,A)','rgba(217,89,38,A)','rgba(25,158,112,A)']
home_data={'towns':tele_boot['towns'],'palette':palette,
           'sky':{'day':[s['first'] for s in sample],'lat':[s['flat'] for s in sample],'lon':[s['flon'] for s in sample],'papers':[s['papers'] for s in sample],
                  'color':[tele_cats[s['cat']]['slot']+1 if s['kind'] else 0 for s in sample]}}
home=(ROOT/'home.html').read_text(encoding='utf8').replace('__HOME_DATA__',json.dumps(home_data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
home=home.replace('__HOME__',home_html).replace('__N_STORIES__',f'{N_STARS:,}')
(OUT/'index.html').write_text(fill(home,'home',VER,N_STARS),encoding='utf8')
def copy_with_assets(src,dest):
    """Copy a report and the local files it links to (images, data), keeping their relative paths.
    The site is English only, so links to Chinese quick-read files are dropped from the copy."""
    dest.mkdir(parents=True,exist_ok=True)
    page=re.sub(r'\s*·\s*<a href="[^"]*\.zh-CN\.md">[^<]*</a>','',src.read_text(encoding='utf8'))
    (dest/src.name).write_text(page,encoding='utf8')
    for ref in set(re.findall(r'(?:src|href)="([^"#?]+)"',page)):
        if re.match(r'^(?:[a-z]+:|//)',ref) or '.zh-CN.' in ref: continue
        f=src.parent/ref
        if f.is_file(): (dest/ref).parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(f,dest/ref)
shutil.rmtree(OUT/'notes',ignore_errors=True)   # notes/ is generated: start clean, so no stale file lingers
copy_with_assets(ROOT.parent/'outputs/attention_pilot_report.html',OUT/'notes/attention')
copy_with_assets(ROOT.parent/'outputs/reading_evidence_2026-11-03/reading_notebook.html',OUT/'notes/reading')
for leftover in [m for m in ['__N_STORIES__','__N_MATCHED__','__N_PRINTINGS__','__N_REVIEWED__','__N_TWINNED__','__N_TWINS_SHARED__','__N_ALL_STARS__','__N_NOT_ADMITTED__','__N_ELIGIBLE__','__RELEASE__','__REPO__','__HOME_DATA__','__HOME__','__ARCHIVE__']
                 for page in ['index.html','method.html','notes.html','findings.html','notebook.html','stories.html'] if m in (OUT/page).read_text(encoding='utf8')]:
    raise AssertionError('Unfilled placeholder '+leftover)
assert '__FINDINGS__' not in (OUT/'findings.html').read_text(encoding='utf8') and '__NOTEBOOK__' not in (OUT/'notebook.html').read_text(encoding='utf8')
assert '__STORIES__' not in (OUT/'stories.html').read_text(encoding='utf8')

pages={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['index.html','telescope.html','pulses.html','radio.html','stories.html','exhibit.html','method.html','notes.html','findings.html','notebook.html','site.css','glass.js','radio.js','music.js']}
# The radio's recorded voices (work/audio_render.py writes audio/ next to the pages; this build leaves it alone). Report
# how many reviewed passages have a recording; a passage without one is read by the browser's voice on the Radio page, and introduced by the announcer elsewhere.
audio_summary=None
if (OUT/'audio'/'index.json').exists():
    ai=json.loads((OUT/'audio'/'index.json').read_text(encoding='utf8')); clips=ai.get('clips',{})
    obs_ids=[o['id'] for d in reviewed_list for o in d['observations']]
    audio_summary={'clips':len(clips),'packs':len(ai.get('packs',[])),'mb':round(sum(f.stat().st_size for f in (OUT/'audio').rglob('*.mp3'))/1e6,1),
                   'reviewed_passages_recorded':sum(('p:'+i) in clips for i in obs_ids),'reviewed_passages':len(obs_ids),
                   'titles_recorded':sum(k.startswith('t:') for k in clips),'announcer_clips':sum(k.startswith('a:') for k in clips)}
receipt={'passed':True,'release_version':VER,
         'reviewed_years':[{'year':y,'newspapers':len(d['newspapers']),'passages':len(d['observations']),'group_views':len(d['groups']),'stories':len(d['stories']),'categories':len(d['categories'])} for y,d in sorted(reviewed_data.items())],
         'curated_passages':len(observations),'group_views':sum(len(d['groups']) for d in reviewed_list),'stories_in_overview':len(stories),'overview_categories':len(tele_cats),
         'years':len(years_index),'matched_families':len(families),'reviewed_twins':len(twins),'sky_stars':len(stars),'trace_words':len(trace_words),'trace_stories':trace_cover,'year_files_mb':round(sum((years_dir/f'{y}.json').stat().st_size for y in range(1770,1811))/1e6,1),'year_index_mb':round((years_dir/'index.json').stat().st_size/1e6,1),'telescope_stars':len(stars),'telescope_mb':round((OUT/'telescope.json').stat().st_size/1e6,1),'telescope_text_mb':round((OUT/'telescope-text.json').stat().st_size/1e6,1),'story_topic_lanes':len(topic_list),'edges':0,
         'checks':['All displayed sources have scan assets and excerpts','All displayed publications join to observed date coverage','No duplicate observation within a group','Read-only release with verified input hashes','Matched families are labelled as not checked against scans','Every page carries the shared header and footer',
                   'Each reviewed year lists every one of its groups once, and every top-level story has a display category']
                  +(['Every matched printing carries its transcription check, one printing per page'] if printing_checks else [])
                  +(['Every storyline quotes printed text: each opening is from a printing the scan check found faithful, and every quoted phrase is in a printing, its group or its scan verdict'] if storylines else []),
         'matched_printings':sum(len(v) for v in apps_by.values()),
         'storylines':[{'id':s['id'],'year':s['year'],'pieces':len(s['by']),'printings':len(s['every']),'newspapers':len({o['node'] for o in s['every']})} for s in storylines],
         'recorded_voices':audio_summary,
         'pages_sha256':pages}
(OUT/'build_validation.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps(receipt,indent=2))
