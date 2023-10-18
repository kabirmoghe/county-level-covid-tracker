from flask import Flask, redirect, url_for, render_template, request
import covidapp
import os.path
from os import path
import readbucketdata
import pandas as pd

app = Flask(__name__)
app.secret_key = 'MY_KEY'

# Home page
@app.route("/")
def home():

	# To avoid lag, data will always be reloaded at this page but at 'data', 'stats', etc., data will only be produced if unavailable in local directory
	templates = os.listdir('/app/templates')
	needed = ['index.html', '.DS_Store', 'about.html', 'base.html', 'explore_results.html', 'explorehome.html', 'vaxx_stats.html', 'data.html', 'deaths_stats.html', 'statshome.html', 'cases_stats.html', 'result.html', 'empty.html', 'undef_result.html']
	[os.remove('/app/templates/{}'.format(file)) for file in templates if file not in needed] # removes extra files

	readbucketdata.readbucketdata('vaxx').to_csv('vaxxdataset.csv')
	readbucketdata.readbucketdata('full').to_csv('fulldataset.csv')

	return render_template("index.html")

# Data route: provides users with COVID-19 info on a specific county (i.e. moving avgs., vaxx. progress, etc.)
@app.route("/data", methods = ['POST', 'GET'])
def countyinfo():
	# Only reproduces data if necessary to avoid long waits between reloads
	if path.exists('vaxxdataset.csv') == False and path.exists('fulldataset.csv') == False:
		readbucketdata.readbucketdata('vaxx').to_csv('vaxxdataset.csv')
		readbucketdata.readbucketdata('full').to_csv('fulldataset.csv')
	
	if request.method == "POST":
		county = request.form["cty"]
		if county == '':
			return render_template('empty.html')
		else:

			data1, data2 = pd.read_csv('fulldataset.csv'), pd.read_csv('vaxxdataset.csv')

			# Goes on with producing metrics if county name is valid and exists in both aggregate dataset and vaxx. dataset
			if county in data1['County Name'].values and county in data2['County Name'].values:

				v_update, vaxxkeytype = covidapp.vaxx_plot(county)
				covidapp.avg_plot(county)
				allinfo = covidapp.county_stats(county)
				
				tbl, stat, info, rec, risk_pos, pct, mask_details, mask_links, color, risk, c_update, m_update = allinfo

				link_dict = {}

				for source in mask_links.split(", "):
					link_dict[source.split(" - ")[0]] = source.split(" - ")[1]
				
				ctyrisk_pos = risk_pos - 12.5

				if vaxxkeytype == 'vaxxkeyissue':
					# Certain counties may have issues with info on partial vaccinations

					vaxxnote = 'The partial vaccination data for {} is incomplete, so it is not shown below.'.format(county)
					vaxxsize = 10
				else:
					vaxxnote = ''
					vaxxsize = 25

				# Parsing information

				if round(pct) == 100.0:
					ptile = 'Top ~99%'
				else:
					if pct >= 50:
						ptile = 'Top ~{}%'.format(str(round(100.0-pct)))
					else:
						ptile = 'Bottom ~{}%'.format(str(round(pct)))

				state = county.split(', ')[1]

				if state == 'TX' or state == 'HI':
					note = 'Hawaii, Texas, and counties in California with populations less than 20,000 do not provide county-level data on vaccinations, hence why the visualizations below are empty.'

				else:
					note = 'Toggle the button below to show either visualizations on the percentage of fully vaccinated people within the county broken down by age group or visualizations on percent fully vaccinated and percent with at least one dose in the county.'

				return render_template("result.html", county = county, state = state, tbl = [tbl.to_html(classes='data', header = True)], stat = stat, info = info, rec = rec, risk_pos = risk_pos, pct = pct, ctyrisk_pos = ctyrisk_pos, mask_details = mask_details, link_dict = link_dict, color = color, note = note, ptile = ptile, risk = risk, c_update = c_update, m_update = m_update, v_update = v_update, vaxxkeytype = vaxxkeytype, vaxxnote = vaxxnote, vaxxsize = vaxxsize)
			
			else:
				return render_template("undef_result.html", issue = 'Please enter a valid county name (i.e. Orange County, CA). The county you entered, {}, may not have complete information.'.format(county))
	else:
		# Removes unnecessary files on reload to lighten load
		templates = os.listdir('/app/templates')
		needed = ['index.html', '.DS_Store', 'about.html', 'base.html', 'explore_results.html', 'explorehome.html', 'vaxx_stats.html', 'data.html', 'deaths_stats.html', 'statshome.html', 'cases_stats.html', 'result.html', 'empty.html', 'undef_result.html']
		[os.remove('/app/templates/{}'.format(file)) for file in templates if file not in needed]

		ctys = covidapp.county_list()
		return render_template("data.html", ctys = ctys)
		
# Stats route: provides users with nationwide stats on infection & mortality rates + vaxx. progress
@app.route("/stats", methods = ['POST', 'GET'])
def stats():

	if path.exists('vaxxdataset.csv') == False and path.exists('fulldataset.csv') == False:
		readbucketdata.readbucketdata('vaxx').to_csv('vaxxdataset.csv')
		readbucketdata.readbucketdata('full').to_csv('fulldataset.csv')
		
	if request.method == "POST":
		choice = request.form["choice"]

		if choice == 'vaxx': # Plotting vaccination progress
			date = covidapp.multivaxx_plot()
			return render_template("vaxx_stats.html", date = date)
		else:
			if choice == 'c': # Cases/infection rates
				top10, bot10, date, num0 = covidapp.usplot('c')
				return render_template("cases_stats.html", top10 = [top10.to_html(classes='data', header = True)], bot10 = [bot10.to_html(classes='data', header = True)], choice = choice, date = date, num0 = num0)
			else: # Mortality rate
				top10, bot10, date, num0 = covidapp.usplot('d')
				return render_template("deaths_stats.html", top10 = [top10.to_html(classes='data', header = True)], bot10 = [bot10.to_html(classes='data', header = True)], choice = choice, date = date, num0 = num0)
	else:
		# Removes unnecessary files on reload to lighten load
		templates = os.listdir('/app/templates')
		needed = ['index.html', '.DS_Store', 'about.html', 'base.html', 'explore_results.html', 'explorehome.html', 'vaxx_stats.html', 'data.html', 'deaths_stats.html', 'statshome.html', 'cases_stats.html', 'result.html', 'empty.html', 'undef_result.html']
		[os.remove('/app/templates/{}'.format(file)) for file in templates if file not in needed]

		return render_template("statshome.html")

# Explore route: allows users to explore relationships between all attributes in the data
@app.route("/explore", methods = ['POST', 'GET'])
def explore():
	templates = os.listdir('/app/templates')
	needed = ['index.html', '.DS_Store', 'about.html', 'base.html', 'explore_results.html', 'explorehome.html', 'vaxx_stats.html', 'data.html', 'deaths_stats.html', 'statshome.html', 'cases_stats.html', 'result.html', 'empty.html', 'undef_result.html']
	[os.remove('/app/templates/{}'.format(file)) for file in templates if file not in needed]

	if path.exists('vaxxdataset.csv') == False and path.exists('fulldataset.csv') == False:
		readbucketdata.readbucketdata('vaxx').to_csv('vaxxdataset.csv')
		readbucketdata.readbucketdata('full').to_csv('fulldataset.csv')

	if request.method == "POST":
		# Given choices for columns, produces output plot using plotly and imported methods from 'covidapp' file
		attr1 = request.form["choice1"]
		attr2 = request.form["choice2"]
		trendline = request.form["trendline"]

		covidapp.scatter(attr1, attr2, trendline)

		return render_template("explore_results.html", attr1 = attr1, attr2 = attr2, trendline = trendline)
			
	else:
		# Prepares to pass columns as options for input fields to select for relationship exploration
		templates = os.listdir('/app/templates')
		needed = ['index.html', '.DS_Store', 'about.html', 'base.html', 'explore_results.html', 'explorehome.html', 'vaxx_stats.html', 'data.html', 'deaths_stats.html', 'statshome.html', 'cases_stats.html', 'result.html', 'empty.html', 'undef_result.html']
		[os.remove('/app/templates/{}'.format(file)) for file in templates if file not in needed]
		
		cols = [col for col in pd.read_csv('fulldataset.csv').columns[3:] if col != 'State' and "Mask" not in col]
		cols.reverse()
		return render_template("explorehome.html", cols = cols)

# About route: info page to explain methodology, sources, and goal for this project
@app.route("/about")
def about():
	static = os.listdir('/app/static')
	[os.remove('/app/static/{}'.format(file)) for file in static if file == 'nationwideavg.png']

	return render_template("about.html")

if __name__ == '__main__':
    app.run(debug = True)