from log_into_wiki import *
import mwparserfromhell, time

site = login('bot', 'lol')  # Set wiki
summary = 'replace blockbox'  # Set summary

limit = -1
# startat_page = 'asdf'
this_template = site.pages['Template:BlockBox']  # Set template
pages = this_template.embeddedin()

pages_var = list(pages)

pages_array = [p.name for p in pages_var]

try:
	startat = pages_array.index(startat_page)
except NameError as e:
	startat = -1
except ValueError as e:
	startat = -1
print(startat)

lmt = 0
for page in pages_var:
	if lmt == limit:
		break
	lmt += 1
	if lmt < startat or 'Scoreboards' in page.name:
		print("Skipping page %s" % page.name)
	else:
		if 'Picks and Bans' in page.name:
			time.sleep(30)
		text = page.text()
		wikitext = mwparserfromhell.parse(text)
		for template in wikitext.filter_templates():
			if template.name.matches('BlockBox'):
				template.name = 'Box'
		
		newtext = str(wikitext)
		if text != newtext:
			print('Saving page %s...' % page.name)
			page.save(newtext, summary=summary)
		else:
			print('Skipping page %s...' % page.name)