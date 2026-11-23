# Items read and not admitted

The reviews read the widely printed items of each reviewed year and admitted those that meet the year's rule. This list holds every item a review read and did not admit, each with its reason, so that no part of the archive drops out of view.

- The candidates came from the automatic families, so most of these items stay in the sky as matched stars; only the reviewed label is withheld.
- 1797 was read on 6 November 2026, before the one rule existed, so its stories reach 2 to 5 papers and its list is of a different kind (see 1797 below).
- Since 11 November 2026 every item is counted by the same rule whatever its subject. Items once held back for framing were read again by that rule; those that reach it are admitted, and the others are listed here with the rest.
- Items that turn on private persons are described without names.
- An item that a later round admitted is not listed. `pipeline/not_admitted.json` records it under `accounted`, with the ledger and the group.
- **Papers** is the number of newspapers that printed the item, as the review counted it. **Source** is the ledger key it comes from (`stories_YEAR.json#section/key`, in `pipeline/archive_data/ledgers/`) or a section of the year's review notes (`story_discovery_YEAR/README.md#heading/phrase`), which are kept with the project's working files.

`pipeline/not_admitted.py` writes this page and `not_admitted.csv` (the same list) from `pipeline/not_admitted.json`. It checks that every key of `not_admitted`, `for_the_owner` and `for_user_decision` in every ledger is listed here or accounted for, and that every family of 1797 that was read is admitted or listed.

## Counts

| Year | Items | Below the rule | Not chosen | Digests, lists, proceedings | Private persons | Other |
|---|---:|---:|---:|---:|---:|---:|
| [1776](#1776) | 26 | 8 | 4 | 1 | 1 | 12 |
| [1793](#1793) | 43 | 39 | 2 | 0 | 2 | 0 |
| [1797](#1797) | 37 | 0 | 0 | 0 | 0 | 37 |
| [1805](#1805) | 35 | 14 | 14 | 1 | 6 | 0 |
| [1806](#1806) | 56 | 11 | 34 | 2 | 7 | 2 |
| [1807](#1807) | 27 | 13 | 10 | 2 | 0 | 2 |
| [1808](#1808) | 27 | 17 | 5 | 4 | 0 | 1 |
| [1809](#1809) | 32 | 16 | 11 | 4 | 1 | 0 |
| **All years** | **283** | **118** | **80** | **14** | **17** | **54** |

**Kinds.** *Below the rule*: counted by its own words, the item is in fewer papers than the year's rule. *Not chosen*: it reaches the rule, but its months and kind of news were already covered. *Digests, lists and proceedings*: not one printed item. *Private persons*: it turns on private persons. *Other*: a different item from the one admitted, a quotation, or another reason given.

Besides these, `pipeline/not_admitted.json` holds 49 records for ledger keys, or parts of keys, that are not items left out: 32 items that a later round admitted, 11 repeats of an item listed from another key, 4 counting decisions about admitted stories and 2 notes on admitted stories.

## 1776

An item printed in 9 or more papers is admitted, except digests; items in 7 or 8 papers are chosen to cover the months and the kinds of news.

### Below the rule (8)

- **Congress's resolutions of 23 March on privateering.** Papers: 6. An earlier document that shares wording with the resolution of 24 July, in 6 papers. Source: `stories_1776.json#not_admitted/Congress's privateering resolutions of 23 March (PEP 03-26, PG 03-27, NYP 04-04, VGa 04-13, VGb 04-19, NEC 05-02)`
- **A London paragraph on deserters from the Cork regiments.** Papers: 5. A one-sentence paragraph in 5 papers: the finder's 8 came from neighbouring paragraphs, and the New-York Gazette of 5 February prints a different report. Source: `stories_1776_round2.json#not_admitted/Deserters from the Cork regiments (PG 01-31, PL 02-03, PP 02-05, VGb 02-16, VGa 02-17)`
- **A London report of the Prohibitory bill's second reading, 1 December 1775.** Papers: 3. A different report, on a different clause, in 3 papers. Source: `stories_1776_round2.json#not_admitted/Another London report on the Prohibitory bill (NYP 03-07, VGb 03-15, VGa 03-16)`
- **A Philadelphia letter of 11 April on the capture of the Edward.** Papers: 1. A different report of the same capture, in 1 paper. Source: `stories_1776_round2.json#not_admitted/A Philadelphia letter of 11 April on the Edward (NEC 04-25 p3)`
- **The Howes' joint declaration of 14 July.** Papers: 1. Printed in the New-York Gazette only, and its text is that of Lord Howe's June declaration, which the story holds. Source: `stories_1776_round2.json#not_admitted/The Howes' joint declaration of 14 July (NYG 09-30 and 10-07)`
- **A satirical rewriting of the Howes' September declaration, with 'the King's Commissioners for deluding the good people of America'.** Papers: 4. Commentary, not the declaration, in 4 papers. Source: `stories_1776_round2.json#not_admitted/A parody of the September declaration (PG 10-02, VGa 10-25, VGb 10-25, FJ 10-29)`
- **The Howes' proclamation of 30 November.** Papers: 1. One paper in this collection, the Freeman's Journal. Source: `stories_1776_round2.json#not_admitted/The Howes' proclamation of 30 November (FJ 12-24)`
- **The London notice of the Howes' commission, with the letters patent of 3 May.** Papers: 6. A different document from the declarations, in 6 papers. Source: `stories_1776_round2.json#not_admitted/The London notice of the Howes' commission (PJ 07-31, PEP 08-01, PP 08-05, NEC 08-08, FJ 08-10, VGb 08-16)`

### Not chosen: month and kind covered (4)

- **Letters from Fincastle of late July.** Papers: 7. Read in round one among the items in 7 or more papers and not chosen, like other 7- and 8-paper items. Source: `stories_1776_round3.json#not_admitted/Other reports of the southern frontier in 7 papers (not held back for framing)`
- **An express on the relief of the Watauga fort.** Papers: 7. Read in round one among the items in 7 or more papers and not chosen, like other 7- and 8-paper items. Source: `stories_1776_round3.json#not_admitted/Other reports of the southern frontier in 7 papers (not held back for framing)`
- **A September paragraph of letters from the south on the war against the lower towns.** Papers: 7. Read in round one among the items in 7 or more papers and not chosen, like other 7- and 8-paper items. Source: `stories_1776_round3.json#not_admitted/Other reports of the southern frontier in 7 papers (not held back for framing)`
- **Other documents in 7 or 8 papers that round one read and did not choose, not recorded one by one.** Papers: 7 or 8 each. Round one read 101 documents in 7 or more papers and listed only some of those it did not choose; they can be read again in a later round. Source: `story_discovery_1776/README.md#Candidates for a later round/with the other 7- and 8-paper items round one did not choose`

### Digests, lists and proceedings (1)

- **A digest of London and Halifax news, printed in pieces (matched family R1776-0003).** Papers: 13. Several unrelated paragraphs, not one printed item. Source: `stories_1776.json#not_admitted/London and Halifax news digest (R1776-0003, 13 papers)`

### Private persons (1)

- **Notices of the Philadelphia and Gloucester County committees of inspection that quote Congress's resolution on the bills of credit and publish the names of people the committees said had refused the bills.** Papers: 18 printings in 5 papers. Separate documents that publish the names of private persons, left out by the owner's decision of 9 November 2026. Source: `stories_1776_round2.json#not_admitted/Committee of inspection notices under the bills-of-credit resolution (PJ 02-07 to PJ 04-24; 18 printings in 5 Philadelphia papers)`

### Other (12)

- **Parliament's address in answer to the King's speech of October 1775.** Papers: 4. A different document that repeats the speech's words, so it is not a printing of the speech. Source: `stories_1776.json#not_admitted/VGa 1776-02-03 p2, PG 02-07 p2, NYP 02-08 p1, PP 02-12 p4`
- **Other reports from before Quebec on the batteries at Point Levy.** Papers: 4. Different reports, not the letter written in the camp on 6 April that the story holds. Source: `stories_1776.json#not_admitted/PJ 1776-05-01 p2, PEP 05-02 p3, PL 05-04 p2, NEC 05-16 p3`
- **The inventory of stores taken at New Providence, printed apart from Hopkins's letter.** Papers: 2. A separate document from Hopkins's letter, in 2 papers. Source: `stories_1776.json#not_admitted/PEP 1776-04-18 p2, NEC 04-25 p1`
- **Purdie's Virginia Gazette, 17 May: the London paragraphs from the Dublin paper, without its report of the naval force.** Papers: 1. It does not print the report that the story holds. Source: `stories_1776.json#not_admitted/VGb 1776-05-17 p2`
- **The Freeman's Journal, 8 June, page 2: a paraphrase of Congress's resolution of 15 May inside another item.** Papers: 1. The same issue prints the full text on page 4, and that printing is counted. Source: `stories_1776.json#not_admitted/FJ 1776-06-08 p2`
- **The New-York Gazette, 8 July: a report of Congress's vote for independence.** Papers: 1. A different item, not a printing of the Virginia Convention's resolutions. Source: `stories_1776.json#not_admitted/NYG 1776-07-08 p3`
- **Commentary quoting the preamble of Pennsylvania's new instructions (Dunlap's Pennsylvania Packet, 24 June; Pennsylvania Gazette, 26 June).** Papers: 2. Commentary that quotes the instructions, not a printing of them. Source: `stories_1776.json#not_admitted/PP 1776-06-24 p2, PG 06-26 p1`
- **Another colony's instructions to its deputies (Pennsylvania Journal, 19 June; Dixon and Hunter's Virginia Gazette, 13 July).** Papers: 2. A different document that shares a phrase with Pennsylvania's instructions. Source: `stories_1776.json#not_admitted/PJ 1776-06-19 p3, VGa 07-13 p5`
- **The New-England Chronicle, 8 August: a notice that the account of Washington's meeting with Colonel Patterson had been published in the New-York papers.** Papers: 1. A notice, not the account, which the same paper printed on 15 August. Source: `stories_1776.json#not_admitted/NEC 1776-08-08 p3`
- **The notice of the Synod of New-York and Philadelphia moving its meeting because of Congress's fast.** Papers: 3. A different document from Congress's resolution on the fast. Source: `stories_1776_round2.json#not_admitted/The Synod's notice on the fast (NYG 04-22, PJ 04-24, PG 05-01 and repeats; 3 papers)`
- **Notices of other fast days in August 1776 (Massachusetts, 1 August; the Synod, 8 August).** Other fast days, not Congress's of 17 May. Source: `stories_1776_round2.json#not_admitted/Fasts of August 1776 (Massachusetts, 1 August; the Synod, 8 August)`
- **Advertisements of the sale of the sloop Edward.** Papers: 3. Advertisements, not Barry's letter. Source: `stories_1776_round2.json#not_admitted/The sale of the sloop Edward (PEP 04-30, PG 05-01, PJ 05-01)`

## 1793

A story needs one printed item in 6 or more papers, because few papers of 1793 survive; items in 6 are chosen as items in 7 or 8 are in other years.

### Below the rule (39)

- **A Lisbon letter of 8 February with 'a certainty of the execution of the King of France'.** Papers: 5. One of six different accounts of the King's sentence and death, none in more than 5 of the 6 papers then in print. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **The Convention's decree on the King's sentence, with the votes.** Papers: 5. One of six different accounts of the King's sentence and death, none in more than 5 of the 6 papers then in print. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **'The last requests of Louis'.** Papers: 5. One of six different accounts of the King's sentence and death, none in more than 5 of the 6 papers then in print. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **Two accounts of the execution of Louis XVI.** Papers: 4 each. Two of six different accounts of the King's sentence and death, none in more than 5 of the 6 papers then in print. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **The will of Louis XVI.** Papers: 4. One of six different accounts of the King's sentence and death, none in more than 5 of the 6 papers then in print. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **France's decree of war on Britain and Holland, 1 February.** Papers: 5. In 5 papers, below the year's rule of 6; the Kentucky Gazette does not print it. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **The French Republic's letter to the United States, 'Amidst the storms which buffet our infant liberty'.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **Mr. Giles's resolutions on the Secretary of the Treasury.** Papers: 5. In 5 papers as moved and as the House journal, below the year's rule of 6. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **The report of Washington's second inauguration, with the oath.** Papers: 4. In 4 papers; his short address is found only in the Gazette of the United States. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **The President's proclamation of neutrality, 22 April.** Papers: 4. Its text is in 4 papers; the Mirrour gives only a summary. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **The merchants' address thanking the President for the proclamation of neutrality.** Papers: 4. In 4 papers, below the year's rule of 6. Source: `story_discovery_1793/README.md#Not admitted/The merchants' address thanking the President`
- **Reports of Genêt's arrival and reception: the addresses to him and his answers.** Papers: 2 to 4 each. No item about his arrival and reception is in more than 4 papers. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **Reports of the yellow fever in Philadelphia: the College of Physicians' advice, the committee's orphan house and many local letters.** Papers: 3 or 4. No shared item is in more than 4 papers: each surviving paper told it in its own letters and paragraphs, and both Philadelphia papers stopped. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **Reports from Toulon, from November, in many different texts.** Papers: 4 or fewer. No item is in more than 4 papers. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **Reports that Marie Antoinette's trial was expected.** Papers: 4. In 4 papers, below the year's rule of 6; no page of 1793 in the collection reports her execution. Source: `story_discovery_1793/README.md#Not admitted/Marie Antoinette's execution`
- **The President's address of 3 December and his message of 5 December.** Papers: 4 each. Each is in 4 papers, every paper then in print, below the year's rule of 6. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **The consul Edward Church's circular from Lisbon: 'Nine Algerine Corsairs are now cruising'.** Papers: 3. In 3 papers at the end of December, when only 4 papers have pages. Source: `stories_1793.json#not_admitted/The 1793 news that no single item carries to 7 papers`
- **News from Ostend by the ship Fortitude.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **Jefferson's letter to the Philadelphia merchants on spoliations.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **A Paris report of Marat's funeral.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **The Convention's decree arresting foreigners, a paragraph of a news digest.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **The Prince of Saxe-Cobourg's proclamation of 9 April.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **A Philadelphia report that a party of militia was put on board the prize ship William.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **A report that Pitt wished to resign.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **A Charleston letter reporting that the body of Henry Laurens was burnt after his death.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **A report that Rome had surrendered.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **A Charleston report of a house of rendezvous opened for entering seamen for the French service.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **The Commune of Paris's call 'To arms'.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **A London report of Sir James Murray landing at Dover.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **An official account of the sortie from Cassel.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **A letter from Mons of 1 May.** Papers: 5. In 5 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **The revocation of the exequatur of the French vice-consul Duplaine.** Papers: 4. In 4 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **Genêt's answer on the revocation of Duplaine's exequatur.** Papers: 4. In 4 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **Dumouriez's letter from Louvain.** Papers: 4. In 4 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **Dumouriez's declaration at Frankfort.** Papers: 4. In 4 papers, below the year's rule of 6. Source: `stories_1793.json#not_admitted/Below 6 papers`
- **A ship captain's report that Dumouriez 'had got possession of Amsterdam'.** Papers: 4 + 2 in two wordings. Printed in two different wordings, so no single item reaches 6 papers. Source: `stories_1793_round2.json#not_admitted/Not recommended at 6 papers`
- **The French civil commissioners' proclamation of 21 June, giving liberty to 'the negro warriors, who will fight for the republic'.** Papers: 4. In 4 papers, below the year's rule of 6, and not a sub-story, as for the 4-paper documents of Dumouriez's defection. Source: `stories_1793_round3.json#not_admitted/The civil commissioners' proclamation of 21 June`
- **The letter of the commissioners Polverel and Sonthonax to Genêt.** Papers: 4. In 4 papers, below the year's rule of 6. Source: `stories_1793_round3.json#not_admitted/The letter of Polverel and Sonthonax to Genêt`
- **'An act respecting fugitives from justice, and persons escaping from the service of their masters', 12 February.** Papers: 2. Its text is in 2 papers; its title in the lists of the session's acts is a different item. Source: `stories_1793_round3.json#not_admitted/The Fugitive Slave Act`

### Not chosen: month and kind covered (2)

- **A Rome paragraph of 29 September 1792.** Papers: 6. A single paragraph of a news digest, in a month already covered. Source: `stories_1793_round2.json#not_admitted/Not recommended at 6 papers`
- **A Paris paragraph on the city 'in sullen tranquillity'.** Papers: 6. A single paragraph of a news digest, in a month already covered. Source: `stories_1793_round2.json#not_admitted/Not recommended at 6 papers`

### Private persons (2)

- **Reports of the prosecutions of two seamen for serving on a French privateer.** Papers: 5. In 5 papers, below the year's rule of 6, and it turns on private persons. Source: `stories_1793_round3.json#not_admitted/Private people (5 papers each)`
- **A report of a killing near Middletown, New Jersey.** Papers: 5. In 5 papers, below the year's rule of 6, and it turns on private persons. Source: `stories_1793_round3.json#not_admitted/Private people (5 papers each)`

## 1797

Read on 6 November 2026, before the one rule: candidate families of 3 to 5 papers were read and some were chosen, and its stories reach 2 to 5 papers; it has not yet been read by the one rule. Its list holds the pages set aside while counting its stories, and the candidate families read and not chosen.

### Other (37)

- **The Gazette of the United States, 5 and 12 June: pages that quote phrases of President Adams's speech to the special session.** Papers: 1 (2 pages). They quote the speech but do not print it; the House's answer on the page of 5 June was admitted in round two. Source: `stories_1797.json#not_admitted/F97-005 Gazette of the United States 5 and 12 June`
- **Other accounts from Tenerife, with texts different from the Norfolk report.** Papers: 3 (6 pages). Different texts, not printings of the report the story holds. Source: `stories_1797.json#not_admitted/Tenerife: GUS 30 Aug, GUS 5 Sep, NH 12 Sep, NH 1 Nov, GUS 14 Nov, KY 25 Nov`
- **Other pages naming Admiral Duncan and Admiral De Winter: first reports, the notice of Duncan's peerage and other items.** Not printings of Duncan's dispatches, which the story holds. Source: `stories_1797.json#not_admitted/Camperdown: other 'Admiral Duncan' and 'De Winter' pages`
- **Other pages on Senator Blount's affair from July: a committee report, the Senate's vote to expel him, documents and debate.** Papers: 3, and later pages. Items on the wider affair, not printings of Blount's letter. Source: `stories_1797.json#not_admitted/Blount: GUS 7 and 10 July, NH 18 July p1, KY 29 July p3 and later pages`
- **Other pages of the New Hampshire Gazette naming the master of the brig Brothers: ship arrivals and advertisements.** Papers: 1. Ship arrivals and advertisements, not his report. Source: `stories_1797.json#not_admitted/Kennard: other NH pages`
- **The Gazette of the United States, 7 June, page 2, found with the answers to the President's speech.** Papers: 1. The answer's text is not on this page. Source: `stories_1797_round2.json#not_admitted/GUS 1797-06-07 p2 (F97-025)`
- **The Gazette of the United States, 25 October, page 3: a list of ship arrivals naming the sloop Cleopatra.** Papers: 1. A ship list, not the Charleston report of American vessels carried into Havana. Source: `stories_1797_round2.json#not_admitted/GUS 1797-10-25 p3`
- **Other pages on General Kościuszko, and New York reports on a physician taken into custody in the Blount affair.** Different items about the same people. Source: `stories_1797_round2.json#not_admitted/other Kosciuszko and Romayne pages`
- **A Vienna letter on the peace talks between Austria and France (the Marquis de Gallo's conferences, Mantua, the Cisalpine Republic).** Papers: 5. Read as a candidate family on 6 November and not shortlisted. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-002`
- **The Secretary of State's reply to the French minister Adet's complaints, printed in instalments over many issues.** Papers: 4. Held for later: a document printed in parts over about 30 pages needs handling by instalment. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-003`
- **Letters between the Spanish minister Yrujo and the Secretary of State on the boundary posts.** Papers: 4. Held for later as a set of several letters. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-004`
- **The French Directory's proclamation to the French nation after 18 Fructidor.** Papers: 4. Read as a candidate family on 6 November and not shortlisted. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-006`
- **News from the Isle of France and India: French frigates and privateers cruising.** Papers: 4. Read as a candidate family on 6 November and not shortlisted. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-008`
- **A printer's notice of the editions of the Bible from his press.** Papers: 4. Read as a candidate family on 6 November and not shortlisted. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-009`
- **The French Directory's message to the Councils on a deficit.** Papers: 4. Read as a candidate family on 6 November and not shortlisted. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-012`
- **Reports of French troops moving to Brest, with doubts about the talks at Lille.** Papers: 4. Read as a candidate family on 6 November and not shortlisted. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-015`
- **A Paris comment on the negotiations with the English government.** Papers: 4. Read as a candidate family on 6 November and not shortlisted. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-016`
- **Reports that Hoche was named generalissimo of the armies of the Rhine, with letters from Milan.** Papers: 4. Read as a candidate family on 6 November and not shortlisted. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-017`
- **Reports on the negotiations at Lille and the Portuguese envoy.** Papers: 4. Read as a candidate family on 6 November and not shortlisted. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-018`
- **A letter from Providence, dated September: its writer's account of a 'conspiracy' among 'French negroes' who had been 'captured and sold here'.** Papers: 4. Not shortlisted on 6 November, when it was set aside for careful framing; the rule 'every story alike' later dropped that reason, and 1797 has not been read again. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-019`
- **News from Brest and Algiers, January to March.** Papers: 4. Read as a candidate family on 6 November and not shortlisted. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-020`
- **Reports from Hamburg papers on the sieges of Kehl and Huningen.** Papers: 4. Read as a candidate family on 6 November and not shortlisted. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-021`
- **The Archduke Charles's dispatch on General Moreau's retreat across the Rhine.** Papers: 4. Read as a candidate family on 6 November and not shortlisted. Source: `story_discovery_1797/README.md#The 23 families that reach 4–5 newspapers/F97-023`
- **A report of the examination of a man charged with fitting out a vessel to cruise against a nation at peace with the United States.** Papers: 3. Noted on 6 November as a smaller shipping story and not recommended. Source: `story_discovery_1797/README.md#Noted but not recommended now/(055)`
- **A ship captain's report of his schooner's capture by a French privateer.** Papers: 3. Noted on 6 November as a smaller shipping story and not recommended. Source: `story_discovery_1797/README.md#Noted but not recommended now/(067)`
- **A report on an American vessel carried into Portsmouth with arms on board.** Papers: 3. Noted on 6 November as a smaller shipping story and not recommended. Source: `story_discovery_1797/README.md#Noted but not recommended now/(070)`
- **A shipmaster's report that the cargo of the schooner Jane was taken at Cape François.** Papers: 3. Noted on 6 November as a smaller shipping story and not recommended. Source: `story_discovery_1797/README.md#Noted but not recommended now/(071)`
- **Letters and a statement of James Monroe on his recall, with the Secretary of State's letters.** Papers: 3 each. Noted on 6 November as a set of documents and not recommended. Source: `story_discovery_1797/README.md#Noted but not recommended now/the Monroe controversy (029, 036)`
- **Papers on the Spanish boundary and a suspected expedition from the lakes: the President's message, a Spanish proclamation at New Orleans and the Secretary of State's note.** Papers: 3 each. Noted on 6 November as a set of documents and not recommended. Source: `story_discovery_1797/README.md#Noted but not recommended now/(047, 051, 054)`
- **An Albany paper's report at second hand that British troops and Indians headed by Colonel Brant had marched towards the Mississippi.** Papers: 3. Noted on 6 November as a frontier report and not recommended. Source: `story_discovery_1797/README.md#Noted but not recommended now/Brant (116)`
- **A frontier paragraph reporting a killing on Beaver Creek.** Papers: 3. Noted on 6 November and set aside for careful framing, a reason the rule 'every story alike' later dropped. Source: `story_discovery_1797/README.md#Noted but not recommended now/(115)`
- **An obituary of a Portsmouth physician.** Papers: 2. Only 2 papers are confirmed; the third match is a neighbouring item. Source: `story_discovery_1797/README.md#Noted but not recommended now/(077)`
- **48 other candidate families of 3 papers on European and other foreign news and foreign documents: F97-027, F97-028, F97-034, F97-037, F97-038, F97-040, F97-041, F97-045, F97-046, F97-049, F97-050, F97-057, F97-058, F97-059, F97-061, F97-062, F97-063, F97-064, F97-069, F97-072, F97-073, F97-075, F97-076, F97-078, F97-079, F97-080, F97-083, F97-084, F97-085, F97-087, F97-089, F97-090, F97-094, F97-099, F97-101, F97-102, F97-103, F97-104, F97-105, F97-107, F97-108, F97-110, F97-111, F97-112, F97-114, F97-118, F97-121, F97-122.** Papers: 3 each. Read from their representative excerpts on 6 November and not recommended. Source: `story_discovery_1797/README.md#The 99 families that reach 3 newspapers (read 6 November 2026)/European and other foreign news, foreign documents`
- **6 other candidate families of 3 papers on US government and politics: F97-031, F97-048, F97-082, F97-086, F97-100, F97-113.** Papers: 3 each. Read from their representative excerpts on 6 November and not recommended. Source: `story_discovery_1797/README.md#The 99 families that reach 3 newspapers (read 6 November 2026)/US government and politics`
- **6 other candidate families of 3 papers on ships, privateers, seizures and French decrees: F97-024, F97-026, F97-042, F97-056, F97-091, F97-098.** Papers: 3 each. Read from their representative excerpts on 6 November and not recommended. Source: `story_discovery_1797/README.md#The 99 families that reach 3 newspapers (read 6 November 2026)/Ships, privateers, seizures, French decrees`
- **4 other candidate families of 3 papers on the frontier, Native nations, Spain and Louisiana: F97-035, F97-081, F97-109, F97-117.** Papers: 3 each. Read from their representative excerpts on 6 November and not recommended. Source: `story_discovery_1797/README.md#The 99 families that reach 3 newspapers (read 6 November 2026)/Frontier, Native nations, Spain and Louisiana`
- **5 other candidate families of 3 papers on local news, people, disasters, essays and verse: F97-043, F97-044, F97-053, F97-096, F97-106.** Papers: 3 each. Read from their representative excerpts on 6 November and not recommended. Source: `story_discovery_1797/README.md#The 99 families that reach 3 newspapers (read 6 November 2026)/Local news, people, disasters, essays, verse`

## 1805

An item printed in 9 or more papers is admitted, except digests; items in 7 or 8 papers are chosen to cover the months and the kinds of news.

### Below the rule (14)

- **London reports that Sir George Rumbold was seized at Hamburg (January).** Papers: 4 + 2 + 1 in three forms. Not one printed item in 7 papers: the London paragraph is in 4, a summary in other words in 2 and a condensed paragraph in 1. Source: `stories_1805.json#not_admitted/Rumbold seized at Hamburg (January)`
- **Two merchants' letters quoting the Privy Council's order (October).** Papers: 3 each, 5 in all. Two different letters, not one printed item; the consuls' notices of the order are admitted. Source: `stories_1805.json#not_admitted/Two merchants' letters quoting the Privy Council's order (5, October)`
- **Governor Claiborne's letter of 24 October.** Papers: 6 as a summary, 4 in full. No single printed form is in 7 papers. Source: `stories_1805.json#not_admitted/Governor Claiborne's letter of 24 October (December)`
- **Acts of Congress printed 'by authority'.** Papers: 3 to 6 each. Counted by its own title and enacting clause, each act of the session is in 3 to 6 papers; the finder had joined them into chains. Source: `stories_1805.json#not_admitted/Acts of Congress printed by authority`
- **Mr. Randolph's motion to amend the Constitution, making judges removable on address.** Papers: 6. In 6 papers, in two forms. Source: `stories_1805.json#not_admitted/Randolph's motion to amend the Constitution (judges removable on address)`
- **Mr. Elliot's Letter IX to his constituents, on representation.** Papers: 6. In 6 papers; the Enquirer only quotes one sentence. Source: `stories_1805.json#not_admitted/Mr. Elliot to his constituents, Letter IX (on representation)`
- **A Tortola letter of 16 May with the British instruction of 24 June 1803.** Papers: 5. In 5 papers. Source: `stories_1805.json#not_admitted/The Tortola letter of 16 May with the British instruction of 24 June 1803`
- **A passenger's report, by the brig Lovely Lass, of a French decree for the exiles of St. Domingo (May).** Papers: 6. In 6 papers in May; the seventh is a reprint inside another paragraph in October. Source: `stories_1805.json#not_admitted/A passenger of the brig Lovely Lass on a French decree for the exiles of St. Domingo (May)`
- **General Eaton's letters from Egypt.** Papers: 5 by the opening. In 5 papers counted by their opening. Source: `stories_1805.json#not_admitted/Other candidates in 7 or 8 papers`
- **A ship captain's report from Rochelle.** Papers: 6 by phrase search. In 6 papers by phrase search. Source: `stories_1805.json#not_admitted/Other candidates in 7 or 8 papers`
- **The Cuban Intendant's trade regulations.** Papers: 6. No Caribbean item of July to December reaches 7 papers. Source: `story_discovery_1805/README.md#Not admitted/The Caribbean in July to December`
- **The Bahamas assembly's representation on provisions.** Papers: 6. No Caribbean item of July to December reaches 7 papers. Source: `story_discovery_1805/README.md#Not admitted/The Caribbean in July to December`
- **Reports of the British at Cape Nicholas Mole.** Papers: 6. No Caribbean item of July to December reaches 7 papers. Source: `story_discovery_1805/README.md#Not admitted/The Caribbean in July to December`
- **Reports of two captures off Cuba.** Papers: 6. No Caribbean item of July to December reaches 7 papers. Source: `story_discovery_1805/README.md#Not admitted/The Caribbean in July to December`

### Not chosen: month and kind covered (14)

- **A letter from an officer of the frigate President, Syracuse, 28 September 1804.** Papers: 7. January was covered by O'Brien's letter and Chase's speech, and the Barbary states were already the year's largest subject. Source: `stories_1805.json#not_admitted/Letter from an officer of the President, Syracuse, 28 September 1804 (7, January)`
- **A London paragraph of 17 April, 'An opinion of the French Plan'.** Papers: 7. A London paper's forecast, in a month and kind covered by the Boston report that the Toulon fleet was out. Source: `stories_1805.json#not_admitted/London, 17 April: 'An opinion of the French Plan' (7, June)`
- **A Canandaigua report that Detroit was destroyed by fire.** Papers: 7. July was covered by the news from Lewis and Clark's party. Source: `stories_1805.json#not_admitted/Canandaigua report that Detroit was destroyed by fire (7, July)`
- **A Boston report that the city of Tripoli was taken.** Papers: 7. The Barbary states were already the year's largest subject, and September had the Salem report and the official letters. Source: `stories_1805.json#not_admitted/Boston report that the city of Tripoli was taken (7) and the Norfolk report of the frigate President's arrival (7), September`
- **A Norfolk report of the frigate President's arrival.** Papers: 7. The Barbary states were already the year's largest subject, and September had the Salem report and the official letters. Source: `stories_1805.json#not_admitted/Boston report that the city of Tripoli was taken (7) and the Norfolk report of the frigate President's arrival (7), September`
- **A Bordeaux paper's article from Algiers.** Papers: 7. The Barbary states were already the year's largest subject; the Algiers story keeps the first report and the chargé d'affaires's letter. Source: `stories_1805.json#not_admitted/A Bordeaux paper's article from Algiers (7, September-October)`
- **Napoleon's words to the Austrian generals at Ulm.** Papers: 7. December was covered by Collingwood's dispatch. Source: `stories_1805.json#not_admitted/Napoleon's words to the Austrian generals at Ulm (7, December)`
- **Reports of an expected war with Morocco.** Papers: 7. Its months and kind of news were already covered. Source: `stories_1805.json#not_admitted/Other candidates in 7 or 8 papers`
- **Reports of the Tunisian ambassador's arrival.** Papers: 7. Its months and kind of news were already covered. Source: `stories_1805.json#not_admitted/Other candidates in 7 or 8 papers`
- **A London report of a 'plan of general pacification'.** Papers: 8. A rumour, in months and kinds already covered. Source: `stories_1805.json#not_admitted/Other candidates in 7 or 8 papers`
- **Napoleon's letter to Paris on Wertingen.** Papers: 7. Its months and kind of news were already covered. Source: `stories_1805.json#not_admitted/Other candidates in 7 or 8 papers`
- **A Boston paragraph on seamen's protections.** Papers: 7. Its months and kind of news were already covered. Source: `stories_1805.json#not_admitted/Other candidates in 7 or 8 papers`
- **Reports of an earthquake at Naples.** Papers: 7. Its months and kind of news were already covered. Source: `stories_1805.json#not_admitted/Other candidates in 7 or 8 papers`
- **Reports of a plague at Oujein.** Papers: 7. Its months and kind of news were already covered. Source: `stories_1805.json#not_admitted/Other candidates in 7 or 8 papers`

### Digests, lists and proceedings (1)

- **News digests: the news by the ship Palmyra (May), the London digests of June, and the Vienna, Milan, Munich and Salzburg paragraphs printed in pieces in October and November.** Digests of unrelated paragraphs, not single items. Source: `stories_1805.json#not_admitted/News digests`

### Private persons (6)

- **A captain's account of the loss of the ship Jupiter.** Papers: 7. It reaches the rule but turns on private persons; on 13 November 2026 the owner decided it stays out. Source: `stories_1805.json#for_the_owner/The loss of the ship Jupiter (7 papers, April-May)`
- **A New York report of a man convicted of carrying a challenge to a duel (January).** Papers: 6. In 6 papers, below the rule, and it turns on private persons. Source: `stories_1805.json#for_the_owner/Stories that turn on private persons in 6 papers`
- **A Natchez report of brothers seized at Pinckneyville by armed Spaniards.** Papers: 6. In 6 papers, below the rule, and it turns on private persons. Source: `stories_1805.json#for_the_owner/Stories that turn on private persons in 6 papers`
- **Reports of a murder trial in New York.** Papers: 6. In 6 papers, below the rule, and it turns on private persons. Source: `stories_1805.json#for_the_owner/Stories that turn on private persons in 6 papers`
- **A report of a fatal duel at Alexandria.** Papers: 6. In 6 papers, below the rule, and it turns on private persons. Source: `stories_1805.json#for_the_owner/Stories that turn on private persons in 6 papers`
- **Reports of the robbery of the bank office at Baltimore.** Papers: 6. In 6 papers, below the rule, and it turns on private persons. Source: `stories_1805.json#for_the_owner/Stories that turn on private persons in 6 papers`

## 1806

An item printed in 9 or more papers is admitted, except digests; items in 7 or 8 papers are chosen to cover the months and the kinds of news.

### Below the rule (11)

- **An unsigned communication in the Enquirer on the secret proceedings (August and September).** Papers: 6. A commentary in 6 papers; the House's secret journal stands for the affair. Source: `stories_1806.json#not_admitted/Set aside as repeats of an affair or month already represented`
- **The Cumberland road act.** Papers: 8 by its title, mostly in lists of acts. Counted by its own text it is below the selection; most of its 8 are lists of acts. Source: `stories_1806.json#not_admitted/Below the selection`
- **The act for Indian treaties.** Papers: by title only. Found by its title only. Source: `stories_1806.json#not_admitted/Below the selection`
- **The South Carolina and Tennessee acts.** Papers: by title only. Found by their titles only. Source: `stories_1806.json#not_admitted/Below the selection`
- **The articles of war.** Below the selection, counted by its own text. Source: `stories_1806.json#not_admitted/Below the selection`
- **The post roads act.** Below the selection, counted by its own text. Source: `stories_1806.json#not_admitted/Below the selection`
- **The December act suspending the act of 18 April.** Papers: 6, mostly as a bill in debate. In 6 papers, mostly as a bill in debate. Source: `stories_1806.json#not_admitted/Below the selection`
- **The Treasury's annual report of December 1805.** Papers: 4 in 1806. In 4 papers in 1806; 3 printed it in December 1805. Source: `stories_1806.json#not_admitted/Below the selection`
- **Two differently worded reports of Fox's death.** Papers: 6 each. Two different reports, each in 6 papers. Source: `stories_1806.json#not_admitted/Below the selection`
- **Fox's and Howick's blockade notices.** Papers: 7 in all. Several different notices, so no single item reaches 7 papers. Source: `stories_1806.json#not_admitted/Below the selection`
- **A Detroit letter of 4 June headed 'NO INDIAN WAR'.** Papers: fewer than 7. Found in the gap search, in fewer papers. Source: `stories_1806.json#not_admitted/Below the selection`

### Not chosen: month and kind covered (34)

- **A letter with the list of prisoners taken in Miranda's schooners (July).** Papers: 8. Set aside because the Miranda story already stands for the affair. Source: `stories_1806.json#not_admitted/Set aside as repeats of an affair or month already represented`
- **A Jamaica report that Miranda had landed near Coro (September).** Papers: 8. Set aside because the Miranda story already stands for the affair. Source: `stories_1806.json#not_admitted/Set aside as repeats of an affair or month already represented`
- **Miranda's proclamation at Coro (October and November).** Papers: 8. His proclamation of 28 June stands for his own words in the Miranda story. Source: `stories_1806.json#not_admitted/Set aside as repeats of an affair or month already represented`
- **The memorial of the Corporation of New York to the President on the Leander.** Papers: 7. Set aside because the Leander story already stands for the affair. Source: `stories_1806.json#not_admitted/Set aside as repeats of an affair or month already represented`
- **A Natchez paragraph that the Spanish army stayed at Bayou Pierre.** Papers: 8. Set aside because the Sabine story already stands for the affair. Source: `stories_1806.json#not_admitted/Set aside as repeats of an affair or month already represented`
- **General Eaton's statement on Burr, as a Boston paper gave it.** Papers: 7. Set aside because the Burr story already stands for the affair. Source: `stories_1806.json#not_admitted/Set aside as repeats of an affair or month already represented`
- **The National Intelligencer's paragraph on the nomination of Monroe and Pinkney (April).** Papers: 8. Set aside because its month and kind of news were already represented. Source: `stories_1806.json#not_admitted/Set aside as repeats of an affair or month already represented`
- **George III's declaration on Hanover against Prussia (June).** Papers: 7. Set aside because its month and kind of news were already represented. Source: `stories_1806.json#not_admitted/Set aside as repeats of an affair or month already represented`
- **General Stuart's dispatch on the battle of Maida (October and November).** Papers: 7. Set aside because its months and kind of news were already represented. Source: `stories_1806.json#not_admitted/Set aside as repeats of an affair or month already represented`
- **A ship captain's news that Russia refused d'Oubril's treaty (November).** Papers: 8. Set aside because its month and kind of news were already represented. Source: `stories_1806.json#not_admitted/Set aside as repeats of an affair or month already represented`
- **The act regulating the currency of foreign coins.** Papers: 7 by its enacting text. Printed from May, in a month and kind already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **Strachan's dispatch on taking four French ships (January).** Papers: 7. War news in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **The convention between Murat and Kutusow (February).** Papers: 8. War news in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **A ship captain's report of 'the battle of the three emperors'.** Papers: 7. War news in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **A New York summary: 'It will appear incredible that a mighty empire should be overthrown in six weeks'.** Papers: 7. Commentary, in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **Reports of the explosion at Malta.** Papers: 8. War news in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **The French bulletins on Jena and the other paragraphs of their run.** Papers: 4 to 7 each. War news in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **Mr. Wright's bill 'for the protection and indemnification of American seamen'.** Papers: 7. A bill that did not pass, in a month and kind already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **Mr. Gallatin's letter of 15 April, inside the day's proceedings.** Papers: 8. Not chosen: its month and kind of news were already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **The House resolution on the memorial of the two New York men tried in the Miranda affair.** Papers: 8. Not chosen: its month and kind of news were already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **The National Intelligencer's paragraph on the close of the session.** Papers: 8. Not chosen: its month and kind of news were already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **The proposed amendment to the Constitution (December).** Papers: 7. Not chosen: its month and kind of news were already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **A report of the British minister Erskine's reception by the President.** Papers: 7. Not chosen: its month and kind of news were already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **A letter on boats building at Marietta.** Papers: 7. Not chosen: its month and kind of news were already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **Governor Strong's speech and the answer.** Papers: 6 to 7. Not chosen: its month and kind of news were already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **A Lloyd's insurance paragraph on Miranda's expedition.** Papers: 8. Other reports, in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **Miranda's letter to his brother.** Papers: 7. Other reports, in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **An account of Miranda's expedition from Aruba.** Papers: 6 to 7. Other reports, in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **Major Claiborne's letter, among the Sabine and Florida news.** Papers: 7. Other reports, in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **The official information of 8 October, among the Sabine and Florida news.** Papers: 7. Other reports, in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **A report that Mobile was opened.** Papers: 7. Other reports, in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **A Havana rumour that the Floridas were ceded to France.** Papers: 8. Other reports, in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **Reports of Mungo Park's death.** Papers: 7. Other reports, in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`
- **A New Orleans letter on the church.** Papers: 7. Other reports, in months and kinds already covered. Source: `stories_1806.json#not_admitted/Below the selection`

### Digests, lists and proceedings (2)

- **Lists and chains of acts: the weekly 'Acts passed at the first session of the Ninth Congress' and laws printed 'by authority'.** Papers: up to 133 printings. The finder's items join lists and laws that share titles and the enacting formula; not one item. Source: `stories_1806.json#not_admitted/Below the selection`
- **The Medina paragraph.** A paragraph of a news digest. Source: `stories_1806.json#not_admitted/Below the selection`

### Private persons (7)

- **A New York report that two men 'were arrested by order of government' in the Miranda affair.** Papers: 7 by phrase search. It turns on private persons; on 13 November 2026 the owner decided it stays out. Source: `stories_1806.json#not_admitted/Stories that turn on private persons`
- **The order of a public funeral procession in New York for the man the papers say was killed by a shot from the Leander.** Papers: 8 by phrase search. It turns on private persons; on 13 November 2026 the owner decided it stays out. Source: `stories_1806.json#not_admitted/Stories that turn on private persons`
- **Letters between a New York officer and the Spanish minister, the Marquis de Casa Yrujo, about the officer's son, one of Miranda's men taken prisoner.** Papers: 6 by phrase search (7 by one reader). It turns on private persons; on 13 November 2026 the owner decided it stays out. Source: `stories_1806.json#not_admitted/Stories that turn on private persons`
- **Reports of the trial of the two New York men in the Miranda affair.** Papers: fewer than 7. Below 7 papers, and it turns on private persons. Source: `story_discovery_1806/README.md#For you to decide/Smaller items of the same kind`
- **Reports of an indictment in Boston for a killing.** Papers: fewer than 7. Below 7 papers, and it turns on private persons. Source: `story_discovery_1806/README.md#For you to decide/Smaller items of the same kind`
- **Reports of killings within a family in Maine.** Papers: fewer than 7. Below 7 papers, and it turns on private persons. Source: `story_discovery_1806/README.md#For you to decide/Smaller items of the same kind`
- **A 'melancholy article' from Doylestown.** Papers: fewer than 7. Below 7 papers, and it turns on private persons. Source: `story_discovery_1806/README.md#For you to decide/Smaller items of the same kind`

### Other (2)

- **The President's annual message of December 1805.** Its only hits in 1806 are Yrujo's note, which quotes it. Source: `stories_1806.json#not_admitted/Below the selection`
- **Mr. Nicholson's resolution as offered on 10 February.** Papers: 7. Its text is printed in the National Intelligencer's paragraph on the vote, which is admitted. Source: `stories_1806.json#not_admitted/Below the selection`

## 1807

An item printed in 9 or more papers is admitted, except digests; items in 7 or 8 papers are chosen to cover the months and the kinds of news.

### Below the rule (13)

- **The act repealing the salt duties.** Papers: 5. In 5 papers by its enacting text. Source: `stories_1807.json#not_admitted/Other laws printed by authority`
- **The act suspending the non-importation act.** Papers: 1. In 1 paper by its enacting text. Source: `stories_1807.json#not_admitted/Other laws printed by authority`
- **The President's messages of 26 and 28 January on the Burr affair.** Papers: 1 and 4 by their openings. Each is in fewer than 7 papers counted by its opening. Source: `stories_1807.json#not_admitted/Other Burr items`
- **Mr. Mead's letter on the Burr affair.** Papers: 3. In 3 papers. Source: `story_discovery_1807/README.md#Not admitted/Mead's letter (3)`
- **Reports that Burr was bailed at Natchez.** Papers: 4. In 4 papers. Source: `stories_1807.json#not_admitted/Other Burr items`
- **A Richmond report of Burr's examination that ends 'he should not commit Col. Burr' (April).** Papers: 2. A different item from Marshall's opinion, in 2 papers. Source: `stories_1807.json#not_admitted/Other Burr items`
- **A Norfolk report of the opening days of the court of inquiry.** Papers: 5. A different item from the court's opinion, in 5 papers. Source: `stories_1807.json#not_admitted/The court of inquiry's opening days (5 papers)`
- **The President's message of 18 December on the embargo.** Papers: 4. In 4 papers by 31 December. Source: `stories_1807.json#not_admitted/The Embargo`
- **The Embargo Act of 22 December.** Papers: 5 by 31 December. In 5 papers by 31 December; its January printings are in the reviewed story of 1808. Source: `stories_1807.json#not_admitted/The Embargo`
- **The constitution of the Republic of Hayti, printed in full by the Alexandria Daily Advertiser (7 and 10 February).** Papers: 1. A different item from the Hayti report, in 1 paper. Source: `stories_1807.json#for_user_decision/News from the Republic of Hayti (Baltimore, 3 February; 9 papers)`
- **Fourth of July toasts naming seamen of the Chesapeake.** Papers: 2. Other items, in 2 papers. Source: `stories_1807.json#for_user_decision/Robert MacDonald's death and funeral (Norfolk, 29 June; 7 papers)`
- **'An act to prohibit the importation of slaves', 2 March 1807, printed in full 'by authority'.** Papers: 5. Its text is in 5 papers, below the rule like the other laws printed by authority in fewer than 7; its title in the list of acts and in debate reports are other items. Source: `stories_1807_round2.json#not_admitted/The act to prohibit the importation of slaves`
- **The act continuing the suspension of trade with parts of St. Domingo.** Papers: 3 or 4. Its text is in 3 or 4 papers, below the rule. Source: `stories_1807_round2.json#not_admitted/The act continuing the suspension of trade with parts of St. Domingo`

### Not chosen: month and kind covered (10)

- **The act on Virginia military warrants.** Papers: 7. In 7 papers by its enacting text, one of them a weekly legal notice in the Virginia Argus; not chosen. Source: `stories_1807.json#not_admitted/Other laws printed by authority`
- **The President's proclamation suspending the non-importation act further (March).** Papers: 7. Not chosen: its month and kind of news were already covered. Source: `stories_1807.json#not_admitted/Other laws printed by authority`
- **The House committee's second report on aggressions (24 November).** Papers: 8. Its months and kind of news were already covered. Source: `stories_1807.json#not_admitted/Candidates in 7 or 8 papers not chosen in this round`
- **The President's proclamation pardoning army deserters (19 October).** Papers: 7. Its months and kind of news were already covered. Source: `stories_1807.json#not_admitted/Candidates in 7 or 8 papers not chosen in this round`
- **The War Department's circular to the governors on volunteer companies (3 August).** Papers: 7. Its months and kind of news were already covered. Source: `stories_1807.json#not_admitted/Candidates in 7 or 8 papers not chosen in this round`
- **The resolutions of the Norfolk and Portsmouth meeting of 24 June.** Papers: 7. Its months and kind of news were already covered. Source: `stories_1807.json#not_admitted/Candidates in 7 or 8 papers not chosen in this round`
- **A London report in the Courier of 14 April of peace between England, Russia and Turkey.** Papers: 7. Its months and kind of news were already covered. Source: `stories_1807.json#not_admitted/Candidates in 7 or 8 papers not chosen in this round`
- **The articles of the peace of Tilsit.** Papers: 7. Its months and kind of news were already covered. Source: `stories_1807.json#not_admitted/Candidates in 7 or 8 papers not chosen in this round`
- **The National Intelligencer's report that Britain disclaims searching ships of war (28 September).** Papers: 7. Its months and kind of news were already covered. Source: `stories_1807.json#not_admitted/Candidates in 7 or 8 papers not chosen in this round`
- **Bennigsen's dispatch of 10 February.** Papers: 7. Its months and kind of news were already covered. Source: `stories_1807.json#not_admitted/Candidates in 7 or 8 papers not chosen in this round`

### Digests, lists and proceedings (2)

- **The List of Acts passed during the second session of the Ninth Congress.** Papers: 10. An index of the session's unrelated laws, treated like a digest. Source: `stories_1807.json#not_admitted/The List of Acts passed during the second session of the Ninth Congress (10 papers)`
- **News digests: runs of London and continental paragraphs printed in pieces, such as the London news by the Manchester packet and the Hamburg and Berlin paragraphs of January.** Digests of unrelated paragraphs; single paragraphs from them that reach 9 papers are admitted. Source: `stories_1807.json#not_admitted/News digests`

### Other (2)

- **A New Hampshire Gazette commentary of 6 October quoting the verdict.** Papers: 1. A commentary that quotes the verdict, not a printing of it. Source: `stories_1807.json#not_admitted/Other Burr items`
- **The President's message of 19 February printed without Monroe and Pinkney's letter, and later articles that quote it.** It is counted under the letter where the letter is printed, and not otherwise. Source: `stories_1807.json#not_admitted/The President's message of 19 February without the letter`

## 1808

An item printed in 9 or more papers is admitted, except digests; items in 7 or 8 papers are chosen to cover the months and the kinds of news.

### Below the rule (17)

- **The militia detachment act of 30 March.** Papers: 6. In 6 papers by its own text; the finder's 9 includes the list of acts. Source: `stories_1808.json#not_admitted/Laws and resolutions below 7 papers by their own text`
- **The act arming the militia.** Papers: fewer than 7. Below 7 papers by its own text. Source: `stories_1808.json#not_admitted/Laws and resolutions below 7 papers by their own text`
- **The act raising an additional military force.** Papers: fewer than 7. Below 7 papers by its own text. Source: `stories_1808.json#not_admitted/Laws and resolutions below 7 papers by their own text`
- **The House resolution on when the embargo could be removed (January).** Papers: 7 by the finder. Below 7 papers by its own text. Source: `stories_1808.json#not_admitted/Laws and resolutions below 7 papers by their own text`
- **G. W. Campbell's resolution, which repeats the suspension act's words in debate reports.** Below 7 papers by its own text. Source: `stories_1808.json#not_admitted/Laws and resolutions below 7 papers by their own text`
- **Timothy Pickering's letter to Governor Sullivan (February).** Papers: 6. In 6 papers; the New Hampshire Gazette prints only an answer that quotes it. Source: `stories_1808.json#not_admitted/Timothy Pickering's letter to Governor Sullivan (February)`
- **Canning's notice of the blockade of Copenhagen and Zealand.** Papers: 6. Not one item: the Foreign Office notice of 4 May is in 6 papers. Source: `stories_1808.json#not_admitted/Canning's notice of the blockade of Copenhagen and Zealand`
- **The Armstrong papers on the Berlin decree.** Papers: 6. In 6 papers in spring. Source: `stories_1808.json#not_admitted/The Armstrong papers on the Berlin decree`
- **Lord Collingwood's letter and the 'Note 1' from Cadiz.** Papers: 6 each. Two items, in 6 papers each. Source: `stories_1808.json#not_admitted/News digests and mixed reports`
- **The President's message of 2 February sending the Orders in Council.** Papers: 4 by its text. In 4 papers by its text. Source: `stories_1808.json#not_admitted/Candidates in 6 or 7 papers not chosen`
- **Jefferson's answer to the Democratic Ward of Philadelphia.** Papers: about 5 in full. In about 5 papers in full. Source: `stories_1808.json#not_admitted/Candidates in 6 or 7 papers not chosen`
- **A table of how the states choose their electors.** Papers: 5 by phrase search. In 5 papers by phrase search. Source: `stories_1808.json#not_admitted/Candidates in 6 or 7 papers not chosen`
- **Mr. Randolph's resolution for an inquiry into General Wilkinson.** Papers: 4 by its text. In 4 papers by its text. Source: `stories_1808.json#not_admitted/Candidates in 6 or 7 papers not chosen`
- **Gallatin's letter to the Senate committee on enforcing the embargo (December).** Papers: 6. In 6 papers. Source: `stories_1808.json#not_admitted/Candidates in 6 or 7 papers not chosen`
- **The Treasury's certificate on the two millions (September).** Papers: 6. In 6 papers. Source: `stories_1808.json#not_admitted/Candidates in 6 or 7 papers not chosen`
- **Joseph Bonaparte's proclamation (August).** Papers: 6. In 6 papers. Source: `stories_1808.json#not_admitted/Candidates in 6 or 7 papers not chosen`
- **Champagny's report of 1 September.** Papers: 6. In 6 papers. Source: `stories_1808.json#not_admitted/Candidates in 6 or 7 papers not chosen`

### Not chosen: month and kind covered (5)

- **Other documents sent with the President's message of 8 November: Madison to Armstrong of 22 May and 8 February, the letters to Pinkney, and Armstrong's letters of February and April.** Papers: 5 to 7 each. Three documents, one British, one French and one American, already stand for the set. Source: `stories_1808.json#not_admitted/Other documents sent with the message of 8 November`
- **The President's message of 4 February with Clark's papers.** Papers: 7. Its months and kind of news were already covered. Source: `stories_1808.json#not_admitted/Candidates in 6 or 7 papers not chosen`
- **The Navy Department's letter on seamen (February).** Papers: 7. Its months and kind of news were already covered. Source: `stories_1808.json#not_admitted/Candidates in 6 or 7 papers not chosen`
- **Lord Grenville's speech in the Lords on the Orders in Council, 5 May.** Papers: 7. Its months and kind of news were already covered. Source: `stories_1808.json#not_admitted/Candidates in 6 or 7 papers not chosen`
- **The Liverpool 'Political Review' on Rose's return.** Papers: 7. A forecast, in a month and kind already covered. Source: `stories_1808.json#not_admitted/Candidates in 6 or 7 papers not chosen`

### Digests, lists and proceedings (4)

- **The Supplemental Journal of the House: the secret proceedings of 26 February and 30 March.** Papers: 9 only with a November reprint and both Alexandria titles. Procedural entries printed in parts. Source: `stories_1808.json#not_admitted/The Supplemental Journal of the House (secret proceedings of 26 February and 30 March)`
- **News digests and mixed reports: the London paragraphs of 23 February on papers laid before the Commons, the outline of Parliament's proceedings in May, the Madrid paragraph on the Duke of Berg (August), the London paragraph on Joseph Bonaparte at Madrid (October) and the news by the ship Camilla from Cadiz (October).** Digest paragraphs and mixed reports, not single items; the Camilla news came in two New York wordings and several letters. Source: `stories_1808.json#not_admitted/News digests and mixed reports`
- **The resolutions of the committee on foreign relations and the debates on them (November and December).** Papers: up to 27 printings. Daily proceedings in which the resolutions recur, treated like a digest. Source: `stories_1808.json#not_admitted/The resolutions of the committee on foreign relations and the debates on them`
- **The day-by-day debates of November and December on the embargo, among them those on Giles's enforcement bill.** Papers: many printings. Proceedings rather than single items. Source: `story_discovery_1808/README.md#Candidates for a later round/The embargo debates of November and December`

### Other (1)

- **Article 12 of the French convention, quoted inside different editorials.** A treaty article quoted in editorials, not one printed item. Source: `stories_1808.json#not_admitted/Article 12 of the French convention`

## 1809

An item printed in 9 or more papers is admitted, except digests; items in 7 or 8 papers are chosen to cover the months and the kinds of news.

### Below the rule (16)

- **The appropriation, relief, land and military acts of the two sessions.** Papers: 5 or 6 each. Counted by its own first section, no act reaches 7 papers; the finder had chained the acts together. Source: `stories_1809.json#not_admitted/The appropriation, relief, land and military acts of the two sessions (5 or 6 papers each)`
- **The British order in council of 21 December 1808, as a separate item.** Papers: 6. In 6 papers by its own words; in June it is printed inside the Senate papers, which are admitted. Source: `stories_1809.json#not_admitted/The order in council of 21 December 1808 as a separate item (6)`
- **The Treasury report of December 1808.** Papers: 2 in 1809. Two papers printed it in 1809; the finder had chained it to the year's other reports. Source: `stories_1809.json#not_admitted/The Treasury report of December 1808 (2 papers in 1809)`
- **The Treasury report of June 1809.** Papers: 6. In 6 papers by its own words; the report of December 1809 is admitted. Source: `stories_1809.json#not_admitted/The Treasury report of June 1809 (6)`
- **A Boston report of a ship captain's news from Lisbon.** Papers: 6. Below 7 papers counted by its own words. Source: `stories_1809.json#not_admitted/Captain Sawyer's report from Portugal (6)`
- **A report of an interview with the bearer of Mr. Pinkney's dispatches.** Papers: 5. Below 7 papers counted by its own words. Source: `stories_1809.json#not_admitted/An interview with Mr. Purviance (5)`
- **Reports of Lord Cochrane's fire ships in Basque Roads.** Papers: 6. Below 7 papers counted by its own words. Source: `stories_1809.json#not_admitted/Lord Cochrane's fire ships in Basque Roads (6)`
- **The British dispatches on Corunna and Sir John Moore's death.** Papers: 6 each. Each is below 7 papers counted by its own words. Source: `stories_1809.json#not_admitted/The British dispatches on Corunna and Sir John Moore's death (6 each)`
- **The King's speech delivered by the Lords Commissioners to both Houses of Parliament.** Papers: 6. Below 7 papers counted by its own words. Source: `stories_1809.json#not_admitted/The King's speech and the Erfurt papers (6 each)`
- **The papers on the overtures from Erfurt, laid before Parliament.** Papers: 6. Below 7 papers counted by its own words. Source: `stories_1809.json#not_admitted/The King's speech and the Erfurt papers (6 each)`
- **Pinkney's letter to Canning of October 1808.** Papers: 6. Below 7 papers counted by its own words. Source: `stories_1809.json#not_admitted/Pinkney's letter to Canning of October 1808 (6)`
- **The Archduke Charles's statement on his resignation.** Papers: 6. Below 7 papers counted by its own words. Source: `stories_1809.json#not_admitted/The Archduke Charles's resignation (6)`
- **A summary of the bill on commercial intercourse.** Papers: 3. Below 7 papers counted by its own words. Source: `stories_1809.json#not_admitted/The summary of the bill on commercial intercourse (3)`
- **A letter from the city of Santo Domingo: 'We still remain besieged by the Spaniards'.** Papers: 6. Below 7 papers counted by its own words, with no parent story to stand under. Source: `stories_1809.json#not_admitted/The letter from Santo Domingo, 'We still remain besieged by the Spaniards' (6)`
- **The War Department's notice for ration proposals, printed weekly from July.** Papers: 6. In 6 papers; no standing notice of 1809 reaches 9. Source: `story_discovery_1809/README.md#For you to decide/the War Department's notice for ration proposals`
- **The Senate's bill of the act of 28 June, printed a week before the act.** Papers: 4. In 4 papers, and its later sections differ from the act, so it is not counted with it. Source: `story_discovery_1809/README.md#For you to decide/the Senate's bill, printed in four papers a week earlier`

### Not chosen: month and kind covered (11)

- **The National Intelligencer on the dispatches brought by the Union (20 March).** Papers: 7. Its months and kind of news were already covered by the admitted stories. Source: `stories_1809.json#not_admitted/The Intelligencer on the dispatches by the Union (20 March, 7)`
- **The French bulletins from Ebersdorf of 28 May to 2 June.** Papers: 8. Its months and kind of news were already covered by the admitted stories. Source: `stories_1809.json#not_admitted/The French bulletins from Ebersdorf of 28 May to 2 June (8)`
- **The Austrian bulletin of the battle of Raab.** Papers: 7. Its months and kind of news were already covered by the admitted stories. Source: `stories_1809.json#not_admitted/The Austrian bulletin of the battle of Raab (7)`
- **General Venegas's dispatch on Almonacid.** Papers: 7. Its months and kind of news were already covered by the admitted stories. Source: `stories_1809.json#not_admitted/General Venegas's dispatch on Almonacid (7)`
- **The Archduke Charles's order of the day after Wagram.** Papers: 7. Its months and kind of news were already covered by the admitted stories. Source: `stories_1809.json#not_admitted/The Archduke Charles's order of the day after Wagram (7)`
- **The Emperor Francis's general order.** Papers: 7. Its months and kind of news were already covered by the admitted stories. Source: `stories_1809.json#not_admitted/The Emperor Francis's general order (7)`
- **A British colonel's letter from Badajoz.** Papers: 7. Its months and kind of news were already covered by the admitted stories. Source: `stories_1809.json#not_admitted/A British colonel's letter from Badajoz (7)`
- **Mr. Troup's resolutions in the House.** Papers: 8. Its months and kind of news were already covered by the admitted stories. Source: `stories_1809.json#not_admitted/Troup's resolutions in the House (8)`
- **The Senate's proceedings of 1 December.** Papers: 7. Its months and kind of news were already covered by the admitted stories. Source: `stories_1809.json#not_admitted/The Senate's proceedings of 1 December (7)`
- **The President's message of 16 December with extracts of Pinkney's letters.** Papers: 7. Its months and kind of news were already covered by the admitted stories. Source: `stories_1809.json#not_admitted/The President's message of 16 December with extracts of Pinkney's letters (7)`
- **A decree of the King of Holland.** Papers: 8. Left out in the check because May was covered by six other stories; it can be added after a scan check of its printings. Source: `stories_1809.json#not_admitted/The Dutch decree (8)`

### Digests, lists and proceedings (4)

- **The list of appointments made by the new President and the Senate.** Papers: 7. A list of names, left out in the scan check; it can be added after a scan check of its printings. Source: `stories_1809.json#not_admitted/The list of appointments (7)`
- **Runs of London and Hamburg paragraphs.** Digests of unrelated paragraphs. Source: `stories_1809.json#not_admitted/Runs of London and Hamburg paragraphs`
- **Ship-news digests: the brig Favorite, the Fair American, the Paragon, the Golden Age and the Salem Register's French papers.** Digests of unrelated paragraphs. Source: `stories_1809.json#not_admitted/Ship-news digests (the brig Favorite, the Fair American, the Paragon, the Golden Age, the Salem Register's French papers)`
- **Debates, day-by-day proceedings and lists.** Not single printed items: proceedings and lists made of many unrelated parts. Source: `stories_1809.json#not_admitted/Debates, day-by-day proceedings and lists`

### Private persons (1)

- **A mate's letter on a swordfish striking the schooner Sarah (14 to 29 November).** Papers: 7. It reaches the rule but turns on private persons; on 13 November 2026 the owner decided it stays out. Source: `stories_1809.json#for_the_owner/A letter on a swordfish striking the schooner Sarah (7 papers, 14 to 29 November)`
