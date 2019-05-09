import re, threading, mwparserfromhell
from log_into_wiki import *

#################################################################################################

original_name = 'Comeback'
irl_name = 'Ha Seung-chan'
new_name = '{} ({})'.format(original_name, irl_name)
init_move = True
blank_edit = False
limit = -1
timeout_limit = 30

listplayer_templates = ["listplayer", "listplayer/Current"]
roster_templates = ["ExtendedRosterLine", "ExtendedRosterLine/MultipleRoles"]
scoreboard_templates = ["MatchRecap/Player", "MatchRecapS4/Player",
					   "MatchRecapS5/Player", "MatchRecapS6/Player",
					   "MatchRecapS7/Player", "MatchRecapS8/Player",
					   "MatchRecapS6NoSMW/Player", "MatchRecapS7NoKeystones/Player",
					   "MatchRecapNoItems/Player", "MatchRecap/Player",
					   "Scoreboard/Player"]
stat_templates = ["IPS", "CareerPlayerStats", "MatchHistoryPlayer"]
player_line_templates = ["LCKPlayerLine", "LCSPlayerLine"]
roster_change_templates = ["RosterChangeLine", "RosterRumorLine2", "RosterRumorLineStay", "RosterRumorLineNot"]
summary = "Disambiguating {} to {}".format(original_name, new_name)

css_style = "{\n    color:orange!important;\n    font-weight:bold;\n}"

orig_name_lc = original_name[0].lower() + original_name[1:]
new_name_lc = new_name[0].lower() + new_name[1:]

blank_edit_these = []

#############################################################################################

def savepage(targetpage, savetext):
	targetpage.save(savetext, summary=summary, tags="bot_disambig")

def blank_edit_page(page):
	textname = str(page.name)
	newpage = site.pages[textname]
	text = newpage.text(cache=False)
	page.save(text, summary="Blank Editing")

def move_page(from_page):
	new_page_name = str(from_page.name).replace(original_name, new_name)
	new_page = site.pages[new_page_name]
	if new_page.exists:
		print("{} already exists, cannot move!".format(from_page.name))
	else:
		print("Moving page {} to {}".format(from_page.name, new_page_name))
		from_page.move(new_page_name, reason=summary, no_redirect=True)
		blank_edit_these.append(new_page)

def edit_concept(concept):
	text = concept.text()
	wikitext = mwparserfromhell.parse(text)
	for template in wikitext.filter_templates():
		if template.name.matches("PlayerGamesConcept"):
			i = 1
			while template.has(i):
				if template.get(i).strip() == original_name:
					template.add(i, new_name)
				elif template.get(i).strip() == orig_name_lc:
					template.add(i, new_name_lc)
				i = i + 1
	newtext = str(wikitext)
	if newtext != text:
		concept.save(newtext, summary=summary, tags="bot_disambig")

def save_css_page():
	print('Starting css page...')
	csspage = site.pages["MediaWiki:Gadget-highlightDisambigs.css"]
	csstext = csspage.text()
	if '"' + original_name + '"' not in csstext:
		# use re in case a human edited the page and didn't use exactly the expected styling
		# remove the style from the string
		s = csstext.split('{')[0]
		# split string to capture the page titles
		tbl = re.split('a\\[title="\s*(.+?)\s*\"\\],?\s*', s)
		tbl.append(original_name)
		tblSorted = sorted(tbl)
		# re-add style
		tblSorted2 = ['a[title="{}"]'.format(s) for s in tblSorted if s.strip(", ") != ""]
		# concatenage back into a string
		csstext = ', '.join(tblSorted2) + css_style
		print("Saving css page...")
		csspage.save(csstext, summary=summary, tags="bot_disambig")

def edit_subpage(subpage):
	text = subpage.text()
	wikitext = mwparserfromhell.parse(text)
	for stemplate in wikitext.filter_templates():
		if stemplate.has(1):
			if stemplate.get(1).value.strip() == original_name:
				stemplate.add(1, new_name)
	newtext = str(wikitext)
	if text != newtext:
		print("Editing " + subpage.name + "...")
		subpage.save(newtext, reason=summary)

def process_page(page):
	print("Processing next page: " + page.name)
	text = page.text()
	origtext = text
	# do links first because it's easier to just edit them as a string
	text = text.replace("[[" + original_name + "]]", "[[" + new_name + "|" + original_name + "]]")
	wikitext = mwparserfromhell.parse(text)
	for template in wikitext.filter_templates():
		process_template(template)
	newtext = str(wikitext)
	if origtext != newtext or blank_edit:
		print("Saving...")
		t = threading.Thread(target=savepage, kwargs={"targetpage": page, "savetext": newtext})
		t.start()
		t.join(timeout=timeout_limit)
	else:
		print("No changes, skipping")

def process_template(template):
	if template.name.matches('bl') and template.get(1).value.strip() == original_name and not template.has(2):
		template.add(1, new_name)
		template.add(2, original_name)
	
	elif template.name.strip() in listplayer_templates and template.get(
					1).value.strip() == original_name and not template.has("link"):
		template.add("link", new_name, before=1)
	
	elif template.name.strip() in roster_templates \
					and template.has("player") \
					and template.get("player").value.strip() == original_name \
					and not template.has("link"):
		template.add("link", new_name, before="name")
	
	elif template.name.matches('TeamRoster'):
		j = 1
		jstr = str(j)
		while template.has("player" + jstr):
			if template.get("player" + jstr).value.strip() == original_name and not template.has("link" + jstr):
				template.add("link" + jstr, new_name, before="flag" + jstr)
			j = j + 1
			jstr = str(j)
	
	elif template.name.strip() in scoreboard_templates and template.get("name").value.strip() == original_name:
		template.add("link", new_name, before="kills")
	
	elif template.name.strip() in roster_change_templates and template.get("player").value.strip() == original_name:
		template.add("player", new_name + "{{!}}" + original_name)
	
	elif [_ for _ in player_line_templates if template.name.matches(_)] and template.get(1).value.strip() == original_name:
		template.add(2, new_name)
	
	elif template.name.matches("Player") and template.get(1).strip() == original_name:
		template.add('link', new_name)
	
	elif template.name.matches("RSCR/Line"):
		if template.has("p1"):
			if template.get("p1").strip() == original_name:
				template.add("p1", new_name + "{{!}}" + original_name)
		if template.has("p2"):
			if template.get("p2").strip() == original_name:
				template.add("p2", new_name + "{{!}}" + original_name)
				
	elif template.name.matches("MatchDetails/Series"):
		if template.has("mvp"):
			if template.get("mvp").strip() == original_name:
				template.add("mvplink", new_name, before="mvp")
	elif template.name.matches("PentakillLine"):
		if template.has(6):
			if template.get(6).value.strip() == original_name:
				template.add("playerlink", new_name, before=6)
	
	elif template.name.matches("MatchSchedule") or template.name.matches("MatchSchedule/Game"):
		if template.has("mvp"):
			if template.get("mvp").value.strip() == original_name:
				template.add("mvplink", new_name, before="mvp")
		check_links(template, 'with', 'withlinks', ',', original_name, new_name)
	
	elif template.name.matches("PortalCurrentRosters"):
		for pos in ['t', 'j', 'm', 'a', 's']:
			for period in ['old', 'new']:
				arg_name = pos + '_' + period
				arg_link = arg_name + '_links'
				check_links(template, arg_name, arg_link, ',', original_name, new_name)

def make_disambig_page():
	text = "{{DisambigPage\n|player1=" + new_name + "\n|player2=\n}}"
	page = site.pages[original_name]
	old_text = page.text()
	if 'disambigpage' not in old_text.lower():
		page.save(text, summary=summary)

site = login('me','lol')

thispage = site.pages[original_name]
newpage = site.pages[new_name]

if init_move:
	save_css_page()
	move_page(thispage)
	subpages = site.allpages(prefix=original_name + "/")
	for subpage in subpages:
		edit_subpage(subpage)
		move_page(subpage)
	concept = site.pages["Concept:{}/Games".format(original_name)]
	if concept.exists:
		edit_concept(concept)
		move_page(concept)
	
	
pages = thispage.backlinks()
i = 0
for page in pages:
	if i == limit:
		break
	i = i + 1
	process_page(page)
print("Blank editing...")
if init_move:
	for page in blank_edit_these:
		blank_edit_page(page)
	make_disambig_page()
print("Done! If some pages stalled out you may still need to abort manually.")